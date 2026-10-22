"""Tarefas em thread e tabelas de apresentação sem regras de negócio.

Erro é mostrado ao operador, mas o log contém só o tipo da exceção. O modelo
de tabela recebe apenas a página atual, sem duplicar uma base inteira.
"""
import logging
from threading import Event

from PySide6.QtCore import QAbstractTableModel, Qt, QThread, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QAbstractItemView, QLabel, QPushButton, QTableView

from app.models import Cancelled, Control


class Worker(QThread):
    result = Signal(object)
    error = Signal(str)
    progress = Signal(int, str)

    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task
        self.cancelled = Event()

    def run(self):
        try:
            self.result.emit(self.task(Control(self.cancelled.is_set, self.progress.emit)))
        except Cancelled as error:
            self.error.emit(str(error))
        except Exception as error:
            # Never log exception text: it may contain a path, key or cell data.
            logging.getLogger("conversor").warning("operation_failed type=%s", type(error).__name__)
            self.error.emit(str(error))


class GridModel(QAbstractTableModel):
    def __init__(self, headers=None, rows=None, statuses=None, parent=None):
        super().__init__(parent)
        self.headers = headers or []
        self.rows = rows or []
        self.statuses = statuses or []

    def rowCount(self, parent=None):
        return len(self.rows)

    def columnCount(self, parent=None):
        return len(self.headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role in {Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole}:
            return str(self.rows[index.row()][index.column()])
        if role == Qt.ItemDataRole.ForegroundRole and index.column() == 1 and self.statuses:
            return QColor({"ERRO": "#B42318", "AVISO": "#8A4B06", "OK": "#09695D"}.get(self.statuses[index.row()], "#243342"))
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            return self.headers[section] if orientation == Qt.Orientation.Horizontal else str(section + 1)


def table(parent=None):
    view = QTableView(parent)
    view.setAlternatingRowColors(True)
    view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    view.setWordWrap(False)
    view.verticalHeader().setDefaultSectionSize(34)
    view.verticalHeader().hide()
    view.horizontalHeader().setStretchLastSection(True)
    return view


def button(label, callback, primary=False):
    widget = QPushButton(label)
    widget.setAccessibleName(label)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    if primary:
        widget.setObjectName("primary")
    widget.clicked.connect(callback)
    return widget


def text_label(text, name=""):
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setWordWrap(True)
    if name:
        label.setObjectName(name)
    return label
