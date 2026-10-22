"""Visão geral operacional: metadados reais, atalhos e fontes configuradas.

O dashboard não lê células, não processa bases e não guarda cópias do histórico.
Usa o catálogo já carregado pelo shell e o manifesto dos trabalhos. Caminhos
podem ser copiados ou abertos localmente; o editor continua na Biblioteca.
"""
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QFrame, QGridLayout, QHBoxLayout, QLineEdit, QProgressBar, QScrollArea, QSizePolicy, QVBoxLayout, QWidget

from app.core.catalog import rules_path, verify_rules, workspace_config
from app.storage.dashboard import summarize
from app.storage.imports import FAMILIES
from app.ui.common import button, text_label
from app.ui.icons import icon
from app.ui.surfaces import ElidedLabel, SoftPanel
from app.ui.theme import palette


def date_label(value):
    try:
        return datetime.fromisoformat(value).strftime("%d/%m · %H:%M")
    except (TypeError, ValueError):
        return "Data não disponível"


def decorative(widget):
    """Filhos visuais não interceptam o clique/teclado do botão que os contém."""
    widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    return widget


class PathAccess(QWidget):
    def __init__(self, label, notify):
        super().__init__()
        self.path, self.notify = None, notify
        box = QHBoxLayout(self)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(7)
        self.field = QLineEdit()
        self.field.setObjectName("pathField")
        self.field.setReadOnly(True)
        self.field.setAccessibleName(label)
        box.addWidget(self.field, 1)
        self.copy = button("", self.copy_path)
        self.copy.setAccessibleName("Copiar caminho de " + label.lower())
        self.copy.setToolTip(self.copy.accessibleName())
        self.open = button("", self.open_folder)
        self.open.setAccessibleName("Abrir pasta de " + label.lower())
        self.open.setToolTip(self.open.accessibleName())
        for control in [self.copy, self.open]:
            control.setObjectName("iconButton")
            control.setFixedSize(38, 38)
            box.addWidget(control)

    def configure(self, path, t):
        self.path = Path(path) if path else None
        self.field.setText(str(self.path) if self.path else "Nenhum caminho configurado")
        self.field.setCursorPosition(0)
        self.field.setToolTip(self.field.text())
        self.copy.setIcon(icon("copy", t["ink"], 18))
        self.open.setIcon(icon("folder", t["ink"], 18))
        self.copy.setEnabled(bool(self.path))
        self.open.setEnabled(bool(self.path and self.path.exists()))

    def copy_path(self):
        if self.path:
            QApplication.clipboard().setText(str(self.path))
            self.copy.setToolTip("Caminho copiado")

    def open_folder(self):
        if not self.path or not self.path.exists():
            self.notify("O caminho configurado não existe. Atualize-o em Biblioteca.")
            return
        folder = self.path if self.path.is_dir() else self.path.parent
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder))):
            self.notify("Não foi possível abrir a pasta. Você pode copiar o caminho ao lado.")


