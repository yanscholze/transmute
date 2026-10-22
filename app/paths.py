"""Resolve diretório portátil e estado gravável, com override explícito do operador."""
import os
import sys
import json
from pathlib import Path


def project_root():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def state_root():
    root = project_root()
    installed = root / "installation.json"
    per_user = installed.is_file() and json.loads(installed.read_text(encoding="utf-8")).get("state_mode") == "user"
    if os.environ.get("CONVERSOR_STATE_DIR"):
        path = Path(os.environ["CONVERSOR_STATE_DIR"])
    elif per_user:
        # Installed app directories may be read-only; uninstallers never own data.
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) if sys.platform == "win32" else Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
        path = base / "Transmute" if sys.platform == "win32" else base / "transmute"
    else:
        path = root / ".local"
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path
