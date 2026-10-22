"""Editor de correspondências e perfis, sem transformar células.

Decisões incertas precisam de confirmação; perfis só armazenam estrutura e
ficam restritos ao fingerprint do destino para evitar reaplicação absoluta.
"""
import hashlib
import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QInputDialog, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from app.core.mapping import suggest, targets
from app.models import Decision
from app.ui.common import button, text_label


def fingerprint(layout):
    return hashlib.sha256(json.dumps([layout.family, layout.variant, layout.headers], ensure_ascii=False).encode()).hexdigest()


class MappingPane(QWidget):
    def __init__(self, source, layout, sample, store, notify, parent=None):
        super().__init__(parent)
        self.source, self.layout, self.store, self.notify = source, layout, store, notify
        self.sample = sample
        self.decisions = suggest(source, layout)
        box = QVBoxLayout(self)
        top = QHBoxLayout()
        top.addWidget(text_label("Confira as correspondências. Sugestões incertas precisam de confirmação.", "muted"), 1)
        top.addWidget(button("Reutilizar perfil", self.load_profile))
        top.addWidget(button("Salvar perfil", self.save_profile))
        box.addLayout(top)
        self.grid = QTableWidget(0, 6)
        self.grid.setHorizontalHeaderLabels(["Origem", "Exemplos locais", "Destino", "Confiança", "Decisão", "Confirmado"])
        self.grid.verticalHeader().hide()
        self.grid.setAlternatingRowColors(True)
        self.grid.horizontalHeader().setStretchLastSection(True)
        box.addWidget(self.grid, 1)
        self.summary = text_label("", "muted")
        box.addWidget(self.summary)
        self.render()

    def render(self):
        self.grid.setRowCount(len(self.source.headers))
        self.combos, self.checks = [], []
        for i, d in enumerate(self.decisions):
            header = self.source.headers[i]
            examples = [raw[d.source].text for _, raw, _ in self.sample if raw and d.source in raw and raw[d.source].text][:3]
            for col, value in [(0, f"{d.source} · {header or '(sem cabeçalho)'}"), (1, " / ".join(examples)), (3, f"{d.confidence:.0%}" if d.target else "—"), (4, d.origin)]:
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.grid.setItem(i, col, item)
            combo = QComboBox()
            combo.addItem("— Não utilizar —", "")
            for target in targets(self.layout):
                combo.addItem(target, target)
            combo.setCurrentIndex(max(0, combo.findData(d.target)))
            combo.setAccessibleName(f"Destino de {d.source} {header}")
            check = QCheckBox("Confirmado")
            check.setChecked(d.confirmed)
            combo.currentIndexChanged.connect(lambda _, idx=i: self.manual(idx))
            self.grid.setCellWidget(i, 2, combo)
            self.grid.setCellWidget(i, 5, check)
            self.combos.append(combo)
            self.checks.append(check)
        self.grid.setColumnWidth(0, 210)
        self.grid.setColumnWidth(1, 230)
        self.grid.setColumnWidth(2, 280)
        self.grid.resizeRowsToContents()
        self.update_summary()

    def manual(self, index):
        self.checks[index].setChecked(True)
        self.decisions[index].origin = "Usuário"
        self.decisions[index].confidence = 1.
        self.grid.item(index, 3).setText("100%")
        self.grid.item(index, 4).setText("Usuário")
        self.update_summary()

    def get_decisions(self):
        return [Decision(d.source, self.combos[i].currentData(), d.confidence, d.origin, self.checks[i].isChecked(), d.reason) for i, d in enumerate(self.decisions)]

    def update_summary(self):
        mapped = {c.currentData() for c in self.combos}
        missing = [t for t in targets(self.layout) if t not in mapped]
        self.summary.setText("Sem origem mapeada (não implica obrigatoriedade): " + ", ".join(missing))

    def save_profile(self):
        name, ok = QInputDialog.getText(self, "Salvar mapeamento", "Nome do perfil (somente cabeçalhos e destinos serão guardados)")
        if ok and name.strip():
            mapping = {self.source.headers[i]: d.target for i, d in enumerate(self.get_decisions()) if d.target and d.confirmed}
            if len(set(self.source.headers)) != len(self.source.headers):
                self.notify("Cabeçalhos duplicados: renomeie as colunas em uma cópia antes de salvar o perfil.")
                return
            self.store.save_profile(name.strip(), fingerprint(self.layout), mapping)
            self.notify("Perfil salvo localmente, sem amostras ou valores de células.")

    def load_profile(self):
        profiles = self.store.profiles(fingerprint(self.layout))
        if not profiles:
            self.notify("Nenhum perfil salvo para esta estrutura de destino.")
            return
        labels = [f"{p[0]} · {p[1]}" for p in profiles]
        name, ok = QInputDialog.getItem(self, "Reutilizar perfil", "Perfil", labels, 0, False)
        if ok:
            saved = profiles[labels.index(name)][3]
            self.decisions = suggest(self.source, self.layout, saved)
            self.render()
