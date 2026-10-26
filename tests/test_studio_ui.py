"""IDE-like workflow exercised with real Qt widgets and a synthetic AI provider."""
import json

from app.core.batch import export_import
from app.core.catalog import workspace_config
from app.storage.workspace import save_config
from app.ui.source_picker import SourcePicker
from tests.test_import_ui import make_window
from tests.test_studio import library


def test_new_project_ai_plan_execution_audit_history(qtbot, tmp_path, make_xlsx, monkeypatch):
    window, messages = make_window(qtbot, tmp_path, monkeypatch)
    prepared = library(tmp_path, make_xlsx, [("ctp.xlsx", ["Documento", "Valor"], "pagar"), ("ctr.xlsx", ["Documento", "Valor"], "receber")])
    save_config(window.root, {**workspace_config(window.root), **workspace_config(prepared)})
    window.reload_library()
    source = make_xlsx(["Documento", "Tipo", "Valor"], [["0001", "P", "10,00"], ["0002", "R", "20,00"]], "recebido.xlsx")
    window.new_import()
    wizard = window.wizard
    assert wizard.studio_mode.isChecked()
    wizard.name.setText("CTP e CTR sintéticos")
    wizard.categories["pagar"].setChecked(True)
    wizard.categories["receber"].setChecked(True)
    wizard.advance()
    wizard.add_files([str(source)])
    wizard.advance()
    assert wizard.pages.currentIndex() == 2
    assert not wizard.options.ack.isChecked()
    wizard.advance()  # Planning project can start without a legacy rule checkbox.
    qtbot.waitUntil(lambda: window.worker is None, timeout=10000)
    detail, sent = window.detail, []
    assert detail.job["mode"] == "studio" and window.worker is None
    pane = detail.studio
    pane.instructions.setPlainText("Tipo P é CTP; Tipo R é CTR. Preserve documento e valor.")
    class SyntheticAI:
        name, model = "Gemini", "synthetic-model"
        def generate(self, data, schema, control):
            control.check()
            sent.append(data)
            if "execution_audit" in data:
                return json.dumps({"summary": "Contagens sintéticas conferidas", "findings": [], "questions": []})
            sid = data["sources"][0]["id"]
            targets = {t["family"]: t["id"] for t in data["targets"]}
            outputs = [{"id": kind, "title": kind.upper(), "target": targets[family], "group": "principal", "rules": [], "inputs": [
                {"source": sid, "filters": [{"column": "C2", "operator": "equals", "values": [value]}], "joins": [],
                 "fields": [{"target": "Documento", "source": "C1"}, {"target": "Valor", "source": "C3"}], "constants": []}]} for kind, family, value in [("ctp", "pagar", "P"), ("ctr", "receber", "R")]]
            return json.dumps({"version": 1, "summary": "Separar CTP e CTR por Tipo", "questions": [], "outputs": outputs, "exclusions": []})
    monkeypatch.setattr(pane, "providers", lambda: [SyntheticAI()])
    monkeypatch.setattr(pane, "consent", lambda *args: True)
    pane.prompt.setPlainText("Planeje as duas saídas.")
    pane.ask_plan()
    qtbot.waitUntil(lambda: window.worker is None and bool(detail.job["studio"].get("plan")), timeout=15000)
    assert "0001" not in json.dumps(sent[0])
    pane.plan_ack.setChecked(True)
    pane.approve_current()
    assert detail.job["studio"]["approval"]
    detail.process_all()
    qtbot.waitUntil(lambda: window.worker is None and len(detail.sessions) == 2, timeout=15000)
    assert detail.job["status"] == "Pronta para exportar"
    assert pane.result_route.count() == 2
    pane.ask_audit()
    qtbot.waitUntil(lambda: window.worker is None and bool(detail.job["studio"].get("ai_audit")), timeout=10000)
    assert len(sent) == 2 and detail.job["studio"]["ai_audit"]["summary"] == "Contagens sintéticas conferidas"
    assert len(pane.history.list(detail.job["id"])) >= 7
    output = export_import(detail.job, detail.sessions, tmp_path / "exported")
    assert len(list(output.rglob("*.xlsx"))) == 2
    window.resize(1420, 940)
    detail.workspace_tabs.setCurrentIndex(0)
    pane.tabs.setCurrentIndex(2)
    window.grab().save(str(tmp_path / "studio-plan.png"))
    from app.storage.workspace import set_brand
    set_brand(window.root, "Transmute", "#ff6900")
    for mode in ["light", "dark"]:
        config = workspace_config(window.root)
        config["theme_mode"] = mode
        save_config(window.root, config)
        window.apply_brand()
        qtbot.wait(20)
        window.grab().save(str(tmp_path / ("studio-plan-" + mode + ".png")))
    pane.tabs.setCurrentIndex(5)
    pane.result_grid.setCurrentIndex(pane.result_grid.model().index(0, 2))
    window.grab().save(str(tmp_path / "studio-results.png"))
    # A local correction is saved, invalidates approval and goes through the
    # complete engine again; the received workbook remains unchanged.
    pane.result_route.setCurrentIndex(pane.result_route.findData("ctp"))
    pane.result_grid.setCurrentIndex(pane.result_grid.model().index(0, 2))
    from PySide6.QtWidgets import QInputDialog
    monkeypatch.setattr(QInputDialog, "getText", lambda *args, **kwargs: ("0003", True))
    pane.correct_cell()
    assert not detail.job["studio"]["approval"] and not detail.sessions
    pane.validate_draft()
    pane.plan_ack.setChecked(True)
    pane.approve_current()
    detail.process_all()
    qtbot.waitUntil(lambda: window.worker is None and len(detail.sessions) == 2, timeout=15000)
    assert next(detail.sessions["ctp"].rows())["values"]["Documento"] == "0003"
    assert not messages
    window.close()


