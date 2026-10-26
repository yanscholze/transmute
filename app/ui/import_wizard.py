"""Assistente: nome/categorias → arquivos classificados → regras e início.

Cada arquivo tem título, categoria e destino visíveis. Os originais são
referenciados, não movidos nem enviados a serviços externos.
"""
import uuid
from dataclasses import asdict
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QFileDialog, QFormLayout, QGridLayout, QHBoxLayout, QLineEdit, QStackedWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from app.storage.imports import FAMILIES
from app.ui.common import button, text_label
from app.ui.options import OptionsPane


class ImportWizard(QWidget):
    created = Signal(object)
    cancelled = Signal()

    def __init__(self, imports, layouts, notify, run_job=None):
        super().__init__()
        self.imports, self.layouts, self.notify = imports, layouts, notify
        self.run_job = run_job
        self.files, self.controls = [], []
        self.setAcceptDrops(True)
        body = QVBoxLayout(self)
        body.setSpacing(16)
        body.addWidget(text_label("Nova importação", "title"))
        self.steps = text_label("1  Identificação     /     2  Arquivos     /     3  Conferência", "steps")
        body.addWidget(self.steps)
        self.pages = QStackedWidget()
        self.pages.addWidget(self.identification())
        self.pages.addWidget(self.file_page())
        self.options = OptionsPane()
        self.options.columns.setCurrentIndex(1)
        self.pages.addWidget(self.options)
        body.addWidget(self.pages, 1)
        self.feedback = text_label("Escolha somente as tabelas que fazem parte deste trabalho.", "muted")
        body.addWidget(self.feedback)
        actions = QHBoxLayout()
        self.back = button("Cancelar", self.previous)
        self.next = button("Escolher arquivos", self.advance, True)
        actions.addWidget(self.back)
        actions.addStretch()
        actions.addWidget(self.next)
        body.addLayout(actions)

    def identification(self):
        page = QWidget()
        box = QVBoxLayout(page)
        box.setSpacing(20)
        form = QFormLayout()
        self.name = QLineEdit()
        self.name.setMaxLength(120)
        self.name.setPlaceholderText("Ex.: Cliente — migração de outubro")
        self.name.setAccessibleName("Nome da importação")
        form.addRow("Nome da importação", self.name)
        box.addLayout(form)
        self.studio_mode = QCheckBox("Planejar no Estúdio IA — fontes juntas, separadas e cruzamentos")
        self.studio_mode.setChecked(True)
        self.studio_mode.setToolTip("O projeto abre antes da transformação. Você define as regras, revisa e aprova o plano.")
        box.addWidget(self.studio_mode)
        box.addWidget(text_label("Quais tabelas serão importadas?", "section"))
        grid = QGridLayout()
        self.categories = {}
        for index, (key, label) in enumerate(FAMILIES.items()):
            check = QCheckBox(label)
            check.setObjectName("categoryCard")
            check.setToolTip("Incluir " + label.lower() + " nesta importação")
            check.setMinimumHeight(46)
            grid.addWidget(check, index // 2, index % 2)
            self.categories[key] = check
        box.addLayout(grid)
        box.addStretch()
        return page

    def selected_categories(self):
        return [key for key, check in self.categories.items() if check.isChecked()]

    def file_page(self):
        page = QWidget()
        box = QVBoxLayout(page)
        box.addWidget(text_label("Adicione os arquivos recebidos", "section"))
        box.addWidget(text_label("Arraste vários arquivos ou selecione-os. Dê um título e confira a categoria e o modelo de saída de cada um. Todas as abas e tabelas reconhecidas serão incluídas.", "drop"))
        actions = QHBoxLayout()
        actions.addWidget(button("Adicionar planilhas ou PDFs…", self.browse))
        actions.addWidget(button("Escolher tabelas de uma pasta…", self.browse_folder))
        actions.addWidget(button("Remover selecionado", self.remove))
        actions.addStretch()
        box.addLayout(actions)
        self.grid = QTableWidget(0, 5)
        self.grid.setHorizontalHeaderLabels(["Arquivo recebido", "Título", "Categoria", "Modelo de saída", "Finalidade"])
        self.grid.verticalHeader().hide()
        self.grid.setAlternatingRowColors(True)
        box.addWidget(self.grid, 1)
        box.addWidget(text_label("Fonte de dados será convertida. Documento de apoio fica associado ao trabalho para conferência, sem gerar registros.", "muted"))
        return page

    def browse_folder(self):
        from app.studio.catalog import folder_tables
        folder = QFileDialog.getExistingDirectory(self, "Pasta dos arquivos recebidos")
        if not folder:
            return
        def task(control):
            return folder_tables(folder, control)
        if self.run_job:
            self.run_job(task, self.pick_tables, "Lendo abas e tabelas da pasta…")
        else:
            try:
                self.pick_tables(task(None))
            except (ValueError, OSError) as error:
                self.feedback.setText(str(error))

    def pick_tables(self, entries):
        from app.ui.source_picker import SourcePicker
        self.snapshot()
        dialog = SourcePicker(entries, self)
        if dialog.exec() == SourcePicker.DialogCode.Accepted:
            existing = {(f["path"], f.get("source_sheet", "")) for f in self.files}
            for entry in dialog.selected:
                if (entry["path"], entry["source_sheet"]) not in existing:
                    self.files.append({k: v for k, v in {**entry, "family": self.selected_categories()[0]}.items() if k != "error"})
            self.render_files()

    def browse(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Selecionar arquivos recebidos", "", "Planilhas e PDFs (*.xlsx *.xls *.csv *.tsv *.pdf)")
        self.add_files(files)

    def add_files(self, files):
        if self.pages.currentIndex() != 1:
            return
        self.snapshot()
        for file in files:
            path = Path(file).resolve()
            if path.suffix.lower() not in {".xlsx", ".xls", ".csv", ".tsv", ".pdf"} or not path.is_file():
                self.feedback.setText("Adicione arquivos XLSX, XLS, CSV ou PDF existentes.")
                continue
            self.files.append({"path": str(path), "title": path.stem, "family": self.selected_categories()[0]})
        self.render_files()

    def snapshot(self):
        for i, controls in enumerate(self.controls):
            if i >= len(self.files):
                break
            category, layout, role = controls
            chosen = layout.currentData()
            self.files[i].update(title=self.grid.item(i, 1).text(), family=category.currentData(),
                                 layout_path=str(chosen.path) if chosen else "", layout_sheet=chosen.sheet if chosen else "", role=role.currentData())

    def render_files(self):
        self.grid.setRowCount(len(self.files))
        self.controls = []
        for row, item in enumerate(self.files):
            filename = QTableWidgetItem(Path(item["path"]).name)
            filename.setFlags(filename.flags() & ~Qt.ItemFlag.ItemIsEditable)
            filename.setToolTip(item["path"])
            self.grid.setItem(row, 0, filename)
            self.grid.setItem(row, 1, QTableWidgetItem(item["title"]))
            category, model, role = QComboBox(), QComboBox(), QComboBox()
            for key in self.selected_categories():
                category.addItem(FAMILIES[key], key)
            category.setCurrentIndex(max(0, category.findData(item["family"])))
            role.addItem("Converter", "source")
            role.addItem("Apoio", "reference")
            role.setCurrentIndex(max(0, role.findData(item.get("role", "source"))))
            self.controls.append((category, model, role))
            self.populate_models(row, item)
            category.currentIndexChanged.connect(lambda _, r=row: self.populate_models(r))
            self.grid.setCellWidget(row, 2, category)
            self.grid.setCellWidget(row, 3, model)
            self.grid.setCellWidget(row, 4, role)
        for col, width in enumerate([220, 200, 170, 300, 115]):
            self.grid.setColumnWidth(col, width)
        self.grid.resizeRowsToContents()

    def populate_models(self, row, previous=None):
        category, combo, _ = self.controls[row]
        combo.clear()
        choices = [layout for layout in self.layouts if layout.family == category.currentData()]
        combo.addItem("Selecione o modelo…", None)
        for layout in choices:
            combo.addItem(layout.label, layout)
        if previous and previous.get("layout_path"):
            for index, layout in enumerate(choices, 1):
                if str(layout.path) == previous["layout_path"] and layout.sheet == previous["layout_sheet"]:
                    combo.setCurrentIndex(index)
                    return
        # Equivalent versions can share a safe, visible default. Different shapes require choice.
        if choices and len({(tuple(layout.headers), layout.variant) for layout in choices}) == 1:
            combo.setCurrentIndex(1)

    def remove(self):
        row = self.grid.currentRow()
        if row >= 0:
            self.snapshot()
            self.files.pop(row)
            self.render_files()

    def previous(self):
        index = self.pages.currentIndex()
        if index == 0:
            self.cancelled.emit()
            return
        if index == 1:
            self.snapshot()
        self.pages.setCurrentIndex(index - 1)
        self.update_step()

    def advance(self):
        step = self.pages.currentIndex()
        if step == 0:
            if not self.name.text().strip() or not self.selected_categories():
                self.feedback.setText("Informe o nome da importação e selecione ao menos uma tabela.")
                self.name.setFocus()
                return
            self.files = [f for f in self.files if f["family"] in self.selected_categories()]
            self.render_files()
        elif step == 1:
            self.snapshot()
            if not self.files or any(not f["title"].strip() or (not self.studio_mode.isChecked() and f["role"] != "reference" and not f["layout_path"]) for f in self.files):
                self.feedback.setText("Adicione arquivos e preencha título, categoria e modelo de saída para as fontes de dados.")
                return
            missing = set(self.selected_categories()) - {f["family"] for f in self.files}
            if missing and not self.studio_mode.isChecked():
                self.feedback.setText("Faltam arquivos para: " + ", ".join(FAMILIES[k] for k in missing))
                return
            self.options.configure_categories(self.selected_categories(), any(f["path"].lower().endswith(".pdf") for f in self.files))
        else:
            options = self.options.get()
            if not self.studio_mode.isChecked() and (not options.acknowledge_conflicts or ("clientes" in self.selected_categories() and not options.active)):
                self.feedback.setText("Confirme as regras da importação e a opção ATIVO quando houver clientes.")
                return
            try:
                attachments = [{**f, "id": uuid.uuid4().hex, "status": "Aguardando", "group": "principal"} for f in self.files]
                job = self.imports.create(self.name.text(), self.selected_categories(), attachments, asdict(options), "studio" if self.studio_mode.isChecked() else "classic")
                self.created.emit(job)
            except ValueError as error:
                self.feedback.setText(str(error))
            return
        self.pages.setCurrentIndex(step + 1)
        self.update_step()

    def update_step(self):
        step = self.pages.currentIndex()
        self.back.setText("Cancelar" if step == 0 else "Voltar")
        self.next.setText(["Escolher arquivos", "Conferir e iniciar", "Iniciar importação"][step])
        if step == 2 and self.studio_mode.isChecked():
            self.next.setText("Abrir Estúdio de conversão")
        self.steps.setText(f"Etapa {step + 1} de 3 · " + ["Nome e tabelas", "Arquivos por categoria", "Regras desta importação"][step])
        self.feedback.setText(["Escolha as tabelas que fazem parte deste trabalho.", "Cada arquivo permanece na origem; os dados não são enviados à internet.", "O processamento é local. Pendências serão mostradas para revisão antes da exportação."][step])

    def dragEnterEvent(self, event):
        if self.pages.currentIndex() == 1 and event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        self.snapshot()
        self.add_files([u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()])
        event.acceptProposedAction()
