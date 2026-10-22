"""Paleta derivada de uma cor e marca d'água desenhada atrás do conteúdo.

Todas as superfícies usam os mesmos tokens. O contraste do botão é calculado
para cores claras/escuras; logo conserva proporção e não recebe eventos.
"""
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QWidget


def mix(color, other, amount):
    a, b = QColor(color), QColor(other)
    return QColor(*(round(a.getRgb()[i] * (1 - amount) + b.getRgb()[i] * amount) for i in range(3))).name()


def foreground(color):
    c = QColor(color)
    parts = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in [c.redF(), c.greenF(), c.blueF()]]
    lum = sum(a * b for a, b in zip(parts, [.2126, .7152, .0722]))
    return "#FFFFFF" if 1.05 / (lum + .05) >= (lum + .05) / .05 else "#101820"


def palette(color):
    if not QColor(color).isValid():
        color = "#09695D"
    return {"primary": color, "on": foreground(color), "hover": mix(color, "#000000", .12),
            "bg": mix(color, "#FFFFFF", .965), "tint": mix(color, "#FFFFFF", .90),
            "line": mix(color, "#FFFFFF", .73), "stripe": mix(color, "#FFFFFF", .97),
            "ink": mix(color, "#101820", .83), "muted": mix(color, "#34454F", .84),
            "nav": mix(color, "#101820", .76), "nav_active": mix(color, "#101820", .36)}


def stylesheet(color):
    t = palette(color)
    return f"""
QWidget {{ color: {t['ink']}; font-size: 14px; background: transparent; }}
QMainWindow, QDialog {{ background: {t['bg']}; }}
QFrame#sidebar {{ background: {t['nav']}; border: none; }}
QFrame#sidebar QLabel {{ color: #F5F8FA; }}
QLabel#brand {{ font-size: 21px; font-weight: 700; padding: 8px 0; }}
QFrame#sidebar QPushButton {{ color: #F5F8FA; background: transparent; border: none; text-align: left; padding: 13px 15px; }}
QFrame#sidebar QPushButton:hover {{ background: {t['nav_active']}; }}
QFrame#sidebar QPushButton:checked {{ background: {t['primary']}; color: {t['on']}; font-weight: 600; }}
QLabel#title {{ font-size: 28px; font-weight: 700; }}
QLabel#section {{ font-size: 19px; font-weight: 600; }}
QLabel#subtitle, QLabel#muted {{ color: {t['muted']}; }}
QLabel#steps {{ background: {t['tint']}; padding: 13px 16px; border-radius: 8px; color: {t['ink']}; font-weight: 600; }}
QLabel#notice {{ background: {t['tint']}; padding: 12px; border-radius: 7px; }}
QLabel#drop {{ background: {t['tint']}; border: 2px dashed {t['line']}; padding: 22px; border-radius: 12px; }}
QLabel#stats, QFrame#card {{ background: #FFFFFF; border: 1px solid {t['line']}; padding: 14px; border-radius: 8px; }}
QPushButton {{ background: #FFFFFF; border: 1px solid {t['line']}; border-radius: 7px; padding: 9px 14px; min-height: 20px; }}
QPushButton:hover {{ background: {t['tint']}; }}
QPushButton:pressed {{ background: {t['line']}; }}
QPushButton#primary {{ background: {t['primary']}; color: {t['on']}; border-color: {t['primary']}; font-weight: 600; }}
QPushButton#primary:hover {{ background: {t['hover']}; color: {foreground(t['hover'])}; }}
QPushButton:disabled {{ color: #68747C; background: #E4E9EC; border-color: #D2DADF; }}
QPushButton:focus, QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QCheckBox:focus {{ border: 2px solid {t['primary']}; }}
QLineEdit, QComboBox, QSpinBox {{ background: #FFFFFF; border: 1px solid {t['line']}; border-radius: 6px; padding: 7px; min-height: 20px; selection-background-color: {t['primary']}; selection-color: {t['on']}; }}
QComboBox QAbstractItemView {{ background: #FFFFFF; selection-background-color: {t['tint']}; selection-color: {t['ink']}; }}
QTableView, QTableWidget, QTextEdit, QPlainTextEdit, QListWidget {{ background: #FFFFFF; alternate-background-color: {t['stripe']}; border: 1px solid {t['line']}; border-radius: 7px; gridline-color: {t['tint']}; selection-background-color: {t['tint']}; selection-color: {t['ink']}; }}
QTableView#importsGrid {{ background: transparent; alternate-background-color: {t['stripe']}; }}
QTextEdit, QPlainTextEdit {{ padding: 8px; }}
QHeaderView::section {{ background: {t['tint']}; border: none; border-bottom: 1px solid {t['line']}; padding: 10px; font-weight: 600; }}
QTabWidget::pane {{ border: 1px solid {t['line']}; background: #FFFFFF; border-radius: 7px; }}
QTabBar::tab {{ background: {t['tint']}; padding: 10px 14px; border-bottom: 2px solid transparent; }}
QTabBar::tab:selected {{ background: #FFFFFF; border-bottom: 2px solid {t['primary']}; font-weight: 600; }}
QCheckBox {{ padding: 8px 2px; spacing: 8px; }}
QCheckBox::indicator {{ width: 18px; height: 18px; }}
QCheckBox#categoryCard {{ background: #FFFFFF; border: 1px solid {t['line']}; border-radius: 8px; padding: 12px; }}
QCheckBox#categoryCard:hover {{ border-color: {t['primary']}; }}
QCheckBox#categoryCard:checked {{ background: {t['tint']}; border: 2px solid {t['primary']}; font-weight: 600; }}
QProgressBar {{ border: 1px solid {t['line']}; border-radius: 4px; background: {t['tint']}; height: 10px; text-align: center; }}
QProgressBar::chunk {{ background: {t['primary']}; }}
QSlider::groove:horizontal {{ height: 6px; background: {t['line']}; border-radius: 3px; }}
QSlider::handle:horizontal {{ background: {t['primary']}; width: 18px; margin: -6px 0; border-radius: 9px; }}
QScrollArea {{ border: none; }}
QToolTip {{ background: {t['nav']}; color: #FFFFFF; padding: 8px; border: none; }}
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
        painter.fillRect(self.rect(), QColor(palette(self.config.get("primary_color", "#09695D"))["bg"]))
        if self.logo.isNull():
            return
        width = int(self.width() * self.config.get("logo_size", 50) / 100)
        logo = self.logo.scaled(width, int(self.height() * .85), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        x, y = (self.width() - logo.width()) // 2, (self.height() - logo.height()) // 2
        if self.config.get("logo_position") == "bottom-right":
            x, y = self.width() - logo.width() - 24, self.height() - logo.height() - 24
        painter.setOpacity(self.config.get("logo_opacity", 8) / 100)
        painter.drawPixmap(max(0, x), max(0, y), logo)
