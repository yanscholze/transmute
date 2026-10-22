"""Início centrado em trabalhos nomeados; configurações ficam em outras telas."""
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLineEdit, QStackedWidget, QVBoxLayout, QWidget

from app.storage.imports import FAMILIES
from app.ui.common import GridModel, button, table, text_label


class ImportsHome(QWidget):
    def __init__(self, imports, start, open_import):
        super().__init__()
        self.imports, self.open_import = imports, open_import
        body = QVBoxLayout(self)
        body.setSpacing(20)
        top = QHBoxLayout()
        top.addWidget(text_label("Importações", "title"), 1)
        top.addWidget(button("Nova importação", start, True))
        body.addLayout(top)
        body.addWidget(text_label("Organize os arquivos recebidos por cliente ou trabalho e acompanhe cada importação.", "subtitle"))
        toolbar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar pelo nome da importação")
        self.search.setAccessibleName("Buscar importações")
        self.filter = QComboBox()
        self.filter.addItems(["Todas as importações", "Com pendências", "Prontas", "Exportadas"])
        toolbar.addWidget(self.search, 1)
        toolbar.addWidget(self.filter)
        toolbar.addWidget(button("Abrir importação", self.open_selected))
        body.addLayout(toolbar)
        self.content = QStackedWidget()
        empty = QWidget()
        empty_body = QVBoxLayout(empty)
        empty_body.addSpacing(64)
        empty_body.addWidget(text_label("Tudo começa com uma nova importação", "section"))
        empty_body.addWidget(text_label("Dê um nome ao trabalho, escolha as tabelas e adicione as planilhas ou PDFs recebidos.", "muted"))
        empty_body.addWidget(button("Iniciar nova importação", start, True))
        empty_body.addStretch()
        self.grid = table()
        self.grid.setObjectName("importsGrid")
        self.grid.setAccessibleName("Lista de importações por nome, categorias e andamento")
        self.grid.doubleClicked.connect(self.open_selected)
        self.content.addWidget(empty)
        self.content.addWidget(self.grid)
        body.addWidget(self.content, 1)
        self.count = text_label("", "muted")
        body.addWidget(self.count)
        self.search.textChanged.connect(self.refresh)
        self.filter.currentIndexChanged.connect(self.refresh)
        self.refresh()

    def refresh(self, *args):
        jobs = self.imports.list()
        query = self.search.text().casefold()
        mode = self.filter.currentIndex()
        self.visible = [j for j in jobs if query in j["name"].casefold() and
                        (mode == 0 or mode == 1 and j["status"] in {"Revisar pendências", "Interrompida"} or
                         mode == 2 and j["status"] == "Pronta para exportar" or mode == 3 and j["status"] == "Exportada")]
        rows = [[j["name"], j["status"], ", ".join(FAMILIES[c] for c in j["categories"]), len(j["attachments"]),
                 j["updated"][:16].replace("T", " ")] for j in self.visible]
        self.grid.setModel(GridModel(["Importação", "Andamento", "Tabelas", "Arquivos", "Atualizada em"], rows, parent=self.grid))
        for col, width in enumerate([290, 210, 270, 80, 150]):
            self.grid.setColumnWidth(col, width)
        self.content.setCurrentIndex(1 if jobs else 0)
        self.count.setText(f"{len(self.visible)} de {len(jobs)} importações · arquivos originais permanecem nos locais escolhidos")

    def open_selected(self, *args):
        row = self.grid.currentIndex().row()
        if 0 <= row < len(self.visible):
            self.open_import(self.visible[row]["id"])
