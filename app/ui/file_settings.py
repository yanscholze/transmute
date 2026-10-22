"""Classificação de arquivo e visualizador PDF local, sem abrir navegador externo."""
from pathlib import Path

from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QHBoxLayout, QLineEdit, QVBoxLayout

from app.storage.imports import FAMILIES
from app.ui.common import button, text_label


class FileSettings(QDialog):
    def __init__(self, item, layouts, parent=None):
        super().__init__(parent)
        self.item, self.layouts = dict(item), layouts
        self.setWindowTitle("Dados do arquivo")
        self.resize(720, 390)
        box = QVBoxLayout(self)
        form = QFormLayout()
        self.path = QLineEdit(item.get("path", ""))
        self.path.setReadOnly(True)
        line = QHBoxLayout()
        line.addWidget(self.path, 1)
        line.addWidget(button("Selecionar…", self.browse))
        form.addRow("Arquivo recebido", line)
        self.title = QLineEdit(item.get("title", ""))
        form.addRow("Título", self.title)
        self.family = QComboBox()
        for key, label in FAMILIES.items():
            self.family.addItem(label, key)
        self.family.setCurrentIndex(max(0, self.family.findData(item.get("family"))))
        form.addRow("Categoria", self.family)
        self.model = QComboBox()
        form.addRow("Modelo de saída", self.model)
        self.role = QComboBox()
        self.role.addItem("Fonte de dados — gerar registros", "source")
        self.role.addItem("Documento de apoio — não converter", "reference")
        self.role.setCurrentIndex(max(0, self.role.findData(item.get("role", "source"))))
        form.addRow("Finalidade", self.role)
        self.group = QLineEdit(item.get("group", "principal"))
        form.addRow("Grupo de vínculo (OS/vendas)", self.group)
        box.addLayout(form)
        self.feedback = text_label("Cabeçalhos e itens do mesmo lote devem ter o mesmo grupo. Documentos de apoio não geram registros.", "notice")
        box.addWidget(self.feedback)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        box.addWidget(buttons)
        self.family.currentIndexChanged.connect(self.populate)
        self.populate()

    def populate(self):
        self.model.clear()
        for layout in self.layouts:
            if layout.family == self.family.currentData():
                self.model.addItem(layout.label, layout)
                if str(layout.path) == self.item.get("layout_path") and layout.sheet == self.item.get("layout_sheet"):
                    self.model.setCurrentIndex(self.model.count() - 1)

    def browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Arquivo recebido", "", "Bases e PDFs (*.xlsx *.xls *.csv *.tsv *.pdf)")
        if path:
            self.path.setText(path)
            if not self.title.text():
                self.title.setText(Path(path).stem)

    def save(self):
        model = self.model.currentData()
        if not Path(self.path.text()).is_file() or not self.title.text().strip() or (not model and self.role.currentData() != "reference"):
            self.feedback.setText("Selecione um arquivo existente, informe o título e confira o modelo de destino.")
            return
        changed_source = self.path.text() != self.item.get("path") or self.family.currentData() != self.item.get("family") or (model and (str(model.path) != self.item.get("layout_path") or model.sheet != self.item.get("layout_sheet")))
        if changed_source:
            for key in ["mapping", "source_sheet", "header_row", "encoding", "delimiter", "corrections", "options", "stats", "source_headers", "source_sha256"]:
                self.item.pop(key, None)
        self.item.update(path=self.path.text(), title=self.title.text().strip(), family=self.family.currentData(),
                         layout_path=str(model.path) if model else "", layout_sheet=model.sheet if model else "",
                         role=self.role.currentData(), group=self.group.text().strip() or "principal", status="Aguardando reprocessamento", message="")
        self.accept()


def open_pdf(path, parent=None):
    from PySide6.QtCore import QFile, QIODevice
    from PySide6.QtPdf import QPdfDocument
    from PySide6.QtPdfWidgets import QPdfView
    dialog = QDialog(parent)
    dialog.setWindowTitle("Conferir PDF original · " + Path(path).name)
    dialog.resize(1000, 800)
    layout = QVBoxLayout(dialog)
    document = QPdfDocument(dialog)
    device = QFile(str(path))
    opened = device.open(QIODevice.OpenModeFlag.ReadOnly)
    if opened:
        document.load(device)
    if not opened or document.error() != QPdfDocument.Error.None_:
        layout.addWidget(text_label("Não foi possível abrir o PDF original. Confira se o arquivo existe ou exige senha."))
    else:
        view = QPdfView(dialog)
        view.setDocument(document)
        view.setPageMode(QPdfView.PageMode.MultiPage)
        view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        layout.addWidget(view)
    try:
        dialog.exec()
    finally:
        # Closing the preview must immediately release Windows file locks.
        document.close()
        device.close()
        dialog.deleteLater()
