"""Pick individual source tables from a directory; failures remain visible."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QHBoxLayout, QTableWidget, QTableWidgetItem, QVBoxLayout

from app.ui.common import button, text_label


class SourcePicker(QDialog):
    def __init__(self, entries, parent=None):
        super().__init__(parent)
        self.entries, self.selected = entries, []
        self.setWindowTitle("Escolher tabelas da pasta")
        self.resize(960, 620)
        box = QVBoxLayout(self)
        box.addWidget(text_label("Marque somente as abas e tabelas recebidas que pertencem a este projeto.", "subtitle"))
        actions = QHBoxLayout()
        actions.addWidget(button("Marcar todas", lambda: self.mark(True)))
        actions.addWidget(button("Desmarcar todas", lambda: self.mark(False)))
        actions.addStretch()
        box.addLayout(actions)
        self.grid = QTableWidget(len(entries), 3)
        self.grid.setHorizontalHeaderLabels(["Selecionar / arquivo", "Aba ou tabela", "Situação"])
        for row, entry in enumerate(entries):
            from pathlib import Path
            item = QTableWidgetItem(Path(entry["path"]).name)
            item.setToolTip(entry["path"])
            item.setFlags(Qt.ItemFlag.ItemIsEnabled | (Qt.ItemFlag.ItemIsUserCheckable if not entry["error"] else Qt.ItemFlag.NoItemFlags))
            item.setCheckState(Qt.CheckState.Unchecked)
            self.grid.setItem(row, 0, item)
            for col, value in [(1, entry["source_sheet"]), (2, entry["error"] or "Disponível")]:
                cell = QTableWidgetItem(value)
                cell.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.grid.setItem(row, col, cell)
        self.grid.setColumnWidth(0, 300)
        self.grid.setColumnWidth(1, 230)
        self.grid.horizontalHeader().setStretchLastSection(True)
        box.addWidget(self.grid, 1)
        self.feedback = text_label("Nenhum arquivo será movido ou enviado à internet.", "muted")
        box.addWidget(self.feedback)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Adicionar tabelas selecionadas")
        buttons.accepted.connect(self.accept_selection)
        buttons.rejected.connect(self.reject)
        box.addWidget(buttons)

    def mark(self, checked):
        for row, entry in enumerate(self.entries):
            if not entry["error"]:
                self.grid.item(row, 0).setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)

    def accept_selection(self):
        self.selected = [entry for row, entry in enumerate(self.entries) if not entry["error"] and self.grid.item(row, 0).checkState() == Qt.CheckState.Checked]
        if not self.selected:
            self.feedback.setText("Marque pelo menos uma tabela para continuar.")
            return
        self.accept()
