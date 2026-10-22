"""Aparência isolada do fluxo de importação, com prévia local e logo copiada."""
import shutil
import uuid
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QImageReader
from PySide6.QtWidgets import QColorDialog, QComboBox, QFileDialog, QFormLayout, QHBoxLayout, QLineEdit, QSlider, QVBoxLayout, QWidget

from app.core.catalog import workspace_config
from app.storage.workspace import save_config, set_brand
from app.ui.common import button, text_label
from app.ui.theme import Backdrop


class AppearancePane(QWidget):
    changed = Signal()

    def __init__(self, root, notify):
        super().__init__()
        self.root, self.notify = root, notify
        config = workspace_config(root)
        self.logo_path = config.get("logo_path", "")
        body = QVBoxLayout(self)
        body.setSpacing(16)
        body.addWidget(text_label("Aparência", "title"))
        body.addWidget(text_label("Personalize o nome, a cor de toda a interface e a logo ao fundo.", "subtitle"))
        form = QFormLayout()
        self.brand = QLineEdit(config.get("brand", "Conversor de Bases"))
        form.addRow("Nome da aplicação", self.brand)
        colors = QHBoxLayout()
        self.color = QLineEdit(config.get("primary_color", "#09695D"))
        self.color.setMaximumWidth(150)
        colors.addWidget(self.color)
        colors.addWidget(button("Escolher cor…", self.choose_color))
        for name, value in [("Verde", "#09695D"), ("Azul", "#305AA1"), ("Roxo", "#7450A5"), ("Grafite", "#38434E")]:
            colors.addWidget(button(name, lambda checked=False, v=value: self.color.setText(v)))
        colors.addStretch()
        form.addRow("Cor da interface", colors)
        logo = QHBoxLayout()
        logo.addWidget(button("Inserir logo…", self.choose_logo))
        logo.addWidget(button("Remover logo", self.remove_logo))
        self.logo_label = text_label(Path(self.logo_path).name or "Nenhuma logo selecionada", "muted")
        logo.addWidget(self.logo_label, 1)
        form.addRow("Imagem de fundo", logo)
        self.size = QSlider(Qt.Orientation.Horizontal)
        self.size.setRange(10, 100)
        self.size.setValue(config.get("logo_size", 50))
        self.size_label = text_label("")
        size_row = QHBoxLayout()
        size_row.addWidget(self.size, 1)
        size_row.addWidget(self.size_label)
        form.addRow("Tamanho na tela", size_row)
        self.opacity = QSlider(Qt.Orientation.Horizontal)
        self.opacity.setRange(0, 25)
        self.opacity.setValue(config.get("logo_opacity", 8))
        self.opacity_label = text_label("")
        opacity_row = QHBoxLayout()
        opacity_row.addWidget(self.opacity, 1)
        opacity_row.addWidget(self.opacity_label)
        form.addRow("Intensidade da logo", opacity_row)
        self.position = QComboBox()
        self.position.addItem("Centralizada", "center")
        self.position.addItem("Canto inferior direito", "bottom-right")
        self.position.setCurrentIndex(max(0, self.position.findData(config.get("logo_position", "center"))))
        form.addRow("Posição", self.position)
        body.addLayout(form)
        self.preview = Backdrop()
        self.preview.setMinimumHeight(220)
        preview_body = QVBoxLayout(self.preview)
        preview_body.addWidget(text_label("Prévia do plano de fundo", "section"))
        preview_body.addWidget(text_label("A logo mantém suas proporções. Use PNG transparente para um melhor resultado.", "muted"))
        preview_body.addStretch()
        body.addWidget(self.preview, 1)
        self.feedback = text_label("As mudanças só são aplicadas ao clicar em Salvar aparência.", "muted")
        body.addWidget(self.feedback)
        body.addWidget(button("Salvar aparência", self.save, True), alignment=Qt.AlignmentFlag.AlignRight)
        for widget in [self.size, self.opacity]:
            widget.valueChanged.connect(self.refresh)
        self.position.currentIndexChanged.connect(self.refresh)
        self.color.textChanged.connect(self.refresh)
        self.refresh()

    def draft(self):
        return {"brand": self.brand.text(), "primary_color": self.color.text(), "logo_path": self.logo_path,
                "logo_size": self.size.value(), "logo_opacity": self.opacity.value(), "logo_position": self.position.currentData()}

    def refresh(self, *args):
        self.size_label.setText(f"{self.size.value()}% da largura")
        self.opacity_label.setText(f"{self.opacity.value()}%")
        self.preview.configure(self.draft())
        self.logo_label.setText(Path(self.logo_path).name if self.logo_path else "Nenhuma logo selecionada")

    def choose_color(self):
        color = QColorDialog.getColor(QColor(self.color.text()), self, "Cor principal da interface")
        if color.isValid():
            self.color.setText(color.name())

    def choose_logo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Escolher logo", "", "Imagens (*.png *.jpg *.jpeg *.webp)")
        if path:
            self.load_logo(Path(path))

    def load_logo(self, path):
        reader = QImageReader(str(path))
        size = reader.size()
        if not reader.canRead() or size.width() <= 0 or size.width() * size.height() > 16_000_000 or path.stat().st_size > 10 * 1024 * 1024:
            self.notify("Use uma imagem PNG, JPG ou WebP de até 10 MB e 16 megapixels.")
            return
        folder = self.root / "assets"
        folder.mkdir(exist_ok=True)
        target = folder / ("logo_" + uuid.uuid4().hex[:10] + path.suffix.lower())
        shutil.copy2(path, target)
        self.logo_path = str(target)
        self.refresh()

    def remove_logo(self):
        self.logo_path = ""
        self.refresh()

    def save(self):
        try:
            set_brand(self.root, self.brand.text(), self.color.text())
            config = workspace_config(self.root)
            config.update(self.draft())
            save_config(self.root, config)
            self.changed.emit()
            self.feedback.setText("Aparência salva. Cor aplicada à navegação, superfícies, campos, tabelas e botões.")
        except ValueError as error:
            self.notify(str(error))
