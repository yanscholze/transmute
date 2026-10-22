"""Resolve diretório portátil e estado gravável, com override explícito do operador."""
import os
import sys
from pathlib import Path


def project_root():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def state_root():
    path = Path(os.environ.get("CONVERSOR_STATE_DIR", project_root() / ".local"))
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path
