"""Fluxo amigável e aparência são verificados em widgets Qt reais, offscreen."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPainter

from app.core.catalog import workspace_config
from app.storage.local import LocalStore
from app.ui.theme import foreground, palette, stylesheet
from app.ui.window import Window
from tests.conftest import ROOT


def make_window(qtbot, tmp_path, monkeypatch):
    messages = []
    monkeypatch.setattr(Window, "notify", lambda self, message: messages.append(message))
    window = Window(ROOT, tmp_path / "state", LocalStore(tmp_path / "state"))
    qtbot.addWidget(window)
    window.show()
    return window, messages


def test_home_shows_imports_and_wizard_validates(qtbot, tmp_path, monkeypatch):
    window, messages = make_window(qtbot, tmp_path, monkeypatch)
    assert window.pages.currentWidget() is window.dashboard
    assert window.home.content.currentIndex() == 0
    window.new_import()
    wizard = window.wizard
    wizard.advance()
    assert wizard.pages.currentIndex() == 0 and "Informe o nome" in wizard.feedback.text()
    wizard.name.setText("Importação sintética")
    wizard.categories["veiculos"].setChecked(True)
    wizard.advance()
    wizard.advance()
    assert wizard.pages.currentIndex() == 1
    assert "Adicione arquivos" in wizard.feedback.text()
    wizard.previous()
    wizard.previous()
    assert window.pages.currentWidget() is window.home
    assert not window.import_store.list() and not messages
    window.close()


def test_named_multi_file_flow_and_saved_pending_correction(qtbot, tmp_path, make_xlsx, monkeypatch):
    window, messages = make_window(qtbot, tmp_path, monkeypatch)
    window.new_import()
    wizard = window.wizard
    wizard.studio_mode.setChecked(False)  # Explicitly retain the classic workflow regression.
    wizard.name.setText("Cliente sintético — migração")
    wizard.categories["veiculos"].setChecked(True)
    wizard.categories["produtos"].setChecked(True)
    window.grab().save(str(ROOT / "docs/interface-categorias-dashboard.png"))
    wizard.advance()
    car = make_xlsx(["descricao"], [["Veículo sintético"]], "carros.xlsx")
    products = make_xlsx(["Descrição", "Tipo do item"], [["Serviço sintético", "Serviço"]], "servicos.xlsx")
    wizard.add_files([str(car), str(products)])
    category = wizard.controls[1][0]
    category.setCurrentIndex(category.findData("produtos"))
    window.grab().save(str(ROOT / "docs/interface-arquivos-dashboard.png"))
    wizard.advance()
    assert wizard.pages.currentIndex() == 2
    wizard.options.ack.setChecked(True)
    wizard.advance()
    qtbot.waitUntil(lambda: window.worker is None, timeout=15000)
    detail = window.detail
    assert window.pages.currentWidget() is detail and len(detail.sessions) == 2
    assert detail.job["status"] == "Pronta para exportar"
    assert len(window.import_store.list()) == 1
    window.grab().save(str(ROOT / "docs/interface-resumo-dashboard.png"))
    detail.grid.setCurrentIndex(detail.grid.model().index(0, 0))
    detail.review_selected()
    qtbot.waitUntil(lambda: window.worker is None, timeout=10000)
    assert detail.editor is not None and detail.editor.pages.currentIndex() == 2
    detail.editor.correct(0, 2, "descricao", "Veículo revisado sintético")
    detail.leave_editor()
    saved = window.import_store.get(detail.job["id"])
    assert saved["attachments"][0]["corrections"][0]["value"] == "Veículo revisado sintético"
    assert not detail.export_button.isEnabled()
    detail.process_all()
    qtbot.waitUntil(lambda: window.worker is None, timeout=15000)
    first = detail.job["attachments"][0]
    assert next(detail.sessions[first["id"]].rows())["values"]["descricao"] == "Veículo revisado sintético"
    assert detail.export_button.isEnabled()
    window.navigate(1)
    assert window.home.grid.model().rowCount() == 1
    assert window.home.grid.model().rows[0][0] == "Cliente sintético — migração"
    window.grab().save(str(ROOT / "docs/interface-importacoes-dashboard.png"))
    window.close()
    assert not messages


def test_global_color_logo_size_and_reopen(qtbot, tmp_path, monkeypatch):
    window, messages = make_window(qtbot, tmp_path, monkeypatch)
    before = window.styleSheet()
    image = QImage(500, 180, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setPen(QColor("#18344A"))
    font = painter.font()
    font.setPointSize(42)
    painter.setFont(font)
    painter.drawText(image.rect(), Qt.AlignmentFlag.AlignCenter, "MARCA TESTE")
    painter.end()
    path = tmp_path / "logo-sintetica.png"
    assert image.save(str(path))
    appearance = window.appearance
    appearance.load_logo(path)
    appearance.color.setText("#7450A5")
    appearance.brand.setText("Marca sintética")
    appearance.size.setValue(73)
    appearance.opacity.setValue(16)
    appearance.save()
    config = workspace_config(window.root)
    assert config["logo_size"] == 73 and config["logo_opacity"] == 16
    assert config["logo_path"] != str(path) and not window.panel.logo.isNull()
    assert window.styleSheet() != before
    assert palette("#7450A5")["nav"] in window.styleSheet()
    assert palette("#7450A5")["bg"] in window.styleSheet()
    assert window.windowTitle() == "Marca sintética"
    window.navigate(3)
    window.grab().save(str(ROOT / "docs/interface-aparencia-dashboard.png"))
    window.close()
    reopened = Window(ROOT, tmp_path / "state", LocalStore(tmp_path / "state"))
    qtbot.addWidget(reopened)
    assert reopened.appearance.size.value() == 73 and not reopened.panel.logo.isNull()
    assert reopened.windowTitle() == "Marca sintética"
    reopened.close()
    assert not messages


def test_light_and_dark_colors_have_distinct_surfaces():
    assert foreground("#FFFFFF") == "#101820"
    assert foreground("#101820") == "#FFFFFF"
    assert palette("#305AA1")["tint"] != palette("#09695D")["tint"]
    assert palette("#305AA1", "dark")["bg"] != palette("#305AA1", "light")["bg"]
    assert "#101820" in stylesheet("#FFFFFF")


def test_worker_defers_qt_cycle_collection_to_gui_thread(qtbot, tmp_path, monkeypatch):
    """Unreachable widgets must never be finalized by Python's worker GC."""
    import gc
    import threading
    from PySide6.QtWidgets import QLabel

    window, messages = make_window(qtbot, tmp_path, monkeypatch)
    finalized, worker_states = [], []
    gui_thread = threading.get_ident()

    class RetiredWidget(QLabel):
        def __del__(self):
            finalized.append(threading.get_ident())

    retired = RetiredWidget("sintetico")
    retired.cycle = retired
    del retired

    def task(control):
        worker_states.append((threading.get_ident(), gc.isenabled()))
        return "ok"

    window.run_job(task, lambda _: None, "Teste sintetico")
    qtbot.waitUntil(lambda: window.worker is None, timeout=10000)
    assert finalized == [gui_thread]
    assert worker_states[0][0] != gui_thread and not worker_states[0][1]
    assert gc.isenabled() and not messages
    window.close()
