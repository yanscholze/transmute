"""Dashboard usa metadados reais e não inventa taxa, atividade ou estado externo."""
from dataclasses import asdict

import pytest
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication

from app.core.catalog import workspace_config
from app.storage.dashboard import summarize
from app.storage.local import LocalStore
from app.storage.workspace import save_config
from app.ui.theme import contrast, palette
from app.ui.window import Window
from tests.conftest import ROOT


def window_for(qtbot, tmp_path, monkeypatch):
    monkeypatch.setattr(Window, "notify", lambda self, text: None)
    window = Window(ROOT, tmp_path / "state", LocalStore(tmp_path / "state"))
    # Branding is synthetic in every screenshot; real user work is not loaded.
    config = workspace_config(window.root)
    config.update(brand="Transmute", primary_color="#FF790F")
    save_config(window.root, config)
    window.apply_brand()
    qtbot.addWidget(window)
    window.show()
    return window


def create_job(window, path, layout, options, name, status):
    item = {"id": name, "path": str(path), "title": path.stem, "family": "veiculos", "role": "source",
            "layout_path": str(layout.path), "layout_sheet": layout.sheet, "status": "Aguardando"}
    job = window.import_store.create(name, ["veiculos"], [item], asdict(options))
    job["status"] = status
    window.import_store.save(job)
    return job


def test_success_uses_latest_jobs_not_technical_events():
    jobs = [{"status": value} for value in ["Pronta para exportar", "Exportada", "Revisar pendências", "Aguardando processamento", "Interrompida"]]
    result = summarize(jobs)
    assert result == {"total": 5, "ready": 1, "exported": 1, "assessed": 3, "successful": 2, "pending": 2, "rate": 67}
    assert summarize([])["rate"] is None
    assert summarize([{"status": "Interrompida"}])["rate"] is None
    assert summarize([{"status": "Revisar pendências"}])["rate"] == 0


@pytest.mark.parametrize("mode", ["light", "dark"])
@pytest.mark.parametrize("color", ["#FF790F", "#FFFFFF", "#000000", "#7450A5", "#777777"])
def test_theme_contrast_and_independent_accent(mode, color):
    t = palette(color, mode)
    assert contrast(t["ink"], t["surface"]) >= 4.5
    assert contrast(t["muted"], t["surface"]) >= 4.5
    assert contrast(t["on"], t["primary"]) >= 4.5
    assert contrast(t["focus"], t["surface"]) >= 3
    for key in ["error", "warning", "success"]:
        assert contrast(t[key], t["field"]) >= 4.5
    assert palette(color, mode)["surface"] == palette("#305AA1", mode)["surface"]


def test_sidebar_expansion_navigation_search_and_paths(qtbot, tmp_path, monkeypatch, make_xlsx, layout, options):
    window = window_for(qtbot, tmp_path, monkeypatch)
    assert window.pages.currentWidget() is window.dashboard
    assert window.dashboard.summary["total"] == 0 and window.dashboard.rate.text() == "—"
    assert not window.dashboard.recent_buttons
    assert window.sidebar.width() == 76
    assert all(control.accessibleName() and control.toolTip() for control in window.nav_buttons)
    qtbot.mouseClick(window.sidebar.toggle, Qt.MouseButton.LeftButton)
    assert window.sidebar.width() == 218 and window.sidebar.toggle.isChecked()
    assert window.store.setting("ui_sidebar_expanded") is True
    for index, control in enumerate(window.nav_buttons):
        qtbot.mouseClick(control, Qt.MouseButton.LeftButton)
        assert window.pages.currentIndex() == index
    window.navigate(0)
    for index, (control, _, _, _) in enumerate(window.dashboard.shortcuts, 1):
        control.click()
        assert window.pages.currentIndex() == index
        window.navigate(0)
    job = create_job(window, make_xlsx(["descricao"], [["Veículo sintético"]]), layout("veiculos"), options, "Importação Alfa sintética", "Pronta para exportar")
    window.refresh_overview()
    window.search.setText("Alfa")
    qtbot.keyClick(window.search, Qt.Key.Key_Return)
    assert window.pages.currentWidget() is window.home
    assert window.home.search.text() == "Alfa" and window.home.grid.model().rowCount() == 1
    window.navigate(0)
    window.dashboard.recent_buttons[0].click()
    assert window.pages.currentWidget() is window.detail and window.detail.job["id"] == job["id"]
    window.navigate(0)
    target = window.dashboard.rules_path
    target.copy.click()
    assert QApplication.clipboard().text() == target.field.text()
    opened = []
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda url: opened.append(url) or True)
    target.open.click()
    assert opened == [QUrl.fromLocalFile(str(target.path.parent))]
    edits = []
    monkeypatch.setattr(window.library, "edit_rules", lambda: edits.append(True))
    window.dashboard.rules_editor.click()
    assert window.pages.currentWidget() is window.library and edits
    window.close()
    reopened = Window(ROOT, tmp_path / "state", LocalStore(tmp_path / "state"))
    qtbot.addWidget(reopened)
    assert reopened.sidebar.expanded and reopened.sidebar.width() == 218
    reopened.close()


