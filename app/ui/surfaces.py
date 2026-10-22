"""Superfícies suaves e texto truncável compartilhados pelo shell/dashboard.

Sombras são pintadas no próprio painel. Efeitos que cacheiam o subtree inteiro
podem recortar filhos após redimensionar/navegar; aqui somente a superfície é
desenhada, preservando a pintura normal e as hitboxes de cada controle filho.
"""
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QFrame, QLabel

from app.ui.theme import palette


class SoftPanel(QFrame):
    def __init__(self, parent=None, pill=False):
        super().__init__(parent)
        self.pill = pill
        self.setObjectName("softPill" if pill else "softPanel")
        # Children are laid out inside the painted surface, excluding shadow space.
        self.setContentsMargins(4, 4, 10, 10)
        self.apply_theme("light")

    def apply_theme(self, mode):
        self.mode = mode
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        rect = QRectF(self.rect()).adjusted(4, 4, -10, -10)
        radius = min(31 if self.pill else 23, rect.height() / 2)
        # Concentric translucent layers approximate a small blur without rendering
        # the children to an offscreen cache. All shadow pixels fit this widget.
        for spread in range(8, 0, -1):
            alpha = round((9 - spread) * (1.2 if self.mode == "dark" else .8))
            painter.setBrush(QColor(0, 0, 0, alpha))
            shadow = rect.adjusted(-spread, -spread, spread, spread).translated(3, 4)
            painter.drawRoundedRect(shadow, radius + spread, radius + spread)
            if self.mode != "dark":
                painter.setBrush(QColor(255, 255, 255, round((9 - spread) * 1.8)))
                painter.drawRoundedRect(rect.adjusted(-spread / 2, -spread / 2, spread / 2, spread / 2).translated(-2, -2), radius, radius)
        t = palette("#09695D", self.mode)
        painter.setPen(QColor(t["edge"]))
        painter.setBrush(QColor(t["surface"]))
        painter.drawRoundedRect(rect, radius, radius)


class ElidedLabel(QLabel):
    """Rótulo de uma linha; mantém nome/caminho completo no tooltip e a11y."""
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.full_text = ""
        self.setMinimumWidth(0)
        self.setText(text)

    def setText(self, text):
        self.full_text = str(text)
        self.setToolTip(self.full_text)
        self.setAccessibleName(self.full_text)
        self.render()

    def render(self):
        super().setText(self.fontMetrics().elidedText(self.full_text, Qt.TextElideMode.ElideRight, max(0, self.width())))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.render()

    def sizeHint(self):
        hint = super().sizeHint()
        hint.setWidth(min(hint.width(), 200))
        return hint
