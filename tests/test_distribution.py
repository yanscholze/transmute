"""Contratos de instalação e encerramento SQLite, independentes do SO do teste."""
import json
import sqlite3
import zipfile
from pathlib import Path

import pytest

from app import paths
from app.storage.database import database
from scripts.package_installers import prepare_payload, write_manifest


def test_database_closes_on_success_and_rolls_back_on_error(tmp_path):
    path = tmp_path / "state.sqlite3"
    with database(path) as connection:
        connection.execute("CREATE TABLE values_test(value TEXT)")
    with pytest.raises(sqlite3.ProgrammingError):
        connection.execute("SELECT 1")
    with pytest.raises(ValueError):
        with database(path) as failed:
            failed.execute("INSERT INTO values_test VALUES('sintetico')")
            raise ValueError("simular falha")
    with pytest.raises(sqlite3.ProgrammingError):
        failed.execute("SELECT 1")
    with database(path) as check:
        assert check.execute("SELECT count(*) FROM values_test").fetchone()[0] == 0
    path.unlink()  # Windows rejects this when a connection still owns the file.


def test_installed_state_is_outside_app_and_override_wins(tmp_path, monkeypatch):
    install = tmp_path / "installed"
    install.mkdir()
    monkeypatch.setattr(paths, "project_root", lambda: install)
    monkeypatch.delenv("CONVERSOR_STATE_DIR", raising=False)
    assert paths.state_root() == install / ".local"
    (install / "installation.json").write_text(json.dumps({"state_mode": "user"}))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "linux-user"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "windows-user"))
    monkeypatch.setattr(paths.sys, "platform", "linux")
    assert paths.state_root() == tmp_path / "linux-user/transmute"
    monkeypatch.setattr(paths.sys, "platform", "win32")
    assert paths.state_root() == tmp_path / "windows-user/Transmute"
    monkeypatch.setenv("CONVERSOR_STATE_DIR", str(tmp_path / "override"))
    assert paths.state_root() == tmp_path / "override"


def test_installer_rechecks_native_zip_and_blank_templates(tmp_path, make_xlsx):
    payload = tmp_path / "payload"
    payload.mkdir()
    (payload / "ConversorDeBases.exe").write_bytes(b"MZsynthetic-contract-only")
    model = make_xlsx(["Campo"], [], "modelo_sintetico.xlsx")
    models = payload / "#PLANILHAS DE BASE"
    models.mkdir()
    (models / model.name).write_bytes(model.read_bytes())
    write_manifest(payload)
    archive = tmp_path / "windows.zip"
    with zipfile.ZipFile(archive, "w") as packed:
        for path in payload.rglob("*"):
            if path.is_file():
                packed.write(path, Path("native") / path.relative_to(payload))
    stage = tmp_path / "stage"
    stage.mkdir()
    result = prepare_payload(archive, stage, "Windows")
    assert json.loads((result / "installation.json").read_text())["state_mode"] == "user"
    assert json.loads((result / "library_preset.json").read_text())["brand"] == "Transmute"
    assert not (result / ".local").exists()
    bad = tmp_path / "bad.zip"
    with zipfile.ZipFile(bad, "w") as packed:
        packed.writestr("../escape.txt", "synthetic")
    other = tmp_path / "other"
    other.mkdir()
    with pytest.raises(ValueError, match="inseguro"):
        prepare_payload(bad, other, "Windows")
