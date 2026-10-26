"""Cria instaladores a partir de ZIPs nativos já validados, sem estado pessoal.

Windows: execute no runner Windows com NSIS; Linux: execute com rpmbuild.
O conteúdo é extraído em staging novo e todos os hashes/modelos são conferidos.
Arquivos finais nunca substituem uma release existente silenciosamente.
"""
import argparse
import json
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import __version__  # noqa: E402
from app.core.catalog import digest  # noqa: E402


def write_manifest(folder):
    manifest = {p.relative_to(folder).as_posix(): digest(p) for p in folder.rglob("*") if p.is_file() and p.name != "SHA256.json"}
    (folder / "SHA256.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def prepare_payload(archive, staging, system):
    """Only native binaries and blank templates are admitted into an installer."""
    with zipfile.ZipFile(archive) as packed:
        if packed.testzip():
            raise ValueError("ZIP de origem corrompido.")
        for member in packed.infolist():
            target = (staging / member.filename).resolve()
            if not target.is_relative_to(staging.resolve()):
                raise ValueError("Caminho inseguro no pacote de origem.")
        packed.extractall(staging)
    payload = next(p for p in staging.iterdir() if p.is_dir())
    checksums = json.loads((payload / "SHA256.json").read_text(encoding="utf-8"))
    for name, value in checksums.items():
        if not (payload / name).resolve().is_relative_to(payload.resolve()) or digest(payload / name) != value:
            raise ValueError("Hash de origem inválido.")
    if (payload / ".local").exists():
        raise ValueError("Estado pessoal não pode acompanhar instalador.")
    executable = payload / ("ConversorDeBases.exe" if system == "Windows" else "ConversorDeBases")
    signature = executable.read_bytes()[:4]
    if (system == "Windows" and not signature.startswith(b"MZ")) or (system == "Linux" and signature != b"\x7fELF"):
        raise ValueError("Executável não corresponde ao sistema alvo.")
    for model in (payload / "#PLANILHAS DE BASE").rglob("*.xlsx"):
        book = load_workbook(model, read_only=True)
        try:
            if any(sum(any(v is not None for v in row) for row in sheet.values) != 1 for sheet in book):
                raise ValueError("Modelo de distribuição contém dados preenchidos.")
        finally:
            book.close()
    (payload / "installation.json").write_text(json.dumps({"version": __version__, "state_mode": "user"}), encoding="utf-8")
    shutil.copy2(ROOT / "packaging/brand.json", payload / "library_preset.json")
    # Installed copies use per-user state, unlike the source portable ZIP.
    state = "%LOCALAPPDATA%\\Transmute" if system == "Windows" else "${XDG_DATA_HOME:-~/.local/share}/transmute"
    (payload / "LEIA-ME.txt").write_text(
        f"Transmute {__version__} — instalação {system}\n\n"
        "Abra Transmute pelo menu de aplicativos. Python e Qt estão incluídos.\n"
        "Dashboard reúne importações e atalhos; Biblioteca permite escolher modelos e editar regras.\n"
        "O Estúdio reúne fontes, regras, conversa, planos aprovados e auditoria. Aparência permite temas claro/escuro, destaque e logo personalizáveis.\n"
        f"Dados e preferências ficam em {state}, fora da pasta do programa.\n"
        "Atualizar ou desinstalar preserva esses dados. Os modelos distribuídos estão vazios.\n"
        "Consulte docs para regras, privacidade, manutenção e empacotamento.\n",
        encoding="utf-8",
    )
    # ZIP does not reliably retain Unix execute bits; restore only our executable.
    executable.chmod(0o755)
    write_manifest(payload)
    return payload


def nsis_escape(text):
    return str(text).replace("$", "$$").replace('"', '$\\"')


def windows_installer(payload, output, compiler, workspace):
    if platform.system() != "Windows":
        raise RuntimeError("O instalador Windows deve ser compilado no Windows nativo.")
    target = output / f"Transmute-{__version__}-Windows-x64-Setup.exe"
    if target.exists():
        raise FileExistsError(target)
    uninstall = workspace / "uninstall-files.nsh"
    files = sorted(p for p in payload.rglob("*") if p.is_file())
    dirs = sorted((p for p in payload.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True)
    lines = [f'Delete "$INSTDIR\\{nsis_escape(str(p.relative_to(payload)))}"' for p in files]
    lines += [f'RMDir "$INSTDIR\\{nsis_escape(str(p.relative_to(payload)))}"' for p in dirs]
    uninstall.write_text("\n".join(lines), encoding="utf-8-sig")
    subprocess.run([str(compiler), "/V2", f"/DVERSION={__version__}", f"/DPAYLOAD={payload}",
                    f"/DOUTPUT={target}", f"/DUNINSTALL_LIST={uninstall}", str(ROOT / "packaging/windows.nsi")], check=True)
    return target


def rpm_installer(payload, output, workspace):
    if platform.system() != "Linux":
        raise RuntimeError("RPM exige o builder Linux.")
    top = workspace / "rpmbuild"
    for name in ["SOURCES", "SPECS", "BUILD", "RPMS", "SRPMS", "BUILDROOT"]:
        (top / name).mkdir(parents=True)
    with tarfile.open(top / "SOURCES/payload.tar.gz", "w:gz") as archive:
        archive.add(payload, arcname="payload")
    for name in ["transmute.sh", "transmute.desktop", "transmute.svg"]:
        shutil.copy2(ROOT / "packaging" / name, top / "SOURCES" / name)
    subprocess.run(["rpmbuild", "-bb", "--define", f"_topdir {top}", "--define", f"app_version {__version__}",
                    str(ROOT / "packaging/transmute.spec")], check=True)
    source = next((top / "RPMS").rglob("*.rpm"))
    target = output / source.name
    if target.exists():
        raise FileExistsError(target)
    shutil.copy2(source, target)
    return target


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--windows-zip", type=Path)
    parser.add_argument("--linux-zip", type=Path)
    parser.add_argument("--makensis", type=Path, default=Path("makensis.exe"))
    parser.add_argument("--output", type=Path, default=ROOT / "dist/releases" / __version__)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    (ROOT / ".local").mkdir(exist_ok=True)
    for system, archive in [("Windows", args.windows_zip), ("Linux", args.linux_zip)]:
        if not archive:
            continue
        with tempfile.TemporaryDirectory(prefix="installer-stage-", dir=ROOT / ".local") as directory:
            workspace = Path(directory).resolve()
            extraction = workspace / "extraction"
            extraction.mkdir()
            payload = prepare_payload(archive, extraction, system)
            target = windows_installer(payload, args.output.resolve(), args.makensis, workspace) if system == "Windows" else rpm_installer(payload, args.output.resolve(), workspace)
            print("INSTALADOR CRIADO:", target)


if __name__ == "__main__":
    main()