def test_light_dark_custom_accent_keeps_sessions_and_creates_previews(qtbot, tmp_path, monkeypatch, make_xlsx, layout, options):
    window = window_for(qtbot, tmp_path, monkeypatch)
    path = make_xlsx(["descricao"], [["Veículo sintético"]])
    for name, status in [("Oficina Horizonte · lote 01", "Exportada"), ("Frota Aurora · lote 02", "Revisar pendências"),
                         ("Comercial Leste · lote 03", "Pronta para exportar"), ("Serviços Atlas · lote 04", "Exportada")]:
        create_job(window, path, layout("veiculos"), options, name, status)
    window.refresh_overview()
    assert window.dashboard.summary["rate"] == 75 and len(window.dashboard.recent_buttons) == 4
    assert "Serviços Atlas" in window.dashboard.recent_buttons[0].accessibleName()
    # Process one source to prove theme changes do not close/recreate review data.
    job = window.import_store.list()[0]
    window.open_import(job["id"])
    window.detail.process_all()
    qtbot.waitUntil(lambda: window.worker is None, timeout=10000)
    session = next(iter(window.detail.sessions.values()))
    window.navigate(0)
    window.search.clearFocus()
    qtbot.wait(180)
    window.grab().save(str(ROOT / "docs/interface-dashboard-claro.png"))
    window.theme_button.click()
    assert workspace_config(window.root)["theme_mode"] == "dark"
    assert window.appearance.mode.currentData() == "dark"
    assert session.path.is_file() and session.stats()["read"] == 1
    qtbot.wait(180)
    window.grab().save(str(ROOT / "docs/interface-dashboard-escuro.png"))
    window.sidebar.toggle.click()
    qtbot.wait(180)
    for target in [window.dashboard.models_path, window.dashboard.rules_path]:
        assert target.rect().contains(target.open.geometry())
    window.grab().save(str(ROOT / "docs/interface-dashboard-expandido.png"))
    window.resize(1100, 760)
    qtbot.wait(180)
    assert window.width() == 1100
    assert window.dashboard.horizontalScrollBar().maximum() == 0
    window.grab().save(str(ROOT / "docs/interface-dashboard-compacto.png"))
    appearance = window.appearance
    appearance.color.setText("#46B4B8")
    appearance.mode.setCurrentIndex(appearance.mode.findData("dark"))
    appearance.save()
    assert workspace_config(window.root)["primary_color"] == "#46B4B8"
    assert palette("#46B4B8", "dark")["primary"] in window.styleSheet()
    assert session.path.is_file()
    window.close()
    reopened = Window(ROOT, tmp_path / "state", LocalStore(tmp_path / "state"))
    qtbot.addWidget(reopened)
    assert reopened.appearance.mode.currentData() == "dark"
    assert reopened.appearance.color.text() == "#46B4B8"
    reopened.close()


def test_appearance_draft_and_save_remain_accessible_in_small_window(qtbot, tmp_path, monkeypatch):
    window = window_for(qtbot, tmp_path, monkeypatch)
    window.sidebar.toggle.click()
    window.resize(1100, 760)
    window.navigate(3)
    appearance = window.appearance
    appearance.mode.setCurrentIndex(appearance.mode.findData("dark"))
    assert workspace_config(window.root).get("theme_mode", "light") == "light"
    assert palette("#FF790F", "dark")["ink"] in appearance.preview.styleSheet()
    qtbot.wait(30)
    qtbot.wait(30)
    assert appearance.scroll.horizontalScrollBar().maximum() == 0
    point = appearance.save_button.mapTo(appearance, appearance.save_button.rect().center())
    assert appearance.rect().contains(point)
    appearance.save_button.click()
    assert workspace_config(window.root)["theme_mode"] == "dark"
    window.close()
