"""Detalhes de um trabalho e ponte para o conversor existente por arquivo/lote.

O trabalho possui as sessões; editores apenas as usam enquanto estão abertos.
Revalidação substitui sessões e mantém correções manuais necessárias à retomada.
"""
import uuid
from dataclasses import asdict
from itertools import islice
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QHBoxLayout, QInputDialog, QMessageBox, QStackedWidget, QVBoxLayout, QWidget

from app.core.batch import export_import, groups, options_from, process_import
from app.core.importers.reader import inspect, records, sheets
from app.core.session import validate_links
from app.models import Decision
from app.storage.imports import FAMILIES
from app.ui.common import GridModel, button, table, text_label
from app.ui.conversion import ConversionPane
from app.ui.file_settings import FileSettings, open_pdf
from app.ui.options import OptionsPane


class ImportDetail(QWidget):
    changed = Signal()
    back_requested = Signal()

    def __init__(self, root, state, layouts, store, imports, run_job, notify):
        super().__init__()
        self.root, self.state, self.layouts, self.store, self.imports = root, state, layouts, store, imports
        self.run_job, self.notify = run_job, notify
        self.job, self.sessions, self.editor = None, {}, None
        body = QVBoxLayout(self)
        toolbar = QHBoxLayout()
        toolbar.addWidget(button("Voltar às importações", self.back_requested.emit))
        toolbar.addStretch()
        toolbar.addWidget(button("Renomear", self.rename))
        body.addLayout(toolbar)
        self.title = text_label("", "title")
        self.subtitle = text_label("", "subtitle")
        body.addWidget(self.title)
        body.addWidget(self.subtitle)
        self.pages = QStackedWidget()
        summary = QWidget()
        box = QVBoxLayout(summary)
        actions = QHBoxLayout()
        self.process_button = button("Processar arquivos", self.process_all, True)
        self.export_button = button("Exportar importação", lambda: self.do_export(False))
        actions.addWidget(self.process_button)
        actions.addWidget(self.export_button)
        actions.addWidget(button("Relatório", lambda: self.do_export(True)))
        actions.addStretch()
        actions.addWidget(button("Regras deste trabalho", self.edit_options))
        box.addLayout(actions)
        self.grid = table()
        self.grid.doubleClicked.connect(self.review_selected)
        box.addWidget(self.grid, 1)
        file_actions = QHBoxLayout()
        file_actions.addWidget(button("Revisar arquivo", self.review_selected))
        file_actions.addWidget(button("Editar título / categoria / vínculo", self.edit_selected))
        file_actions.addWidget(button("Adicionar arquivo…", self.add_file))
        file_actions.addWidget(button("Conferir PDF original", self.view_pdf))
        file_actions.addStretch()
        box.addLayout(file_actions)
        self.notice = text_label("", "notice")
        box.addWidget(self.notice)
        self.pages.addWidget(summary)
        body.addWidget(self.pages, 1)

    def set_job(self, job):
        if self.job and self.job["id"] != job["id"]:
            self.close_sessions()
        self.job = job
        self.refresh()

    def refresh(self):
        if not self.job:
            return
        self.title.setText(self.job["name"])
        self.subtitle.setText(f"{self.job['status']} · {len(self.job['attachments'])} arquivos · " + ", ".join(FAMILIES[c] for c in self.job["categories"]))
        rows = [[a["title"], FAMILIES[a["family"]], a.get("source_sheet", Path(a["path"]).suffix.upper().lstrip(".")),
                 a.get("status", "Aguardando"), a.get("stats", {}).get("read", "—"), a.get("group", "principal")] for a in self.job["attachments"]]
        self.grid.setModel(GridModel(["Arquivo / título", "Categoria", "Aba ou tabela", "Andamento", "Registros", "Grupo"], rows, parent=self.grid))
        for col, width in enumerate([270, 155, 155, 205, 90, 100]):
            self.grid.setColumnWidth(col, width)
        pending = [a for a in self.job["attachments"] if a.get("status") == "Precisa de revisão"]
        missing = [a for a in self.job["attachments"] if a.get("role") != "reference" and a["id"] not in self.sessions]
        self.export_button.setEnabled(not pending and not missing and not self.job.get("link_message"))
        self.notice.setText(self.job.get("link_message") or ("Alguns arquivos precisam de revisão. Selecione um e clique em Revisar arquivo para ver o motivo e ajustar o mapeamento." if pending else
                            "Reprocesse os arquivos para abrir os resultados desta importação." if missing else
                            "Revise os resultados antes de exportar. Originais são preservados; correções manuais e referências são salvas localmente neste trabalho."))
        self.grid.selectionModel().selectionChanged.connect(self.selection_changed)

    def selection_changed(self, *args):
        item = self.selected()
        if item and item.get("message"):
            self.notice.setText(item["message"])

    def selected(self):
        row = self.grid.currentIndex().row()
        return self.job["attachments"][row] if self.job and 0 <= row < len(self.job["attachments"]) else None

    def save(self):
        self.imports.save(self.job)
        self.refresh()
        self.changed.emit()

    def process_all(self):
        if not self.job:
            return
        self.close_sessions()
        for item in self.job["attachments"]:
            if item.get("role") != "reference":
                item["status"] = "Aguardando processamento"
                item.pop("stats", None)
        self.job["status"] = "Em processamento"
        self.save()
        self.run_job(lambda control: process_import(self.root, self.state, self.job, control), self.processed,
                     "Lendo e tratando os arquivos da importação…", self.processing_failed)

    def processing_failed(self, message):
        self.job["status"] = "Interrompida"
        self.save()

    def processed(self, result):
        self.close_sessions()
        self.job, self.sessions = result
        self.save()

    def recalculate_status(self):
        pending = any(a.get("role") != "reference" and a.get("status") != "Pronto para exportar" for a in self.job["attachments"])
        self.job.pop("link_message", None)
        try:
            for group in groups(self.job, self.sessions):
                messages = [p.message for p in validate_links(group[0], group[1] if len(group) > 1 else None) if p.severity == "ERRO"]
                if messages:
                    pending = True
                    self.job["link_message"] = "\n".join(messages)
        except ValueError as error:
            pending = True
            self.job["link_message"] = str(error)
        self.job["status"] = "Revisar pendências" if pending else "Pronta para exportar"

    def edit_options(self):
        if not self.job:
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Regras desta importação")
        dialog.resize(950, 710)
        box = QVBoxLayout(dialog)
        options = OptionsPane()
        options.set_options(options_from(self.job["options"]))
        options.configure_categories(self.job["categories"], any(a["path"].lower().endswith(".pdf") for a in self.job["attachments"]))
        box.addWidget(options)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        box.addWidget(buttons)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.job["options"] = asdict(options.get())
            self.close_sessions()
            for item in self.job["attachments"]:
                item.pop("options", None)
                item["status"] = "Aguardando reprocessamento"
            self.job["status"] = "Aguardando processamento"
            self.save()

    def rename(self):
        if self.job:
            name, ok = QInputDialog.getText(self, "Renomear importação", "Nome", text=self.job["name"])
            if ok and name.strip() and len(name) <= 120:
                self.job["name"] = name.strip()
                self.save()

    def edit_selected(self):
        item = self.selected()
        if item:
            self.edit_item(item)

    def add_file(self):
        if self.job:
            self.edit_item({"id": uuid.uuid4().hex, "family": self.job["categories"][0]})

    def edit_item(self, item):
        dialog = FileSettings(item, self.layouts, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        previous = next((i for i, a in enumerate(self.job["attachments"]) if a["id"] == item["id"]), None)
        if previous is None:
            self.job["attachments"].append(dialog.item)
        else:
            self.job["attachments"][previous] = dialog.item
        session = self.sessions.pop(item["id"], None)
        if session:
            session.close()
        if dialog.item["family"] not in self.job["categories"]:
            self.job["categories"].append(dialog.item["family"])
        self.recalculate_status()
        self.save()

    def view_pdf(self):
        item = self.selected()
        if item and Path(item["path"]).suffix.lower() == ".pdf":
            open_pdf(item["path"], self)
        else:
            self.notify("Selecione um arquivo PDF para conferir o documento original.")

    def review_selected(self, *args):
        item = self.selected()
        if not item:
            self.notify("Selecione um arquivo na lista para revisar.")
            return
        if item.get("role") == "reference":
            if Path(item["path"]).suffix.lower() == ".pdf":
                open_pdf(item["path"], self)
            else:
                self.notify("Documento de apoio. Para convertê-lo, altere a finalidade em Editar título / categoria / vínculo.")
            return
        chosen = next((entry for entry in self.layouts if str(entry.path) == item.get("layout_path") and entry.sheet == item.get("layout_sheet")), None)
        if not chosen:
            self.edit_item(item)
            return
        related = []
        if chosen.variant in {"header", "items"}:
            opposite = "items" if chosen.variant == "header" else "header"
            for candidate in self.job["attachments"]:
                layout = next((entry for entry in self.layouts if str(entry.path) == candidate.get("layout_path") and entry.sheet == candidate.get("layout_sheet")), None)
                if layout and layout.family == chosen.family and layout.variant == opposite and layout.path.parent == chosen.path.parent and candidate.get("group", "principal") == item.get("group", "principal"):
                    related.append(candidate)
        items = [item] + (related if len(related) == 1 else [])
        def read(control):
            result = []
            for record in items:
                available = sheets(record["path"], control)
                source = inspect(record["path"], record.get("source_sheet"), record.get("header_row"), record.get("encoding"), record.get("delimiter"), control)
                result.append((source, available, list(islice(records(source, control), 20))))
            return result
        self.run_job(read, lambda loaded: self.open_editor(items, loaded), "Preparando revisão do arquivo…")

    def open_editor(self, items, loaded):
        self.leave_editor()
        editor = ConversionPane(self.root, self.state, self.layouts, self.store, self.run_job, self.notify)
        self.editor = editor
        self.editor_items = items
        editor.linked.setChecked(len(items) == 2)
        for pane, item, source_data in zip(editor.panes(), items, loaded):
            for index in range(pane.layout_box.count()):
                layout = pane.layout_box.itemData(index)
                if str(layout.path) == item["layout_path"] and layout.sheet == item["layout_sheet"]:
                    pane.layout_box.setCurrentIndex(index)
                    break
            pane.path.setText(item["path"])
            pane.loaded(source_data)
        editor.prepare_mapping([value[2] for value in loaded])
        for mapping, item in zip(editor.mappings, items):
            if item.get("mapping") and (not item.get("source_headers") or item["source_headers"] == mapping.source.headers):
                mapping.decisions = [Decision(**d) for d in item["mapping"]]
                mapping.render()
        editor.options.set_options(options_from(items[0].get("options", self.job["options"])))
        editor.options.configure_categories([a["family"] for a in items], any(Path(a["path"]).suffix.lower() == ".pdf" for a in items))
        for index, item in enumerate(items):
            editor.options.overrides[index] = {(c["line"], c["field"]): c["value"] for c in item.get("corrections", [])}
        if all(a["id"] in self.sessions for a in items):
            editor.processed([self.sessions[a["id"]] for a in items])
        editor.processed_event.connect(lambda sessions: self.review_processed(items, sessions))
        wrapper = QWidget()
        box = QVBoxLayout(wrapper)
        top = QHBoxLayout()
        top.addWidget(button("Voltar ao resumo da importação", self.leave_editor))
        if Path(items[0]["path"]).suffix.lower() == ".pdf":
            top.addWidget(button("Conferir PDF original", lambda: open_pdf(items[0]["path"], self)))
        top.addStretch()
        box.addLayout(top)
        box.addWidget(editor, 1)
        self.pages.addWidget(wrapper)
        self.pages.setCurrentWidget(wrapper)

    def review_processed(self, items, sessions):
        for item, session in zip(items, sessions):
            self.sessions[item["id"]] = session
            data = asdict(session.options)
            data.pop("overrides")
            item.update(options=data, source_sheet=session.source.sheet, header_row=session.source.header_row,
                        encoding=session.source.encoding, delimiter=session.source.delimiter,
                        mapping=[asdict(d) for d in session.decisions], stats=session.stats(), source_headers=session.source.headers, source_sha256=session.source_hash,
                        corrections=[{"line": line, "field": field, "value": value} for (line, field), value in session.options.overrides.items()])
            pending = session.stats()["errors"] or any(p.severity == "ERRO" for p in session.global_issues)
            item["status"] = "Precisa de revisão" if pending else "Pronto para exportar"
            item["message"] = "\n".join(p.message for p in session.global_issues if p.severity == "ERRO")
        self.recalculate_status()
        self.save()

    def leave_editor(self):
        if self.editor:
            if self.editor.dirty:
                for index, item in enumerate(self.editor_items):
                    item["corrections"] = [{"line": line, "field": field, "value": value} for (line, field), value in self.editor.options.overrides[index].items()]
                    item["status"] = "Aguardando reprocessamento"
                    session = self.sessions.pop(item["id"], None)
                    if session:
                        session.close()
                self.job["status"] = "Revisar pendências"
                self.save()
            self.editor.release_sessions()
            self.editor = None
        while self.pages.count() > 1:
            widget = self.pages.widget(1)
            self.pages.removeWidget(widget)
            widget.deleteLater()
        self.pages.setCurrentIndex(0)

    def do_export(self, reports_only):
        if not self.job:
            return
        dest = QFileDialog.getExistingDirectory(self, "Pasta para salvar esta importação")
        if not dest:
            return
        audit = False
        if not reports_only:
            audit = QMessageBox.question(self, "Auditoria detalhada", "Incluir valores originais e transformados na auditoria? Esse arquivo contém dados sensíveis.", defaultButton=QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes
        self.run_job(lambda control: export_import(self.job, self.sessions, dest, control, reports_only, audit),
                     lambda path: self.exported(path, reports_only), "Exportando tabelas e relatórios da importação…")

    def exported(self, path, reports_only):
        self.job["exports"].append(str(path))
        if not reports_only:
            self.job["status"] = "Exportada"
        self.save()
        self.notify(f"{'Relatório' if reports_only else 'Importação'} salvo em:\n{path}")

    def close_sessions(self):
        self.leave_editor()
        for session in self.sessions.values():
            session.close()
        self.sessions = {}
