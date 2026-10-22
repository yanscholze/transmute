"""Shell: trabalhos, biblioteca e aparência têm áreas próprias.

O worker único mantém cancelamento acessível. Aparência nunca reinicia uma
importação; mudanças da biblioteca exigem nova validação do trabalho.
"""
import json

from PySide6.QtWidgets import QButtonGroup, QFrame, QHBoxLayout, QMainWindow, QProgressBar, QStackedWidget, QVBoxLayout, QWidget

from app.core.catalog import discover, workspace_config
from app.storage.imports import ImportStore
from app.storage.workspace import initialize
from app.ui.common import GridModel, Worker, button, table, text_label
from app.ui.theme import Backdrop, stylesheet


class Window(QMainWindow):
    def __init__(self, root, state, store):
        super().__init__()
        self.root, self.state, self.store = initialize(root, state), state, store
        self.import_store = ImportStore(store)
        self.worker, self.closing, self.wizard, self.error_callback = None, False, None, None
        try:
            self.layouts = discover(self.root)
        except Exception:
            self.layouts = []
        self.resize(1420, 940)
        self.setMinimumSize(1100, 760)
        shell = QWidget()
        shell_box = QVBoxLayout(shell)
        shell_box.setContentsMargins(0, 0, 0, 0)
        self.body = QWidget()
        body_box = QHBoxLayout(self.body)
        body_box.setContentsMargins(0, 0, 0, 0)
        body_box.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(214)
        nav = QVBoxLayout(sidebar)
        nav.setContentsMargins(18, 24, 18, 22)
        nav.setSpacing(10)
        self.brand_label = text_label("Conversor de Bases", "brand")
        nav.addWidget(self.brand_label)
        nav.addWidget(text_label("Importações para o ERP"))
        nav.addSpacing(30)
        self.pages = QStackedWidget()
        from app.ui.imports_home import ImportsHome
        from app.ui.library import LibraryPane
        from app.ui.appearance import AppearancePane
        from app.ui.settings import SettingsPane
        from app.ui.import_detail import ImportDetail
        self.home = ImportsHome(self.import_store, self.new_import, self.open_import)
        self.library = LibraryPane(self.root, self.notify, self.new_import)
        self.library.changed.connect(self.reload_library)
        self.appearance = AppearancePane(self.root, self.notify)
        self.appearance.changed.connect(self.apply_brand)
        self.settings = SettingsPane(store, state, self.run_job, self.notify)
        self.history_page = self.make_history()
        self.detail = ImportDetail(self.root, state, self.layouts, store, self.import_store, self.run_job, self.notify)
        self.detail.changed.connect(self.home.refresh)
        self.detail.back_requested.connect(lambda: self.navigate(0))
        for page in [self.home, self.library, self.appearance, self.settings, self.history_page, self.detail]:
            self.pages.addWidget(page)
        group = QButtonGroup(self)
        group.setExclusive(True)
        self.nav_buttons = []
        for index, label in enumerate(["Importações", "Biblioteca", "Aparência", "IA e perfis", "Diagnóstico"]):
            item = button(label, lambda checked=False, i=index: self.navigate(i))
            item.setCheckable(True)
            group.addButton(item)
            nav.addWidget(item)
            self.nav_buttons.append(item)
        self.nav_buttons[0].setChecked(True)
        nav.addStretch()
        nav.addWidget(text_label("Conversão local\nOriginais preservados\n\nVersão 1.1.0"))
        body_box.addWidget(sidebar)
        self.panel = Backdrop()
        panel_box = QVBoxLayout(self.panel)
        panel_box.setContentsMargins(28, 26, 28, 22)
        panel_box.addWidget(self.pages)
        body_box.addWidget(self.panel, 1)
        shell_box.addWidget(self.body, 1)
        statusbar = QWidget()
        status_layout = QHBoxLayout(statusbar)
        status_layout.setContentsMargins(18, 8, 18, 8)
        self.status = text_label("Pronto · crie ou abra uma importação", "muted")
        self.progress = QProgressBar()
        self.progress.setFixedWidth(220)
        self.progress.setTextVisible(False)
        self.progress.hide()
        self.cancel = button("Cancelar operação", self.cancel_job)
        self.cancel.hide()
        status_layout.addWidget(self.status, 1)
        status_layout.addWidget(self.progress)
        status_layout.addWidget(self.cancel)
        shell_box.addWidget(statusbar)
        self.setCentralWidget(shell)
        self.apply_brand()

    def notify(self, message):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, self.windowTitle() or "Conversor de Bases", message)

    def navigate(self, index):
        if self.pages.currentWidget() is self.detail:
            self.detail.leave_editor()
        self.nav_buttons[index].setChecked(True)
        if index == 0:
            self.home.refresh()
        elif index == 3:
            self.settings.refresh_profiles()
        elif index == 4:
            self.refresh_history()
        self.pages.setCurrentIndex(index)
        config = workspace_config(self.root)
        self.panel.configure({**config, "logo_path": ""} if index == 2 else config)

    def new_import(self):
        from app.ui.import_wizard import ImportWizard
        if self.wizard is None:
            self.wizard = ImportWizard(self.import_store, self.layouts, self.notify)
            self.wizard.created.connect(self.import_created)
            self.wizard.cancelled.connect(self.cancel_wizard)
            self.pages.addWidget(self.wizard)
        self.nav_buttons[0].setChecked(True)
        self.pages.setCurrentWidget(self.wizard)

    def cancel_wizard(self):
        if self.wizard:
            self.pages.removeWidget(self.wizard)
            self.wizard.deleteLater()
            self.wizard = None
        self.navigate(0)

    def import_created(self, job):
        self.cancel_wizard()
        self.open_import(job["id"])
        self.detail.process_all()

    def open_import(self, identifier):
        self.detail.leave_editor()
        self.detail.set_job(self.import_store.get(identifier))
        self.nav_buttons[0].setChecked(True)
        self.pages.setCurrentWidget(self.detail)

    def apply_brand(self):
        config = workspace_config(self.root)
        self.setWindowTitle(config.get("brand", "Conversor de Bases"))
        self.brand_label.setText(config.get("brand", "Conversor de Bases"))
        self.setStyleSheet(stylesheet(config.get("primary_color", "#09695D")))
        self.panel.configure({**config, "logo_path": ""} if self.pages.currentWidget() is self.appearance else config)

    def reload_library(self):
        try:
            self.layouts = discover(self.root)
        except Exception as error:
            self.layouts = []
            self.notify(str(error))
        self.detail.close_sessions()
        self.detail.layouts = self.layouts
        if self.detail.job:
            self.detail.job["status"] = "Aguardando processamento"
            for item in self.detail.job["attachments"]:
                if item.get("role") != "reference":
                    item["status"] = "Aguardando reprocessamento"
            self.detail.save()
        if self.wizard:
            self.wizard.snapshot()
            self.wizard.layouts = self.layouts
            self.wizard.render_files()

    def run_job(self, task, callback, description, on_error=None):
        if self.worker is not None:
            return
        self.error_callback = on_error
        self.status.setText(description)
        self.body.setEnabled(False)
        self.progress.setRange(0, 0)
        self.progress.show()
        self.cancel.show()
        self.worker = Worker(task, self)
        self.worker.result.connect(callback)
        self.worker.error.connect(self.job_error)
        self.worker.progress.connect(lambda _, message: self.status.setText(message))
        self.worker.finished.connect(self.job_finished)
        self.worker.start()

    def job_error(self, message):
        if self.error_callback:
            self.error_callback(message)
        self.status.setText(message)
        if not self.closing:
            self.notify(message)

    def job_finished(self):
        self.worker.deleteLater()
        self.worker, self.error_callback = None, None
        self.body.setEnabled(True)
        self.progress.hide()
        self.cancel.hide()
        if self.closing:
            self.close()
        else:
            self.status.setText("Pronto · processamento local")

    def cancel_job(self):
        if self.worker:
            self.worker.cancelled.set()
            self.status.setText("Cancelando a operação com segurança…")

    def make_history(self):
        page = QWidget()
        box = QVBoxLayout(page)
        box.addWidget(text_label("Histórico técnico", "title"))
        box.addWidget(text_label("Diagnóstico das conversões anteriores. Os trabalhos nomeados ficam em Importações.", "subtitle"))
        self.history_grid = table()
        box.addWidget(self.history_grid, 1)
        return page

    def refresh_history(self):
        rows = []
        for created, layout, stats, outcome in self.store.history():
            data = json.loads(stats)
            rows.append([created, layout, data["read"], data["valid"], data["warnings"], data["errors"], outcome])
        self.history_grid.setModel(GridModel(["Data", "Layout", "Lidos", "Válidos", "Avisos", "Erros", "Resultado"], rows, parent=self.history_grid))
        self.history_grid.resizeColumnsToContents()

    def closeEvent(self, event):
        if self.worker is not None:
            self.closing = True
            self.cancel_job()
            event.ignore()
            return
        self.detail.close_sessions()
        event.accept()
