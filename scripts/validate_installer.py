"""Valida instalação, execução e remoção do EXE no Windows nativo do CI.

Não aceita Wine nem executa em outro sistema. Diretórios/estado são isolados no
checkout do runner e nenhum perfil real é importado. Desinstalar deve conservar
o sentinela de dados fora da pasta da aplicação.
"""
import argparse
import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import __version__  # noqa: E402
from app.core.catalog import digest  # noqa: E402


def validate(installer):
    if platform.system() != "Windows":
        raise RuntimeError("Validação exige Windows nativo.")
    (ROOT / ".local").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="installed-check-", dir=ROOT / ".local") as directory:
        work = Path(directory).resolve()
        installed = work / "app"
        subprocess.run([str(installer.resolve()), "/S", f"/D={installed}"], check=True, timeout=180)
        executable = installed / "ConversorDeBases.exe"
        assert executable.is_file()
        manifest = json.loads((installed / "SHA256.json").read_text(encoding="utf-8"))
        assert all(digest(installed / key) == value for key, value in manifest.items())
        env = {**os.environ, "LOCALAPPDATA": str(work / "user"), "QT_QPA_PLATFORM": "windows"}
        env.pop("CONVERSOR_STATE_DIR", None)
        report = work / "selftest.json"
        subprocess.run([str(executable), "--self-test", "--self-test-report", str(report)], check=True, env=env, timeout=90)
        assert json.loads(report.read_text())["version"] == __version__
        state = work / "user/Transmute"
        assert state.is_dir() and not (installed / ".local").exists()
        sentinel = state / "preservar.txt"
        sentinel.write_text("dados sinteticos do usuario", encoding="utf-8")
        screenshot = ROOT / "dist/windows-native.png"
        subprocess.run([str(executable), "--smoke-test", "--screenshot", str(screenshot)], check=True, env=env, timeout=60)
        assert screenshot.stat().st_size > 1000
        config = json.loads((state / "workspace/workspace.json").read_text(encoding="utf-8"))
        profile = Path(config["profile_path"])
        assert profile.is_file() and profile.is_relative_to(state) and "_MEI" not in str(profile)
        subprocess.run([str(executable), "--smoke-test"], check=True, env=env, timeout=60)
        assert profile.is_file()
        subprocess.run([str(installed / "Uninstall.exe"), "/S", f"_?={installed}"], check=True, timeout=90)
        assert not executable.exists() and sentinel.is_file() and profile.is_file()
        print("WINDOWS NATIVO OK: instalar, hashes, CSV/PDF/QtPdf/XLSX, interface e desinstalar preservando dados.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("installer", type=Path)
    validate(parser.parse_args().installer)
