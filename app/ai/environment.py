"""Read a developer-owned .env.local without executing it or writing secrets.

The packaged app uses OS environment/keyring. This source-only convenience
connects the secure key provisioning destination to run.py. Only known API/model
variables are accepted; PYTHONPATH, commands and unrelated settings are ignored.
"""
import os
import re
import shlex
from pathlib import Path

ALLOWED = {"OPENAI_API_KEY", "OPENAI_MODEL", "GEMINI_API_KEY", "GOOGLE_API_KEY", "GEMINI_MODEL", "ANTHROPIC_API_KEY", "CLAUDE_API_KEY", "ANTHROPIC_MODEL"}


def read_environment_file(path):
    """Pure local parser used by development startup and explicit UI import."""
    path = Path(path)
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 65536:
        return {}
    values = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return {}
    for line in lines:
        match = re.fullmatch(r"\s*(?:export\s+)?([A-Z_]+)\s*=\s*(.*?)\s*", line)
        if not match or match[1] not in ALLOWED:
            continue
        try:
            parts = shlex.split(match[2], comments=True, posix=True)
        except ValueError:
            continue
        if len(parts) == 1 and parts[0]:
            values[match[1]] = parts[0]
    return values


def load_development_env(root):
    values = read_environment_file(Path(root) / ".env.local")
    for variable, value in values.items():
        if not os.environ.get(variable, "").strip():
            os.environ[variable] = value
