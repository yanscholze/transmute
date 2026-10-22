"""Revisão paginada: correção vira pendência até novo processamento determinístico."""
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QInputDialog, QLineEdit, QSplitter, QTextEdit, QVBoxLayout, QWidget

from app.core.mapping import targets
from app.ui.common import GridModel, button, table, text_label


class ReviewPane(QWidget):
    def __init__(self, on_correct, parent=None):
        super().__init__(parent)
        self.sessions, self.page, self.on_correct = [], 0, on_correct
        box = QVBoxLayout(self)
        self.stats = text_label("", "stats")
        box.addWidget(self.stats)
        bar = QHBoxLayout()
        self.dataset = QComboBox()
        self.dataset.setAccessibleName("Base em revisão")
        self.severity = QComboBox()
        for label, value in [("Todos os registros", ""), ("Somente erros", "ERRO"), ("Somente avisos", "AVISO"), ("Válidos sem avisos", "OK")]:
            self.severity.addItem(label, value)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Pesquisar valor ou linha")
        self.search.setAccessibleName("Pesquisar registros convertidos")
        bar.addWidget(self.dataset)
        bar.addWidget(self.severity)
        bar.addWidget(self.search, 1)
        bar.addWidget(button("Corrigir campo…", self.correct))
        box.addLayout(bar)
        self.grid = table()
        self.grid.setAccessibleName("Prévia dos dados convertidos")
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.setAccessibleName("Comparação original e transformado e validações da linha")
        split = QSplitter()
        split.setOrientation(Qt.Orientation.Vertical)
        split.addWidget(self.grid)
        split.addWidget(self.details)
        split.setSizes([400, 180])
        box.addWidget(split, 1)
        foot = QHBoxLayout()
        foot.addWidget(button("Página anterior", lambda: self.turn(-1)))
        self.page_label = text_label("")
        foot.addWidget(self.page_label, 1)
        foot.addWidget(button("Próxima página", lambda: self.turn(1)))
        box.addLayout(foot)
        self.dataset.currentIndexChanged.connect(self.reset)
        self.severity.currentIndexChanged.connect(self.reset)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(220)
        self.search.textChanged.connect(lambda: self.timer.start())
        self.timer.timeout.connect(self.reset)
        self.grid.doubleClicked.connect(self.correct)

    def set_sessions(self, sessions, global_message=""):
        self.sessions = sessions
        self.global_message = global_message
        self.dataset.blockSignals(True)
        self.dataset.clear()
        self.dataset.addItems([s.layout.label for s in sessions])
        self.dataset.blockSignals(False)
        self.reset()

    def reset(self):
        self.page = 0
        self.refresh()

    def turn(self, amount):
        if amount > 0 and len(self.current) < 200:
            return
        self.page = max(0, self.page + amount)
        self.refresh()

    def refresh(self):
        if not self.sessions:
            return
        session = self.sessions[max(0, self.dataset.currentIndex())]
        stats = session.stats()
        self.stats.setText(f"{stats['read']:,} registros   ·   {stats['valid']:,} válidos   ·   {stats['warnings']:,} com avisos   ·   {stats['errors']:,} com erros".replace(",", "."))
        self.current = list(session.rows(self.severity.currentData(), self.search.text(), self.page * 200, 200))
        self.headers = targets(session.layout)
        rows = [[r["line"], r["severity"]] + [r["values"].get(h, "") for h in self.headers] for r in self.current]
        self.grid.setModel(GridModel(["Linha original", "Status"] + self.headers, rows, [r["severity"] for r in self.current], self.grid))
        self.grid.setColumnWidth(0, 130)
        self.grid.setColumnWidth(1, 100)
        for col in range(2, len(self.headers) + 2):
            self.grid.setColumnWidth(col, 180)
        self.grid.selectionModel().selectionChanged.connect(self.show_details)
        self.page_label.setText(f"Página {self.page + 1} · até 200 registros por página · selecione uma linha para comparar")
        self.details.setPlainText(self.global_message)

    def show_details(self, *args):
        index = self.grid.currentIndex().row()
        if index < 0 or index >= len(self.current):
            return
        row = self.current[index]
        session = self.sessions[self.dataset.currentIndex()]
        lines = [f"Linha original {row['line']} — {row['severity']}", ""]
        lines += [f"{p['severity']} · {p['field']} · {p['message']}" for p in row["issues"]]
        lines += ["", "ORIGINAL → TRANSFORMADO"]
        for field in self.headers:
            sid = next((d.source for d in session.decisions if d.target == field), "")
            original = row["raw"].get(sid, {}).get("text", "")
            transformed = row["values"].get(field, "")
            if original or transformed:
                rules = [c["rule"] for c in row["changes"] if c["field"] == field]
                lines.append(f"{field}: {original or '(vazio)'} → {transformed or '(vazio)'} | {', '.join(rules) or 'preservado'}")
        self.details.setPlainText("\n".join(lines))

    def correct(self, *args):
        index = self.grid.currentIndex().row()
        if index < 0 or index >= len(self.current):
            return
        row = self.current[index]
        col = self.grid.currentIndex().column() - 2
        field, ok = QInputDialog.getItem(self, "Corrigir campo", "Campo de destino", self.headers, max(0, col), False)
        if not ok:
            return
        value, ok = QInputDialog.getText(self, f"Linha {row['line']} · {field}", "Valor revisado (original permanece intacto)", text=row["values"].get(field, ""))
        if ok:
            self.on_correct(self.dataset.currentIndex(), row["line"], field, value)
