"""Tema claro/escuro com acento independente e marca d'água atrás do conteúdo.

Superfícies neutras seguem a referência Soft UI. O acento colore ações, foco e
realces nos dois modos; contraste é calculado para qualquer cor configurada.
"""
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPalette, QPixmap
from PySide6.QtWidgets import QWidget


def mix(color, other, amount):
    a, b = QColor(color), QColor(other)
    return QColor(*(round(a.getRgb()[i] * (1 - amount) + b.getRgb()[i] * amount) for i in range(3))).name()


def luminance(color):
    c = QColor(color)
    parts = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in [c.redF(), c.greenF(), c.blueF()]]
    return sum(a * b for a, b in zip(parts, [.2126, .7152, .0722]))


def contrast(a, b):
    light, dark = sorted([luminance(a), luminance(b)], reverse=True)
    return (light + .05) / (dark + .05)


def foreground(color):
    chosen = max(["#FFFFFF", "#101820"], key=lambda value: contrast(value, color))
    return chosen if contrast(chosen, color) >= 4.5 else "#000000"


def palette(color, mode="light"):
    if not QColor(color).isValid():
        color = "#09695D"
    dark = mode == "dark"
    surface = "#292C32" if dark else "#F0F1F2"
    ink = "#F1F2F4" if dark else "#23262B"
    focus = color if contrast(color, surface) >= 3 else ink
    return {"primary": color, "on": foreground(color), "hover": mix(color, "#FFFFFF" if dark else "#000000", .12),
            "bg": "#1D1F24" if dark else "#E2E3E5", "surface": surface,
            "field": "#23262C" if dark else "#FAFAFB", "inset": "#22252B" if dark else "#E4E5E8",
            "tint": mix(color, surface, .90), "line": "#505661" if dark else "#BEC2C9",
            "stripe": "#2E3239" if dark else "#E9EBEE", "ink": ink,
            "muted": "#B9BFC9" if dark else "#59616D", "nav": surface,
            "nav_active": ink, "nav_on": foreground(ink),
            "edge": "#3D424C" if dark else "#FFFFFF", "focus": focus,
            "error": "#FF9B90" if dark else "#B42318", "warning": "#F7C873" if dark else "#8A4B06",
            "success": "#68D3B1" if dark else "#09695D",
            "disabled": "#767D89" if dark else "#6A717C"}


def native_palette(color, mode="light"):
    """Cubra popups, indicadores e controles nativos que não usam somente QSS."""
    t = palette(color, mode)
    result = QPalette()
    for role, value in [(QPalette.ColorRole.Window, t["bg"]), (QPalette.ColorRole.Base, t["field"]),
                        (QPalette.ColorRole.AlternateBase, t["stripe"]), (QPalette.ColorRole.Button, t["surface"]),
                        (QPalette.ColorRole.Text, t["ink"]), (QPalette.ColorRole.WindowText, t["ink"]),
                        (QPalette.ColorRole.ButtonText, t["ink"]), (QPalette.ColorRole.PlaceholderText, t["muted"]),
                        (QPalette.ColorRole.Highlight, t["primary"]), (QPalette.ColorRole.HighlightedText, t["on"]),
                        (QPalette.ColorRole.Light, t["edge"]), (QPalette.ColorRole.Mid, t["line"]),
                        (QPalette.ColorRole.Dark, t["muted"])]:
        result.setColor(role, QColor(value))
    return result


