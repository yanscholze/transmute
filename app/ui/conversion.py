"""Coordena o assistente e o ciclo de vida das sessões principal/vinculada.

UI coleta decisões e despacha operações ao core. Correção pendente bloqueia
exportação até revalidar; uma chamada de IA nunca escreve uma célula.
"""
from itertools import islice

from PySide6.QtCore import Signal

from PySide6.QtWidgets import QCheckBox, QFileDialog, QHBoxLayout, QMessageBox, QStackedWidget, QTabWidget, QVBoxLayout, QWidget

from app.core.exporters.writer import export
from app.core.importers.reader import records
from app.core.session import process, validate_links
from app.ui.common import button, text_label
from app.ui.input import InputPane
from app.ui.mapping import MappingPane
from app.ui.options import OptionsPane
from app.ui.review import ReviewPane


class ConversionPane(QWidget):
    processed_event = Signal(object)
    exported_event = Signal(object)

    def __init__(self, root, state, layouts, store, run_job, notify, parent=None):
        super().__init__(parent)
        self.root, self.state, self.layouts, self.store = root, state, layouts, store
        self.run_job, self.notify = run_job, notify
        self.sessions, self.mappings = [], []
        self.dirty = False
        body = QVBoxLayout(self)
        body.setSpacing(16)
        body.addWidget(text_label("Nova conversão", "title"))
        body.addWidget(text_label("Prepare uma base para o ERP com revisão e rastreabilidade.", "subtitle"))
        self.steps = text_label("01  Arquivo e modelo     /     02  Mapeamento e regras     /     03  Validação e exportação", "steps")
        body.addWidget(self.steps)
        self.pages = QStackedWidget()
        body.addWidget(self.pages, 1)
        filepage = QWidget()
        filebody = QVBoxLayout(filepage)
        self.linked = QCheckBox("Processar também a base vinculada de cabeçalhos/itens (OS ou vendas)")
        filebody.addWidget(self.linked)
        self.inputs = QTabWidget()
        self.main_input = InputPane(layouts, run_job)
        self.related_input = InputPane(layouts, run_job)
        self.inputs.addTab(self.main_input, "Base principal")
        self.inputs.addTab(self.related_input, "Base vinculada")
        self.inputs.setTabEnabled(1, False)
        self.linked.toggled.connect(lambda enabled: self.inputs.setTabEnabled(1, enabled))
        filebody.addWidget(self.inputs, 1)
        self.pages.addWidget(filepage)
        self.map_tabs = QTabWidget()
        self.options = OptionsPane()
        self.pages.addWidget(self.map_tabs)
        self.review = ReviewPane(self.correct)
        self.pages.addWidget(self.review)
        self.notice = text_label("Modo local · IA desativada por padrão · nenhum dado é enviado automaticamente", "notice")
        body.addWidget(self.notice)
        footer = QHBoxLayout()
        self.back = button("Voltar", self.previous)
        self.ai_button = button("Sugerir com IA…", self.ai_suggest)
        self.ai_button.setVisible(False)
        self.revalidate = button("Revalidar correções", self.process)
        self.revalidate.setVisible(False)
        self.report = button("Exportar relatório", lambda: self.do_export(True))
        self.report.setVisible(False)
        self.next = button("Continuar para mapeamento", self.advance, True)
        footer.addWidget(self.back)
        footer.addWidget(self.ai_button)
        footer.addStretch()
        footer.addWidget(self.report)
        footer.addWidget(self.revalidate)
        footer.addWidget(self.next)
        body.addLayout(footer)
        self.update_step()

    def release_sessions(self):
        """Transfira a posse ao trabalho sem remover os arquivos temporários."""
        self.sessions = []

    def panes(self):
        return [self.main_input, self.related_input] if self.linked.isChecked() else [self.main_input]

    def previous(self):
        self.pages.setCurrentIndex(max(0, self.pages.currentIndex() - 1))
        self.update_step()

    def advance(self):
        index = self.pages.currentIndex()
        if index == 0:
            if any(p.layout is None for p in self.panes()):
                self.notify("Adicione planilhas de base na tela inicial e selecione um modelo.")
                return
            if any(p.source is None for p in self.panes()):
                self.notify("Leia a prévia de cada arquivo antes de continuar.")
                return
            if self.linked.isChecked():
                a, b = [p.layout for p in self.panes()]
                if a.family not in {"os", "vendas"} or a.family != b.family or {a.variant, b.variant} != {"header", "items"}:
                    self.notify("Bases vinculadas precisam usar modelos de cabeçalhos e itens da mesma família.")
                    return
            def task(control):
                return [list(islice(records(p.source, control), 20)) for p in self.panes()]
            self.run_job(task, self.prepare_mapping, "Preparando exemplos para mapeamento…")
        elif index == 1:
            self.process()
        else:
            self.do_export(False)

    def prepare_mapping(self, samples):
        self.mappings = []
        self.map_tabs.clear()
        self.options.overrides = [{}, {}]
        for pane, sample in zip(self.panes(), samples):
            mapping = MappingPane(pane.source, pane.layout, sample, self.store, self.notify)
            self.mappings.append(mapping)
            self.map_tabs.addTab(mapping, pane.layout.label)
        self.map_tabs.addTab(self.options, "Regras e conflitos")
        self.pages.setCurrentIndex(1)
        self.update_step()

    def process(self):
        specs = [(p.source, p.layout, m.get_decisions(), self.options.get(i)) for i, (p, m) in enumerate(zip(self.panes(), self.mappings))]
        def task(control):
            result = []
            try:
                for source, layout, mapping, options in specs:
                    result.append(process(self.root, self.state, source, layout, mapping, options, control))
                return result
            except BaseException:
                for session in result:
                    session.close()
                raise
        self.run_job(task, self.processed, "Transformando e validando os registros…")

    def processed(self, sessions):
        self.close_sessions()
        self.sessions = sessions
        for i, session in enumerate(sessions):
            session.ai_events = getattr(self.mappings[i], "ai_events", [])
        self.dirty = False
        messages = []
        for session in sessions:
            self.store.record(session.layout.label, session.stats(), "Processado")
            messages.extend(f"{p.severity} · {p.message}" for p in session.global_issues)
        messages.extend(f"{p.severity} · {p.message}" for p in validate_links(sessions[0], sessions[1] if len(sessions) > 1 else None))
        self.review.set_sessions(sessions, "\n".join(messages) or "Selecione uma linha para ver os valores originais, transformações e problemas.")
        self.pages.setCurrentIndex(2)
        errors = sum(s.stats()["errors"] for s in sessions)
        self.notice.setText(f"Processamento concluído. {errors} registros com erros. A exportação final é bloqueada enquanto houver erros; o relatório permanece disponível.")
        self.update_step()
        self.processed_event.emit(sessions)

    def correct(self, dataset, row, field, value):
        self.options.overrides[dataset][(row, field)] = value
        self.dirty = True
        self.notice.setText(f"Correção pendente: linha {row}, campo {field}. Clique em Revalidar correções para atualizar a prévia e liberar exportação.")
        self.next.setEnabled(False)
        self.report.setEnabled(False)

    def do_export(self, reports_only):
        if self.dirty or not self.sessions:
            self.notify("Revalide as correções antes de exportar.")
            return
        dest = QFileDialog.getExistingDirectory(self, "Salvar resultado em pasta de tratadas; relatórios acompanham a conversão", str(self.root))
        if not dest:
            return
        diagnostics = None
        if not reports_only:
            diagnostics = QFileDialog.getExistingDirectory(self, "Pasta de diagnósticos da empresa (Parciais / versão correspondente)", dest)
            if not diagnostics:
                return
        audit = QMessageBox.question(self, "Auditoria detalhada", "Incluir arquivo de auditoria com valores originais e transformados? Ele contém dados sensíveis. O relatório padrão não inclui esses valores.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes
        self.run_job(lambda control: export(self.sessions, dest, control, reports_only, audit, diagnostics), self.exported, "Gerando arquivos e relatórios…")

    def exported(self, path):
        for session in self.sessions:
            self.store.record(session.layout.label, session.stats(), "Exportado")
        self.notify(f"Arquivos salvos em:\n{path}\n\nIncluídos diagnóstico Markdown, relatório JSON e resumo TXT. Na exportação de planilhas, os relatórios também foram copiados para a pasta de diagnósticos escolhida.")
        self.exported_event.emit(path)

    def update_step(self):
        step = self.pages.currentIndex()
        self.back.setEnabled(step > 0)
        self.next.setText(["Continuar para mapeamento", "Processar e validar", "Exportar planilha"][step])
        self.next.setEnabled(not self.dirty or step != 2)
        self.ai_button.setVisible(step == 1)
        self.revalidate.setVisible(step == 2)
        self.report.setVisible(step == 2)
        self.report.setEnabled(not self.dirty)

    def ai_suggest(self):
        # Settings and provider service are loaded lazily; offline conversion has no network dependency.
        from app.ui.ai_actions import suggest_mapping
        suggest_mapping(self)

    def close_sessions(self):
        for session in self.sessions:
            session.close()
        self.sessions = []
