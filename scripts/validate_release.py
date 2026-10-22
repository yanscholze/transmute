"""Verifica CRC, manifestos, modelos vazios e runtime extraído do pacote.

Toda extração/execução usa diretório temporário dentro do projeto. Não modifica
o pacote nem a instalação do usuário e não chama serviços externos.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.core.catalog import digest  # noqa: E402


def validate(archive):
    (ROOT / ".local").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="release-check-", dir=ROOT / ".local") as temporary:
        target = Path(temporary)
        with zipfile.ZipFile(archive) as zip:
            if zip.testzip() is not None:
                raise ValueError("ZIP inválido.")
            for item in zip.infolist():
                if not (target / item.filename).resolve().is_relative_to(target.resolve()):
                    raise ValueError("Caminho inseguro dentro do ZIP.")
            zip.extractall(target)
        package = next(p for p in target.iterdir() if p.is_dir())
        hashes = json.loads((package / "SHA256.json").read_text(encoding="utf-8"))
        assert all(digest(package / name) == value for name, value in hashes.items())
        models = list((package / "#PLANILHAS DE BASE").rglob("*.xlsx"))
        for path in models:
            workbook = load_workbook(path, read_only=True)
            try:
                for sheet in workbook:
                    assert sum(1 for row in sheet.values if any(v is not None for v in row)) == 1
            finally:
                workbook.close()
        assert not (package / ".local").exists()
        executable = package / ("ConversorDeBases.exe" if os.name == "nt" else "ConversorDeBases")
        executable.chmod(0o755)
        env = {**os.environ, "CONVERSOR_STATE_DIR": str(target / "state"), "QT_QPA_PLATFORM": "offscreen"}
        env.pop("PYTHONPATH", None)
        env.pop("PYTHONHOME", None)
        subprocess.run([str(executable), "--self-test"], cwd=package, env=env, timeout=60, check=True)
        subprocess.run([str(executable), "--smoke-test"], cwd=package, env=env, timeout=30, check=True)
        print(f"RELEASE OK: {len(hashes)} hashes; {len(models)} modelos vazios; binário extraído executado.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    validate(parser.parse_args().archive)
