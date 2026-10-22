import argparse
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMessageBox

from app.paths import project_root, state_root
from app.storage.local import LocalStore
from app.ui.style import STYLE


def main():
    parser = argparse.ArgumentParser(description="Conversor de Bases desktop")
    parser.add_argument("--root", type=Path, help="Pasta contendo regras e #PLANILHAS DE BASE")
    parser.add_argument("--smoke-test", action="store_true", help="Abrir a interface e sair após 1 segundo")
    parser.add_argument("--screenshot", type=Path, help="Salvar captura da janela antes de sair no smoke test")
    parser.add_argument("--self-test", action="store_true", help="Executar conversão sintética local do pacote")
    args = parser.parse_args()
    root, state = args.root or project_root(), state_root()
    if args.self_test:
        from app.selftest import run
        run(root, state)
        return 0
    handler = RotatingFileHandler(state / "diagnostico.log", maxBytes=1024 * 1024, backupCount=2, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger = logging.getLogger("conversor")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.info("application_start version=1.1.0")
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName("Conversor de Bases")
    app.setOrganizationName("ConversorLocal")
    app.setStyle("Fusion")
    app.setFont(QFont("DejaVu Sans" if sys.platform != "win32" else "Segoe UI", 10))
    app.setStyleSheet(STYLE)
    try:
        from app.ui.window import Window
        window = Window(root, state, LocalStore(state))
    except Exception as error:
        QMessageBox.critical(None, "Não foi possível abrir", str(error))
        return 1
    window.show()
    if args.smoke_test:
        def finish():
            if args.screenshot:
                args.screenshot.parent.mkdir(parents=True, exist_ok=True)
                window.grab().save(str(args.screenshot))
            window.close()
            app.quit()
        QTimer.singleShot(1200, finish)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
