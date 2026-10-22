"""Shell desktop: navegação, biblioteca ativa e execução/cancelamento de tarefas.

Fechamento aguarda o worker terminar antes de remover sessões. Mudanças de
biblioteca recriam o assistente para não reaproveitar decisões de outra base.
"""
import json

from PySide6.QtWidgets import QButtonGroup, QFrame, QHBoxLayout, QMainWindow, QProgressBar, QStackedWidget, QVBoxLayout, QWidget

from app.core.catalog import discover, workspace_config
from app.storage.workspace import initialize
from app.ui.common import GridModel, Worker, button, table, text_label
from app.ui.conversion import ConversionPane


class Window(QMainWindow):
    def __init__(self, root, state, store):
        super().__init__()
        root = initialize(root, state)
        self.root, self.state, self.store = root, state, store
        self.worker, self.closing = None, False
        try:
            self.layouts = discover(root)
        except Exception:
            # Keep the library screen available so a broken model folder is recoverable.
            self.layouts = []
        self.setWindowTitle("Conversor de Bases")
        self.resize(1380, 900)
        self.setMinimumSize(1080, 740)
        shell = QWidget()
        shell_box = QVBoxLayout(shell)
        shell_box.setContentsMargins(0, 0, 0, 0)
        self.body = QWidget()
        body_box = QHBoxLayout(self.body)
        body_box.setContentsMargins(0, 0, 0, 0)
        body_box.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(218)
        nav = QVBoxLayout(sidebar)
        nav.setContentsMargins(20, 24, 20, 24)
        nav.setSpacing(10)
        self.brand_label = text_label("Conversor\nde Bases", "brand")
        nav.addWidget(self.brand_label)
        nav.addWidget(text_label("MIGRAÇÃO PARA ERP"))
        nav.addSpacing(30)
        self.pages = QStackedWidget()
        from app.ui.library import LibraryPane
        self.library = LibraryPane(root, self.notify, lambda: self.navigate(1))
        self.library.changed.connect(self.reload_library)
        self.convert = ConversionPane(root, state, self.layouts, store, self.run_job, self.notify)
        self.history_page = self.make_history()
        self.models_page = self.make_models()
        from app.ui.settings import SettingsPane
        self.settings = SettingsPane(store, state, self.run_job, self.notify)
        for page in [self.library, self.convert, self.history_page, self.models_page, self.settings]:
            self.pages.addWidget(page)
        group = QButtonGroup(self)
        group.setExclusive(True)
        self.nav_buttons = []
        for i, label in enumerate(["Início", "Nova conversão", "Histórico", "Modelos", "Configurações"]):
            item = button(label, lambda checked=False, idx=i: self.navigate(idx))
            item.setCheckable(True)
            group.addButton(item)
            nav.addWidget(item)
            self.nav_buttons.append(item)
        self.nav_buttons[0].setChecked(True)
        nav.addStretch()
        nav.addWidget(text_label("PROCESSAMENTO LOCAL\n\nOriginais preservados\nIA somente com consentimento\n\nVersão 1.0.0"))
        body_box.addWidget(sidebar)
        panel = QWidget()
        panel_box = QVBoxLayout(panel)
        panel_box.setContentsMargins(28, 24, 28, 20)
        panel_box.addWidget(self.pages)
        body_box.addWidget(panel, 1)
        shell_box.addWidget(self.body, 1)
        statusbar = QWidget()
        status_layout = QHBoxLayout(statusbar)
        status_layout.setContentsMargins(18, 8, 18, 8)
        self.status = text_label("Pronto · selecione ou arraste uma planilha", "muted")
        self.progress = QProgressBar()
        self.progress.setFixedWidth(240)
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
        QMessageBox.information(self, "Conversor de Bases", message)

    def navigate(self, index):
        self.nav_buttons[index].setChecked(True)
        if index == 2:
            self.refresh_history()
        if index == 4:
            self.settings.refresh_profiles()
        self.pages.setCurrentIndex(index)

    def apply_brand(self):
        from app.ui.style import STYLE
        config = workspace_config(self.root)
        self.setWindowTitle(config.get("brand", "Conversor de Bases"))
        self.brand_label.setText(config.get("brand", "Conversor de Bases"))
        self.setStyleSheet(STYLE.replace("#09695D", config.get("primary_color", "#09695D")))

    def reload_library(self):
        """Changing the active library resets the conversion, preserving all source files."""
        self.convert.close_sessions()
        old = self.convert
        self.pages.removeWidget(old)
        try:
            self.layouts = discover(self.root)
        except Exception as error:
            self.layouts = []
            self.notify(str(error))
        self.convert = ConversionPane(self.root, self.state, self.layouts, self.store, self.run_job, self.notify)
        self.pages.insertWidget(1, self.convert)
        old.deleteLater()
        old_models = self.models_page
        self.pages.removeWidget(old_models)
        self.models_page = self.make_models()
        self.pages.insertWidget(3, self.models_page)
        old_models.deleteLater()
        self.apply_brand()

    def run_job(self, task, callback, description):
        if self.worker is not None:
            return
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
        self.status.setText(message)
        if not self.closing:
            self.notify(message)

    def job_finished(self):
        self.worker.deleteLater()
        self.worker = None
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
            self.status.setText("Cancelando… a chamada externa, se iniciada, pode levar até o timeout configurado.")

    def make_history(self):
        page = QWidget()
        body = QVBoxLayout(page)
        body.addWidget(text_label("Histórico de conversões", "title"))
        body.addWidget(text_label("Somente datas, layouts, contagens e resultado. Registros e caminhos completos não ficam no histórico.", "muted"))
        self.history_grid = table()
        body.addWidget(self.history_grid, 1)
        body.addWidget(button("Limpar histórico local", self.clear_history))
        return page

    def refresh_history(self):
        rows = []
        for created, layout, stats, outcome in self.store.history():
            data = json.loads(stats)
            rows.append([created, layout, data["read"], data["valid"], data["warnings"], data["errors"], outcome])
        self.history_grid.setModel(GridModel(["Data", "Layout", "Lidos", "Válidos", "Avisos", "Erros", "Resultado"], rows, parent=self.history_grid))
        self.history_grid.resizeColumnsToContents()

    def clear_history(self):
        from PySide6.QtWidgets import QMessageBox
        if QMessageBox.question(self, "Limpar histórico", "Remover somente os metadados do histórico?", defaultButton=QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.store.clear_history()
            self.refresh_history()

    def make_models(self):
        page = QWidget()
        body = QVBoxLayout(page)
        body.addWidget(text_label("Modelos de importação", "title"))
        body.addWidget(text_label("Lidos diretamente das planilhas de referência. Exemplos preenchidos nunca são copiados para uma conversão.", "muted"))
        grid = table()
        rows = [[m.label, m.sheet, len(m.headers), m.digest[:16], " · ".join(m.headers)] for m in self.layouts]
        grid.setModel(GridModel(["Modelo", "Aba", "Colunas", "SHA-256", "Cabeçalhos, na ordem"], rows, parent=grid))
        grid.setColumnWidth(0, 290)
        grid.setColumnWidth(3, 180)
        body.addWidget(grid, 1)
        return page

    def closeEvent(self, event):
        if self.worker is not None:
            self.closing = True
            self.cancel_job()
            event.ignore()
            return
        self.convert.close_sessions()
        event.accept()
