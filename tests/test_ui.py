from PySide6.QtCore import Qt

from app.storage.local import LocalStore
from app.ui.style import STYLE
from app.ui.window import Window
from tests.conftest import ROOT, synthetic_cpf


def test_desktop_full_flow_and_review(qtbot, tmp_path, make_xlsx, monkeypatch):
    messages = []
    monkeypatch.setattr(Window, "notify", lambda self, message: messages.append(message))
    window = Window(ROOT, tmp_path / "state", LocalStore(tmp_path / "state"))
    window.setStyleSheet(STYLE)
    qtbot.addWidget(window)
    window.show()
    assert window.pages.currentIndex() == 0
    # The same converter now lives inside an import's file review.
    from app.ui.conversion import ConversionPane
    conversion = ConversionPane(window.root, window.state, window.layouts, window.store, window.run_job, window.notify)
    window.pages.addWidget(conversion)
    window.pages.setCurrentWidget(conversion)
    pane = conversion.main_input
    for i in range(pane.layout_box.count()):
        layout = pane.layout_box.itemData(i)
        if layout.family == "clientes" and layout.path.parent.name == "V1":
            pane.layout_box.setCurrentIndex(i)
            break
    file = make_xlsx(["Nome", "CPF", "UF"], [["Pessoa sintética", synthetic_cpf(), "SC"]])
    pane.set_path(file)
    qtbot.waitUntil(lambda: window.worker is None, timeout=10000)
    assert pane.source is not None
    qtbot.mouseClick(conversion.next, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.worker is None, timeout=10000)
    assert conversion.pages.currentIndex() == 1
    conversion.options.active.setCurrentIndex(2)
    conversion.options.columns.setCurrentIndex(1)
    conversion.options.ack.setChecked(True)
    conversion.options.geography.setChecked(True)
    conversion.options.geo_evidence.setText("Fonte sintética de teste")
    qtbot.mouseClick(conversion.next, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.worker is None, timeout=10000)
    assert conversion.pages.currentIndex() == 2
    assert conversion.sessions[0].stats()["read"] == 1
    conversion.correct(0, 2, "Razão Social / Nome", "Pessoa revisada sintética")
    assert not conversion.next.isEnabled()
    qtbot.mouseClick(conversion.revalidate, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.worker is None, timeout=10000)
    assert conversion.next.isEnabled()
    assert next(conversion.sessions[0].rows())["values"]["Razão Social / Nome"] == "Pessoa revisada sintética"
    (ROOT / "docs").mkdir(exist_ok=True)
    window.grab().save(str(ROOT / "docs/interface-revisao-dashboard.png"))
    from app.core.catalog import workspace_config
    from app.storage.workspace import save_config
    config = workspace_config(window.root)
    config["theme_mode"] = "dark"
    save_config(window.root, config)
    window.apply_brand()
    qtbot.wait(30)
    window.grab().save(str(ROOT / "docs/interface-revisao-escuro.png"))
    conversion.close_sessions()
    window.close()
    assert not messages


def test_initial_rule_editor_saves_revision_without_touching_original(qtbot, tmp_path, monkeypatch):
    import json
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication, QCheckBox, QDialogButtonBox, QPlainTextEdit
    from app.core.catalog import digest, rules_path, verify_rules
    original = digest(ROOT / "INSTRUCOES_CONVERSOES.md")
    monkeypatch.setattr(Window, "notify", lambda self, message: None)
    window = Window(ROOT, tmp_path / "state", LocalStore(tmp_path / "state"))
    qtbot.addWidget(window)
    window.show()
    def edit():
        dialog = QApplication.activeModalWidget()
        editors = dialog.findChildren(QPlainTextEdit)
        editors[0].setPlainText("# Regras sintéticas da biblioteca\nNome é obrigatório.")
        editors[1].setPlainText(json.dumps({"max_total_rows": 10000, "enabled_modules": [], "rules": [{"id": "NOME", "field": "Nome", "operation": "required"}]}))
        dialog.findChild(QCheckBox).setChecked(True)
        box = dialog.findChild(QDialogButtonBox)
        qtbot.mouseClick(box.button(QDialogButtonBox.StandardButton.Save), Qt.MouseButton.LeftButton)
    QTimer.singleShot(20, edit)
    window.library.edit_rules()
    assert rules_path(window.root) != ROOT / "INSTRUCOES_CONVERSOES.md"
    assert verify_rules(window.root)["rules"][0]["id"] == "NOME"
    assert digest(ROOT / "INSTRUCOES_CONVERSOES.md") == original
    window.close()


def test_bad_model_folder_is_recoverable(qtbot, tmp_path, monkeypatch):
    from app.storage.workspace import initialize, save_config
    from app.core.catalog import workspace_config
    state = tmp_path / "state"
    root = initialize(ROOT, state)
    bad = tmp_path / "bad-models"
    bad.mkdir()
    (bad / "quebrado.xlsx").write_bytes(b"invalid workbook")
    config = workspace_config(root)
    config["models_dir"] = str(bad)
    save_config(root, config)
    monkeypatch.setattr(Window, "notify", lambda self, message: None)
    window = Window(ROOT, state, LocalStore(state))
    qtbot.addWidget(window)
    assert not window.layouts
    assert "Não foi possível" in window.library.model_path.text()
    window.close()