def stylesheet(color, mode="light"):
    t = palette(color, mode)
    return f"""
QWidget {{ color: {t['ink']}; font-size: 14px; background: transparent; }}
QMainWindow, QDialog {{ background: {t['bg']}; }}
QFrame#softPanel, QFrame#softPill {{ background: transparent; border: none; }}
QWidget#shell {{ background: {t['bg']}; }}
QLabel#brand {{ font-size: 19px; font-weight: 600; }}
QLabel#brandAvatar {{ background: {t['primary']}; color: {t['on']}; border-radius: 23px; font-size: 25px; font-weight: 600; }}
QLabel#headerTitle {{ font-size: 20px; font-weight: 600; }}
QLabel#eyebrow {{ color: {t['muted']}; font-size: 12px; }}
QLabel#title {{ font-size: 27px; font-weight: 700; }}
QLabel#section {{ font-size: 19px; font-weight: 600; }}
QLabel#subtitle, QLabel#muted {{ color: {t['muted']}; }}
QLabel#steps {{ background: {t['tint']}; padding: 13px 16px; border-radius: 8px; color: {t['ink']}; font-weight: 600; }}
QLabel#notice {{ background: {t['tint']}; padding: 12px; border-radius: 7px; }}
QLabel#drop {{ background: {t['tint']}; border: 2px dashed {t['line']}; padding: 22px; border-radius: 12px; }}
QLabel#stats, QFrame#card {{ background: {t['surface']}; border: 1px solid {t['line']}; padding: 14px; border-radius: 12px; }}
QPushButton {{ background: {t['field']}; border: 1px solid {t['line']}; border-radius: 10px; padding: 9px 14px; min-height: 20px; }}
QPushButton:hover {{ background: {t['tint']}; }}
QPushButton:pressed {{ background: {t['line']}; }}
QPushButton#primary {{ background: {t['primary']}; color: {t['on']}; border-color: {t['primary']}; font-weight: 600; }}
QPushButton#primary:hover {{ background: {t['hover']}; color: {foreground(t['hover'])}; }}
QPushButton:disabled {{ color: {t['disabled']}; background: {t['inset']}; border-color: {t['line']}; }}
QPushButton:focus, QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QCheckBox:focus {{ border: 2px solid {t['focus']}; }}
QLineEdit, QComboBox, QSpinBox {{ background: {t['field']}; border: 1px solid {t['line']}; border-radius: 8px; padding: 7px; min-height: 20px; selection-background-color: {t['primary']}; selection-color: {t['on']}; }}
QComboBox QAbstractItemView {{ background: {t['field']}; selection-background-color: {t['tint']}; selection-color: {t['ink']}; }}
QTableView, QTableWidget, QTextEdit, QPlainTextEdit, QListWidget {{ background: {t['field']}; alternate-background-color: {t['stripe']}; border: 1px solid {t['line']}; border-radius: 10px; gridline-color: {t['inset']}; selection-background-color: {t['tint']}; selection-color: {t['ink']}; }}
QTableView#importsGrid {{ background: transparent; alternate-background-color: {t['stripe']}; }}
QTextEdit, QPlainTextEdit {{ padding: 8px; }}
QHeaderView::section {{ background: {t['tint']}; border: none; border-bottom: 1px solid {t['line']}; padding: 10px; font-weight: 600; }}
QTabWidget::pane {{ border: 1px solid {t['line']}; background: {t['surface']}; border-radius: 7px; }}
QTabBar::tab {{ background: {t['tint']}; padding: 10px 14px; border-bottom: 2px solid transparent; }}
QTabBar::tab:selected {{ background: {t['surface']}; border-bottom: 2px solid {t['primary']}; font-weight: 600; }}
QCheckBox {{ padding: 8px 2px; spacing: 8px; }}
QCheckBox::indicator {{ width: 18px; height: 18px; }}
QCheckBox#categoryCard {{ background: {t['field']}; border: 1px solid {t['line']}; border-radius: 8px; padding: 12px; }}
QCheckBox#categoryCard:hover {{ border-color: {t['primary']}; }}
QCheckBox#categoryCard:checked {{ background: {t['tint']}; border: 2px solid {t['primary']}; font-weight: 600; }}
QProgressBar {{ border: 1px solid {t['line']}; border-radius: 4px; background: {t['tint']}; height: 10px; text-align: center; }}
QProgressBar::chunk {{ background: {t['primary']}; }}
QSlider::groove:horizontal {{ height: 6px; background: {t['line']}; border-radius: 3px; }}
QSlider::handle:horizontal {{ background: {t['primary']}; width: 18px; margin: -6px 0; border-radius: 9px; }}
QScrollArea {{ border: none; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {t['line']}; min-height: 36px; border-radius: 5px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 0; }}
QScrollBar::handle:horizontal {{ background: {t['line']}; min-width: 36px; border-radius: 5px; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: transparent; }}
QToolTip {{ background: {t['nav_active']}; color: {t['nav_on']}; padding: 8px; border: none; }}
QPushButton#railButton, QPushButton#railToggle {{ background: transparent; border: 2px solid transparent; border-radius: 18px; min-height: 28px; padding: 8px; }}
QPushButton#railButton[expanded="true"], QPushButton#railToggle[expanded="true"] {{ text-align: left; }}
QPushButton#railButton:hover, QPushButton#railToggle:hover {{ background: {t['tint']}; }}
QPushButton#railButton:checked {{ background: {t['nav_active']}; color: {t['nav_on']}; }}
QPushButton#railButton:focus, QPushButton#railToggle:focus {{ border-color: {t['focus']}; }}
QPushButton#railButton:checked:focus {{ border-color: {t['surface']}; }}
QLineEdit#globalSearch {{ background: transparent; border: none; padding: 4px; }}
QLineEdit#globalSearch:focus {{ border-bottom: 2px solid {t['focus']}; }}
QPushButton#textLink {{ background: transparent; border: 1px solid transparent; padding: 4px 7px; font-size: 12px; }}
QPushButton#textLink:hover {{ background: {t['tint']}; border-color: {t['line']}; }}
QPushButton#textLink:focus {{ border-color: {t['focus']}; }}
QPushButton#iconButton {{ padding: 6px; min-width: 24px; min-height: 24px; border-radius: 12px; }}
QPushButton#newImportTile {{ background: {t['primary']}; color: {t['on']}; border: 2px solid {t['primary']}; border-radius: 19px; text-align: left; min-height: 190px; padding: 0; }}
QPushButton#newImportTile QLabel {{ color: {t['on']}; background: transparent; }}
QPushButton#newImportTile:hover {{ background: {t['hover']}; }}
QPushButton#newImportTile:focus {{ border: 3px solid {t['ink']}; }}
QLabel#tileHeading {{ font-size: 25px; font-weight: 600; }}
QFrame#metricPanel {{ background: {t['inset']}; border: 1px solid {t['line']}; border-radius: 19px; }}
QLabel#metricValue {{ font-size: 40px; font-weight: 600; }}
QLabel#cardHeading {{ font-size: 17px; font-weight: 600; }}
QLabel#smallText {{ color: {t['muted']}; font-size: 12px; }}
QLabel#rowTitle {{ font-weight: 600; }}
QPushButton#recentRow, QPushButton#shortcutRow {{ background: transparent; border: 1px solid transparent; text-align: left; padding: 0; min-height: 58px; }}
QPushButton#recentRow:hover, QPushButton#shortcutRow:hover {{ background: {t['tint']}; }}
QPushButton#recentRow:focus, QPushButton#shortcutRow:focus {{ border-color: {t['focus']}; }}
QLabel#statusPill {{ background: {t['inset']}; border: 1px solid {t['line']}; border-radius: 10px; padding: 4px 8px; font-size: 11px; }}
QLineEdit#pathField {{ background: {t['inset']}; font-size: 12px; border: 1px solid {t['line']}; }}
QLabel#localBadge {{ color: {t['muted']}; font-size: 12px; }}
"""


class Backdrop(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config, self.logo = {}, QPixmap()

    def configure(self, config):
        self.config = dict(config)
        path = Path(config.get("logo_path", ""))
        self.logo = QPixmap(str(path)) if path.is_file() else QPixmap()
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = palette(self.config.get("primary_color", "#09695D"), self.config.get("theme_mode", "light"))
        painter.fillRect(self.rect(), QColor(t["bg"]))
        if self.config.get("panel_surface"):
            painter.setPen(QColor(t["edge"]))
            painter.setBrush(QColor(t["surface"]))
            painter.drawRoundedRect(self.rect().adjusted(1, 1, -7, -8), 24, 24)
        if self.logo.isNull():
            return
        width = int(self.width() * self.config.get("logo_size", 50) / 100)
        logo = self.logo.scaled(width, int(self.height() * .85), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        x, y = (self.width() - logo.width()) // 2, (self.height() - logo.height()) // 2
        if self.config.get("logo_position") == "bottom-right":
            x, y = self.width() - logo.width() - 24, self.height() - logo.height() - 24
        painter.setOpacity(self.config.get("logo_opacity", 8) / 100)
        painter.drawPixmap(max(0, x), max(0, y), logo)