class Dashboard(QScrollArea):
    def __init__(self, root, imports, store, navigate, start, open_import, edit_rules, notify):
        super().__init__()
        self.root, self.imports, self.store = root, imports, store
        self.navigate, self.start, self.open_import, self.edit_rules = navigate, start, open_import, edit_rules
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setAccessibleName("Dashboard com resumo das importações e atalhos")
        self.canvas = QWidget()
        self.grid = QGridLayout(self.canvas)
        self.grid.setContentsMargins(9, 9, 13, 15)
        self.grid.setSpacing(23)
        self.grid.setHorizontalSpacing(18)
        self.grid.setColumnStretch(0, 5)
        self.grid.setColumnStretch(1, 3)
        self.grid.setColumnStretch(2, 3)
        self.recent_panel = self.make_recent()
        self.launch_panel = self.make_launch()
        self.shortcuts_panel = self.make_shortcuts()
        self.models_panel = self.make_models(notify)
        self.rules_panel = self.make_rules(notify)
        self.grid.addWidget(self.recent_panel, 0, 0)
        self.grid.addWidget(self.launch_panel, 0, 1)
        self.grid.addWidget(self.shortcuts_panel, 0, 2)
        self.grid.addWidget(self.models_panel, 1, 0)
        self.grid.addWidget(self.rules_panel, 1, 1, 1, 2)
        self.grid.setRowStretch(0, 3)
        self.grid.setRowStretch(1, 1)
        self.setWidget(self.canvas)

    def panel_box(self, panel):
        box = QVBoxLayout(panel)
        box.setContentsMargins(22, 22, 22, 20)
        box.setSpacing(12)
        return box

    def link(self, label, callback):
        control = button(label, callback)
        control.setObjectName("textLink")
        return control

    def make_recent(self):
        panel = SoftPanel()
        panel.setMinimumWidth(240)
        panel.setMinimumHeight(446)
        box = self.panel_box(panel)
        top = QHBoxLayout()
        top.addWidget(text_label("Últimas importações", "cardHeading"), 1)
        top.addWidget(self.link("Ver todas", lambda: self.navigate(1)))
        box.addLayout(top)
        self.overview = text_label("", "smallText")
        box.addWidget(self.overview)
        self.recent_body = QVBoxLayout()
        self.recent_body.setSpacing(7)
        box.addLayout(self.recent_body, 1)
        self.recent_footer = text_label("Últimos estados salvos dos trabalhos.", "smallText")
        box.addWidget(self.recent_footer)
        return panel

    def make_launch(self):
        panel = SoftPanel()
        panel.setMinimumWidth(185)
        box = QVBoxLayout(panel)
        box.setContentsMargins(14, 14, 14, 14)
        box.setSpacing(17)
        self.new_button = button("", self.start)
        self.new_button.setObjectName("newImportTile")
        self.new_button.setAccessibleName("Iniciar nova importação e escolher tabelas")
        self.new_button.setMinimumHeight(190)
        self.new_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        tile = QVBoxLayout(self.new_button)
        tile.setContentsMargins(15, 15, 15, 15)
        top = QHBoxLayout()
        self.plus = decorative(text_label(""))
        top.addWidget(self.plus)
        top.addStretch()
        tile.addLayout(top)
        tile.addStretch()
        tile.addWidget(decorative(text_label("Nova\nimportação", "tileHeading")))
        tile.addStretch()
        tile.addWidget(decorative(text_label("Escolher tabelas  →")))
        box.addWidget(self.new_button, 1)
        metric = QFrame()
        metric.setObjectName("metricPanel")
        inner = QVBoxLayout(metric)
        inner.setContentsMargins(16, 16, 16, 16)
        inner.setSpacing(6)
        inner.addWidget(text_label("Taxa de sucesso", "cardHeading"))
        self.rate = text_label("—", "metricValue")
        inner.addWidget(self.rate)
        self.rate_bar = QProgressBar()
        self.rate_bar.setObjectName("successRateBar")
        self.rate_bar.setRange(0, 100)
        self.rate_bar.setTextVisible(False)
        self.rate_bar.setFixedHeight(7)
        inner.addWidget(self.rate_bar)
        self.rate_caption = text_label("", "smallText")
        inner.addWidget(self.rate_caption)
        inner.addStretch()
        metric.setToolTip("Prontas + exportadas ÷ trabalhos com resultado. Aguardando e interrompidas ficam fora. Não mede aceite no ERP.")
        metric.setAccessibleName("Taxa de sucesso no processamento local")
        box.addWidget(metric, 1)
        return panel

    def make_shortcuts(self):
        panel = SoftPanel()
        panel.setMinimumWidth(206)
        box = self.panel_box(panel)
        box.addWidget(text_label("Seu espaço", "cardHeading"))
        box.addWidget(text_label("Um atalho para cada área", "smallText"))
        self.shortcuts = []
        for index, (label, glyph) in enumerate([("Importações", "imports"), ("Biblioteca", "folder"),
                                                ("Aparência", "appearance"), ("IA e perfis", "ai"), ("Diagnóstico", "activity")], 1):
            control, caption, picture = self.row(label, "", lambda checked=False, i=index: self.navigate(i), glyph)
            control.setObjectName("shortcutRow")
            box.addWidget(control, 1)
            self.shortcuts.append((control, caption, picture, glyph))
        return panel

    def row(self, title, subtitle, callback, glyph=None):
        control = button("", callback)
        control.setAccessibleName(title)
        control.setMinimumHeight(58)
        control.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        row = QHBoxLayout(control)
        row.setContentsMargins(6, 7, 6, 7)
        row.setSpacing(10)
        picture = decorative(text_label(""))
        if glyph:
            picture.setFixedWidth(24)
            row.addWidget(picture)
        text = QVBoxLayout()
        text.setSpacing(3)
        heading = decorative(ElidedLabel(title))
        heading.setObjectName("rowTitle")
        caption = decorative(ElidedLabel(subtitle))
        caption.setObjectName("smallText")
        text.addWidget(heading)
        text.addWidget(caption)
        row.addLayout(text, 1)
        control.setToolTip(title + ("\n" + subtitle if subtitle else ""))
        return control, caption, picture

    def make_models(self, notify):
        panel = SoftPanel()
        box = self.panel_box(panel)
        top = QHBoxLayout()
        top.addWidget(text_label("Planilhas de base", "cardHeading"), 1)
        top.addWidget(self.link("Configurar", lambda: self.navigate(2)))
        box.addLayout(top)
        self.models_summary = text_label("", "smallText")
        box.addWidget(self.models_summary)
        self.models_path = PathAccess("Planilhas de base", notify)
        box.addWidget(self.models_path)
        self.models_extra = text_label("", "smallText")
        box.addWidget(self.models_extra)
        return panel

    def make_rules(self, notify):
        panel = SoftPanel()
        box = self.panel_box(panel)
        top = QHBoxLayout()
        top.addWidget(text_label("Regras de conversão", "cardHeading"), 1)
        self.rules_editor = self.link("Abrir e editar", self.edit_rules)
        top.addWidget(self.rules_editor)
        box.addLayout(top)
        self.rules_summary = text_label("", "smallText")
        box.addWidget(self.rules_summary)
        self.rules_path = PathAccess("Regras de conversão", notify)
        box.addWidget(self.rules_path)
        box.addWidget(text_label("Texto e perfil executável revisados em conjunto.", "smallText"))
        return panel

    def refresh(self, layouts):
        config = workspace_config(self.root)
        t = palette(config.get("primary_color", "#09695D"), config.get("theme_mode", "light"))
        jobs = self.imports.list()
        self.summary = summarize(jobs)
        s = self.summary
        self.overview.setText(f"{s['total']} no total · {s['ready']} prontas · {s['pending']} com pendências")
        while self.recent_body.count():
            item = self.recent_body.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.recent_buttons = []
        for job in jobs[:4]:
            categories = ", ".join(FAMILIES.get(c, c) for c in job["categories"])
            subtitle = date_label(job["updated"]) + " · " + categories
            control, _, _ = self.row(job["name"], subtitle, lambda checked=False, ident=job["id"]: self.open_import(ident))
            control.setObjectName("recentRow")
            control.setAccessibleName(job["name"] + " · " + job["status"])
            short = {"Pronta para exportar": "Pronta", "Revisar pendências": "Revisar",
                     "Aguardando processamento": "Aguardando"}.get(job["status"], job["status"])
            status = decorative(text_label(short, "statusPill"))
            status.setWordWrap(False)
            status.setToolTip(job["status"])
            control.layout().addWidget(status)
            self.recent_body.addWidget(control)
            self.recent_buttons.append(control)
        if not jobs:
            empty = QWidget()
            body = QVBoxLayout(empty)
            body.setContentsMargins(4, 25, 4, 25)
            picture = text_label("")
            picture.setPixmap(icon("imports", t["muted"], 38).pixmap(QSize(38, 38)))
            body.addWidget(picture)
            body.addWidget(text_label("Tudo pronto para começar", "cardHeading"))
            body.addWidget(text_label("Crie uma importação, escolha as tabelas e reúna os arquivos recebidos.", "muted"))
            body.addStretch()
            body.addWidget(self.link("Iniciar primeira importação  →", self.start), alignment=Qt.AlignmentFlag.AlignLeft)
            self.recent_body.addWidget(empty)
        self.recent_body.addStretch()
        self.rate.setText(f"{s['rate']}%" if s["rate"] is not None else "—")
        self.rate_bar.setValue(s["rate"] or 0)
        self.rate_bar.setAccessibleName("Taxa de sucesso: " + (f"{s['rate']} por cento" if s["rate"] is not None else "sem resultados ainda"))
        self.rate_caption.setText(f"{s['successful']} de {s['assessed']} com resultado sem pendências" if s["assessed"] else "Aparece após o primeiro processamento.")
        self.plus.setPixmap(icon("plus", t["on"], 25).pixmap(QSize(25, 25)))
        profiles = len(self.store.profiles())
        enabled = self.store.setting("ai", {}).get("enabled", False)
        captions = [f"{s['total']} trabalhos · {s['exported']} exportados", f"{len(layouts)} modelos disponíveis",
                    f"Tema {'escuro' if config.get('theme_mode') == 'dark' else 'claro'} · cor e logo",
                    f"IA {'habilitada' if enabled else 'opcional'} · {profiles} perfis",
                    f"{len(self.store.history())} eventos técnicos recentes"]
        for (control, caption, picture, glyph), value in zip(self.shortcuts, captions):
            caption.setText(value)
            control.setToolTip(control.accessibleName() + "\n" + value)
            picture.setPixmap(icon(glyph, t["ink"], 22).pixmap(QSize(22, 22)))
        count = len({x.family for x in layouts})
        self.models_summary.setText(f"{len(layouts)} modelos em {count} categorias")
        models = config.get("models_dir", "")
        self.models_path.configure(models, t)
        uploads = len(config.get("uploaded_models", []))
        self.models_extra.setText(f"{uploads} modelos adicionados à biblioteca local" if uploads else "Pasta de referência · originais preservados")
        if not models or not Path(models).is_dir():
            self.models_extra.setText("Pasta não disponível. Configure uma pasta ou adicione modelos.")
        self.rules_path.configure(rules_path(self.root), t)
        try:
            verify_rules(self.root)
            self.rules_summary.setText("Revisão aprovada · documentação e perfil conferem")
        except (OSError, ValueError, KeyError):
            self.rules_summary.setText("Revisão necessária · abra o editor para conferir as regras")
