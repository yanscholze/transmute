"""Ícones vetoriais locais, com traço uniforme e cores do tema.

Primitivas SVG evitam dependência de fontes, emojis ou downloads. O texto
acessível pertence ao controle que usa o ícone, nunca ao desenho decorativo.
"""
from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

SHAPES = {
    "dashboard": '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
    "imports": '<rect x="3" y="4" width="18" height="17" rx="2"/><path d="M3 10h18M8 4V2m8 2V2M8 15h8m-8 3h5"/>',
    "folder": '<path d="M3 7V5a2 2 0 0 1 2-2h4l3 3h7a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7Zm0 2h18"/>',
    "appearance": '<circle cx="12" cy="12" r="9"/><path d="M12 3a9 9 0 0 0 0 18Z" fill="currentColor"/>',
    "ai": '<circle cx="6" cy="6" r="3"/><circle cx="18" cy="18" r="3"/><circle cx="18" cy="5" r="2"/><path d="m8 8 8 8M9 6l7-1M6 9l-1 7h8"/>',
    "activity": '<path d="M3 20h18M5 15v-4m7 9V4m7 16v-9"/>',
    "menu": '<path d="M4 6h16M4 12h16M4 18h16"/>',
    "collapse": '<path d="m14 5-7 7 7 7M21 4v16"/>',
    "exit": '<path d="M9 4H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h4m5-13 5 5-5 5m-7-5h12"/>',
    "plus": '<path d="M12 4v16M4 12h16"/>',
    "arrow": '<path d="M5 12h14m-6-6 6 6-6 6"/>',
    "external": '<path d="M14 3h7v7m0-7L10 14M10 4H5a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h13a2 2 0 0 0 2-2v-5"/>',
    "copy": '<rect x="8" y="8" width="13" height="13" rx="2"/><path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3"/>',
    "rules": '<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9Zm0 0v6h6M8 13h8m-8 4h6"/>',
    "search": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
    "check": '<path d="m5 12 4 4L19 6"/>',
}


def icon(name, color="#24262B", size=24):
    """Renderize em dobro para manter linhas nítidas também em escala alta."""
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" color="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{SHAPES[name]}</svg>'
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    QSvgRenderer(QByteArray(svg.encode())).render(painter)
    painter.end()
    pixmap.setDevicePixelRatio(2)
    return QIcon(pixmap)