def test_folder_picker_requires_explicit_tables(qtbot, tmp_path):
    entries = [{"path": str(tmp_path / "origem.xlsx"), "title": "Origem", "source_sheet": sheet, "error": ""} for sheet in ("CTP", "CTR")]
    picker = SourcePicker(entries)
    qtbot.addWidget(picker)
    picker.accept_selection()
    assert not picker.selected
    picker.mark(True)
    picker.accept_selection()
    assert [e["source_sheet"] for e in picker.selected] == ["CTP", "CTR"]


def test_provider_editor_preserves_primary_and_each_credential(qtbot, tmp_path, monkeypatch):
    from app.ai.credentials import Credentials
    import app.ui.settings as settings_module
    credentials = Credentials()
    monkeypatch.setattr(settings_module, "credentials", credentials)
    window, messages = make_window(qtbot, tmp_path, monkeypatch)
    pane = window.settings
    pane.provider.setCurrentText("OpenAI")
    pane.model.setText("synthetic-openai")
    pane.key.setText("synthetic-openai-key")
    pane.provider.setCurrentText("Gemini")
    pane.model.setText("synthetic-gemini")
    pane.key.setText("synthetic-gemini-key")
    pane.provider.setCurrentText("Claude")
    pane.model.setText("synthetic-claude")
    pane.key.setText("synthetic-claude-key")
    pane.primary.setCurrentText("OpenAI")
    assert pane.save(quiet=True)
    config = window.store.setting("ai")
    assert config["provider"] == "OpenAI" and len(config["models"]) == 3
    assert credentials.get("Gemini") == "synthetic-gemini-key"
    assert credentials.get("Claude") == "synthetic-claude-key"
    assert "synthetic-gemini-key" not in json.dumps(config)
    assert not messages
    window.close()


def test_provider_controls_remain_accessible_in_small_window(qtbot, tmp_path, monkeypatch):
    window, messages = make_window(qtbot, tmp_path, monkeypatch)
    window.resize(1100, 760)
    window.navigate(4)
    qtbot.wait(40)
    assert window.settings.scroll.horizontalScrollBar().maximum() == 0
    assert window.settings.save_button.isVisible()
    assert window.settings.save_button.height() >= 30
    assert not messages
    window.close()
