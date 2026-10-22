"""Sidebar recolhível com navegação por teclado e preferência local persistida."""
from PySide6.QtCore import QSize, Signal
from PySide6.QtWidgets import QButtonGroup, QVBoxLayout, QWidget

from app.ui.common import button
from app.ui.icons import icon
from app.ui.surfaces import SoftPanel
from app.ui.theme import palette

DESTINATIONS = [("Dashboard", "dashboard"), ("Importações", "imports"), ("Biblioteca", "folder"),
                ("Aparência", "appearance"), ("IA e perfis", "ai"), ("Diagnóstico", "activity")]


class NavigationRail(QWidget):
    selected = Signal(int)
    expanded_changed = Signal(bool)
    exit_requested = Signal()

    def __init__(self, expanded=False):
        super().__init__()
        self.expanded, self.mode, self.color = expanded, "light", "#09695D"
        body = QVBoxLayout(self)
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(24)
        toggle_surface = SoftPanel()
        toggle_box = QVBoxLayout(toggle_surface)
        toggle_box.setContentsMargins(8, 8, 8, 8)
        self.toggle = button("", self.toggle_expanded)
        self.toggle.setObjectName("railToggle")
        self.toggle.setCheckable(True)
        toggle_box.addWidget(self.toggle)
        body.addWidget(toggle_surface)
        rail = SoftPanel()
        box = QVBoxLayout(rail)
        box.setContentsMargins(8, 12, 8, 12)
        box.setSpacing(8)
        self.group = QButtonGroup(self)
        self.buttons = []
        for index, (label, _) in enumerate(DESTINATIONS):
            control = button("", lambda checked=False, i=index: self.selected.emit(i))
            control.setObjectName("railButton")
            control.setCheckable(True)
            control.setAccessibleName(label)
            control.setToolTip(label)
            control.setIconSize(QSize(23, 23))
            self.group.addButton(control)
            self.buttons.append(control)
            box.addWidget(control)
        box.addStretch()
        body.addWidget(rail, 1)
        exit_surface = SoftPanel()
        exit_box = QVBoxLayout(exit_surface)
        exit_box.setContentsMargins(8, 8, 8, 8)
        self.exit = button("", self.exit_requested.emit)
        self.exit.setObjectName("railToggle")
        self.exit.setAccessibleName("Fechar aplicativo")
        self.exit.setToolTip("Fechar aplicativo")
        exit_box.addWidget(self.exit)
        body.addWidget(exit_surface)
        self.set_current(0)

    def toggle_expanded(self):
        self.expanded = not self.expanded
        self.render()
        self.expanded_changed.emit(self.expanded)

    def set_current(self, index):
        self.buttons[index].setChecked(True)
        self.render()

    def apply_theme(self, color, mode):
        self.color, self.mode = color, mode
        self.render()

    def render(self):
        self.setFixedWidth(218 if self.expanded else 76)
        self.toggle.setChecked(self.expanded)
        label = "Recolher menu" if self.expanded else "Expandir menu"
        self.toggle.setText("  Recolher" if self.expanded else "")
        self.toggle.setAccessibleName(label)
        self.toggle.setToolTip(label)
        t = palette(self.color, self.mode)
        self.toggle.setIcon(icon("collapse" if self.expanded else "menu", t["ink"]))
        self.exit.setIcon(icon("exit", t["ink"]))
        self.exit.setText("  Fechar aplicativo" if self.expanded else "")
        for control, (label, glyph) in zip(self.buttons, DESTINATIONS):
            control.setText("  " + label if self.expanded else "")
            control.setIcon(icon(glyph, t["nav_on"] if control.isChecked() else t["ink"]))
        self.setProperty("expanded", self.expanded)
        # Re-polish only this widget's controls; no geometry animation to hide focus.
        for control in [self.toggle, self.exit, *self.buttons]:
            control.setProperty("expanded", self.expanded)
            control.style().unpolish(control)
            control.style().polish(control)
