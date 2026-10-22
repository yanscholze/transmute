"""Shell Soft UI: dashboard, sidebar recolhível e páginas operacionais.

O worker único mantém cancelamento acessível. Aparência nunca reinicia uma
importação; mudanças da biblioteca exigem nova validação do trabalho.
"""
import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QMainWindow, QProgressBar, QStackedWidget, QVBoxLayout, QWidget

from app.core.catalog import discover, workspace_config
from app.storage.imports import ImportStore
from app.storage.workspace import initialize, save_config
from app.ui.common import GridModel, Worker, button, table, text_label
from app.ui.icons import icon
from app.ui.navigation import DESTINATIONS, NavigationRail
from app.ui.surfaces import ElidedLabel, SoftPanel
from app.ui.theme import Backdrop, native_palette, palette, stylesheet


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
        shell.setObjectName("shell")
        shell_box = QVBoxLayout(shell)
        shell_box.setContentsMargins(20, 20, 20, 8)
        shell_box.setSpacing(18)
        self.body = QWidget()
        body_box = QVBoxLayout(self.body)
        body_box.setContentsMargins(0, 0, 0, 0)
        body_box.setSpacing(24)
        body_box.addWidget(self.make_header())
        work = QHBoxLayout()
        work.setSpacing(20)
        self.sidebar = NavigationRail(bool(store.setting("ui_sidebar_expanded", False)))
        self.sidebar.selected.connect(self.navigate)
        self.sidebar.expanded_changed.connect(lambda value: store.set_setting("ui_sidebar_expanded", value))
        self.sidebar.exit_requested.connect(self.close)
        self.nav_buttons = self.sidebar.buttons
        work.addWidget(self.sidebar)
        self.pages = QStackedWidget()
        from app.ui.dashboard import Dashboard
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
        self.detail.changed.connect(self.refresh_overview)
        self.detail.back_requested.connect(lambda: self.navigate(1))
        self.dashboard = Dashboard(self.root, self.import_store, store, self.navigate, self.new_import,
                                   self.open_import, self.edit_rules_from_dashboard, self.notify)
        for page in [self.dashboard, self.home, self.library, self.appearance, self.settings, self.history_page, self.detail]:
            self.pages.addWidget(page)
        self.panel = Backdrop()
        self.panel_box = QVBoxLayout(self.panel)
        self.panel_box.setContentsMargins(0, 0, 0, 0)
        self.panel_box.addWidget(self.pages)
        work.addWidget(self.panel, 1)
        body_box.addLayout(work, 1)
        shell_box.addWidget(self.body, 1)
        statusbar = QWidget()
        status_layout = QHBoxLayout(statusbar)
        status_layout.setContentsMargins(8, 0, 8, 0)
        self.status = text_label("Pronto · processamento local · originais preservados", "smallText")
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

    def make_header(self):
        header = QWidget()
        box = QHBoxLayout(header)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(20)
        brand = SoftPanel(pill=True)
        brand.setFixedWidth(218)
        line = QHBoxLayout(brand)
        line.setContentsMargins(9, 8, 17, 8)
        line.setSpacing(12)
        self.avatar = text_label("C", "brandAvatar")
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar.setFixedSize(46, 46)
        self.brand_label = ElidedLabel("Conversor de Bases")
        self.brand_label.setObjectName("brand")
        line.addWidget(self.avatar)
        line.addWidget(self.brand_label, 1)
        box.addWidget(brand)
        context = SoftPanel(pill=True)
        row = QHBoxLayout(context)
        row.setContentsMargins(25, 10, 20, 10)
        title = QVBoxLayout()
        title.setSpacing(1)
        self.header_title = ElidedLabel("Dashboard")
        self.header_title.setObjectName("headerTitle")
        title.addWidget(self.header_title)
        title.addWidget(text_label("Seu espaço de trabalho", "eyebrow"))
        row.addLayout(title, 1)
        self.search = QLineEdit()
        self.search.setObjectName("globalSearch")
        self.search.setPlaceholderText("Buscar importações…")
        self.search.setAccessibleName("Buscar importações pelo nome; Enter para abrir os resultados")
        self.search.setMaximumWidth(260)
        self.search.returnPressed.connect(self.search_imports)
        row.addWidget(self.search, 1)
        box.addWidget(context, 1)
        local = SoftPanel(pill=True)
        right = QHBoxLayout(local)
        right.setContentsMargins(16, 8, 10, 8)
        right.setSpacing(10)
        self.local_label = text_label("Processamento\nlocal", "localBadge")
        right.addWidget(self.local_label)
        self.theme_button = button("", self.toggle_theme)
        self.theme_button.setObjectName("iconButton")
        self.theme_button.setFixedSize(40, 40)
        right.addWidget(self.theme_button)
        box.addWidget(local)
        return header

    def search_imports(self):
        self.home.filter.setCurrentIndex(0)
        self.home.search.setText(self.search.text().strip())
        self.navigate(1)

    def toggle_theme(self):
        config = workspace_config(self.root)
        config["theme_mode"] = "light" if config.get("theme_mode", "light") == "dark" else "dark"
        save_config(self.root, config)
        self.appearance.mode.setCurrentIndex(self.appearance.mode.findData(config["theme_mode"]))
        self.apply_brand()

    def edit_rules_from_dashboard(self):
        self.navigate(2)
        self.library.edit_rules()

    def refresh_overview(self):
        self.home.refresh()
        self.dashboard.refresh(self.layouts)

    def notify(self, message):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, self.windowTitle() or "Conversor de Bases", message)

    def navigate(self, index):
        if self.pages.currentWidget() is self.detail:
            self.detail.leave_editor()
        self.sidebar.set_current(index)
        if index == 0:
            self.dashboard.refresh(self.layouts)
        elif index == 1:
            self.home.refresh()
        elif index == 4:
            self.settings.refresh_profiles()
        elif index == 5:
            self.refresh_history()
        self.pages.setCurrentIndex(index)
        self.header_title.setText(DESTINATIONS[index][0])
        self.configure_backdrop()

    def configure_backdrop(self):
        config = workspace_config(self.root)
        dashboard = self.pages.currentWidget() is self.dashboard
        if self.pages.currentWidget() is self.appearance:
            config = {**config, "logo_path": ""}
        self.panel.configure({**config, "panel_surface": not dashboard})
        self.panel_box.setContentsMargins(*((0, 0, 0, 0) if dashboard else (20, 17, 24, 22)))

    def new_import(self):
        if self.pages.currentWidget() is self.detail:
            self.detail.leave_editor()
        from app.ui.import_wizard import ImportWizard
        if self.wizard is None:
            self.wizard = ImportWizard(self.import_store, self.layouts, self.notify)
            self.wizard.created.connect(self.import_created)
            self.wizard.cancelled.connect(self.cancel_wizard)
            self.pages.addWidget(self.wizard)
        self.sidebar.set_current(1)
        self.pages.setCurrentWidget(self.wizard)
        self.header_title.setText("Nova importação")
        self.configure_backdrop()

    def cancel_wizard(self):
        if self.wizard:
            self.pages.removeWidget(self.wizard)
            self.wizard.deleteLater()
            self.wizard = None
        self.navigate(1)

    def import_created(self, job):
        self.cancel_wizard()
        self.open_import(job["id"])
        self.detail.process_all()

    def open_import(self, identifier):
        self.detail.leave_editor()
        self.detail.set_job(self.import_store.get(identifier))
        self.sidebar.set_current(1)
        self.pages.setCurrentWidget(self.detail)
        self.header_title.setText(self.detail.job["name"])
        self.configure_backdrop()

    def apply_brand(self):
        config = workspace_config(self.root)
        self.setWindowTitle(config.get("brand", "Conversor de Bases"))
        brand = config.get("brand", "Conversor de Bases")
        self.brand_label.setText(brand)
        self.avatar.setText(brand[:1].upper())
        color, mode = config.get("primary_color", "#09695D"), config.get("theme_mode", "light")
        self.setStyleSheet(stylesheet(color, mode))
        self.setPalette(native_palette(color, mode))
        self.sidebar.apply_theme(color, mode)
        for panel in self.findChildren(SoftPanel):
            panel.apply_theme(mode)
        t = palette(color, mode)
        self.theme_button.setIcon(icon("appearance", t["ink"], 21))
        label = "Mudar para tema claro" if mode == "dark" else "Mudar para tema escuro"
        self.theme_button.setAccessibleName(label)
        self.theme_button.setToolTip(label)
        if self.search.actions():
            self.search.actions()[0].setIcon(icon("search", t["muted"], 18))
        else:
            self.search.addAction(icon("search", t["muted"], 18), QLineEdit.ActionPosition.LeadingPosition)
        self.configure_backdrop()
        self.dashboard.refresh(self.layouts)

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
        self.refresh_overview()

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
