"""Escolha/drag and drop, opções de leitura e amostra local limitada.

Alterar leitura invalida a estrutura anterior; nada é processado com uma
prévia que corresponda a outro arquivo, aba ou encoding.
"""
from itertools import islice
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QFileDialog, QFormLayout, QHBoxLayout, QLineEdit, QSpinBox, QVBoxLayout, QWidget

from app.core.importers.reader import inspect, records, sheets
from app.ui.common import GridModel, button, table, text_label


class InputPane(QWidget):
    changed = Signal()

    def __init__(self, layouts, run_job, parent=None):
        super().__init__(parent)
        self.layouts, self.run_job, self.source = layouts, run_job, None
        self.setAcceptDrops(True)
        body = QVBoxLayout(self)
        body.setSpacing(16)
        self.drop = text_label("Arraste uma planilha aqui ou selecione um arquivo\nXLSX, XLS e CSV · o original será preservado", "drop")
        self.drop.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop.setMinimumHeight(92)
        body.addWidget(self.drop)
        pathbar = QHBoxLayout()
        self.path = QLineEdit()
        self.path.setPlaceholderText("Caminho do arquivo recebido")
        self.path.setAccessibleName("Arquivo de origem")
        pathbar.addWidget(self.path, 1)
        pathbar.addWidget(button("Selecionar arquivo", self.browse))
        body.addLayout(pathbar)
        form = QFormLayout()
        self.layout_box = QComboBox()
        for layout in layouts:
            self.layout_box.addItem(layout.label, layout)
        form.addRow("Modelo de destino", self.layout_box)
        line = QHBoxLayout()
        self.sheet = QComboBox()
        self.sheet.setMinimumWidth(180)
        self.sheet.setAccessibleName("Aba de origem")
        self.header = QSpinBox()
        self.header.setRange(0, 10000)
        self.header.setSpecialValueText("Detectar cabeçalho")
        self.header.setAccessibleName("Linha do cabeçalho; zero detecta automaticamente")
        line.addWidget(self.sheet, 2)
        line.addWidget(self.header, 1)
        form.addRow("Aba / linha do cabeçalho", line)
        csvline = QHBoxLayout()
        self.encoding = QComboBox()
        self.encoding.setEditable(True)
        self.encoding.addItems(["Automático", "utf-8-sig", "cp1252", "utf-16", "latin-1"])
        self.encoding.setAccessibleName("Encoding CSV")
        self.delimiter = QComboBox()
        for label, value in [("Detectar delimitador", ""), ("Ponto e vírgula", ";"), ("Vírgula", ","), ("Tabulação", "\t"), ("Barra vertical", "|")]:
            self.delimiter.addItem(label, value)
        self.delimiter.setAccessibleName("Delimitador CSV")
        csvline.addWidget(self.encoding)
        csvline.addWidget(self.delimiter)
        csvline.addWidget(button("Ler / atualizar prévia", self.load, True))
        form.addRow("Leitura de CSV", csvline)
        body.addLayout(form)
        self.notice = text_label("Escolha o modelo correspondente à base e confira a aba e o cabeçalho sugeridos.", "muted")
        body.addWidget(self.notice)
        self.preview = table()
        self.preview.setAccessibleName("Prévia original: até vinte linhas")
        body.addWidget(self.preview, 1)
        self.path.textEdited.connect(self.invalidate)
        self.layout_box.currentIndexChanged.connect(self.changed)
        self.sheet.currentIndexChanged.connect(self.invalidate)
        self.header.valueChanged.connect(self.invalidate)
        self.encoding.currentTextChanged.connect(self.invalidate)
        self.delimiter.currentIndexChanged.connect(self.invalidate)

    @property
    def layout(self):
        return self.layout_box.currentData()

    def invalidate(self, *args):
        self.source = None
        self.changed.emit()

    def browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Selecionar base", "", "Bases (*.xlsx *.xls *.csv *.tsv);;Todos os arquivos (*)")
        if path:
            self.set_path(path)

    def set_path(self, path):
        self.path.setText(str(path))
        self.sheet.blockSignals(True)
        self.sheet.clear()
        self.sheet.blockSignals(False)
        self.header.setValue(0)
        self.invalidate()
        self.load()

    def load(self):
        path = Path(self.path.text()).expanduser()
        sheet, header = self.sheet.currentText(), self.header.value() or None
        enc = self.encoding.currentText()
        enc = "" if enc == "Automático" else enc
        delim = self.delimiter.currentData()
        def task(control):
            available = sheets(path)
            source = inspect(path, sheet or None, header, enc, delim, control)
            sample = list(islice(records(source, control), 20))
            return source, available, sample
        self.run_job(task, self.loaded, "Lendo estrutura e prévia…")

    def loaded(self, result):
        source, available, sample = result
        self.sheet.blockSignals(True)
        self.sheet.clear()
        self.sheet.addItems(available)
        self.sheet.setCurrentText(source.sheet)
        self.sheet.blockSignals(False)
        self.header.blockSignals(True)
        self.header.setValue(source.header_row)
        self.header.blockSignals(False)
        self.source = source
        rows = [[n] + [raw.get(sid).text if raw and raw.get(sid) else "" for sid in source.ids] for n, raw, _ in sample if raw]
        model = GridModel(["Linha"] + source.headers, rows, parent=self.preview)
        self.preview.setModel(model)
        self.preview.resizeColumnsToContents()
        self.notice.setText(f"{source.format.upper()} · {len(source.headers)} colunas · cabeçalho na linha {source.header_row}\n" + "\n".join(source.warnings))
        self.changed.emit()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            self.set_path(urls[0].toLocalFile())
            event.acceptProposedAction()
