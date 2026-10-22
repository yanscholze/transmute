"""Desktop entry point, including noninteractive packaged validation failures."""
import os
import sys
import traceback
from pathlib import Path

from app.main import main

if __name__ == "__main__":
    try:
        result = main()
    except Exception:
        if not ({"--self-test", "--smoke-test"} & set(sys.argv)):
            raise
        # Windowed Windows binaries have no stderr and PyInstaller otherwise
        # displays a modal error dialog, blocking unattended native validation.
        details = traceback.format_exc()
        if os.environ.get("CONVERSOR_DIAGNOSTIC_FILE"):
            Path(os.environ["CONVERSOR_DIAGNOSTIC_FILE"]).write_text(details, encoding="utf-8")
        if sys.stderr is not None:
            sys.stderr.write(details)
        result = 1
    raise SystemExit(result)
