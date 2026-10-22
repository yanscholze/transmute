"""Biblioteca técnica separada dos trabalhos e da aparência, sem editar fontes."""
import json
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QHBoxLayout, QPlainTextEdit, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget

from app.core.catalog import discover, rules_path, workspace_config
from app.storage.workspace import import_model, save_config, save_rule_revision
from app.ui.common import button, text_label

FAMILIES = {"generic": "Genérico · regras declarativas", "clientes": "Clientes", "fornecedores": "Fornecedores", "produtos": "Produtos", "veiculos": "Veículos", "pagar": "Contas a pagar", "receber": "Contas a receber", "os": "Ordens de serviço", "vendas": "Vendas"}


class LibraryPane(QWidget):
    changed = Signal()

    def __init__(self, root, notify, start):
        super().__init__()
        self.root, self.notify = root, notify
        body = QVBoxLayout(self)
        body.setSpacing(16)
        top = QHBoxLayout()
        top.addWidget(text_label("Biblioteca de modelos", "title"), 1)
        body.addLayout(top)
        body.addWidget(text_label("Escolha seus modelos e mantenha as regras de trabalho acessíveis em um só lugar.", "subtitle"))
        body.addWidget(text_label("Planilhas de base", "section"))
        self.model_path = text_label("", "muted")
        body.addWidget(self.model_path)
        models = QHBoxLayout()
        models.addWidget(button("Apontar pasta de modelos…", self.choose_folder))
        models.addWidget(button("Importar planilhas…", self.upload))
        models.addWidget(button("Atualizar biblioteca", self.reload))
        models.addStretch()
        body.addLayout(models)
        self.grid = QTableWidget(0, 3)
        self.grid.setHorizontalHeaderLabels(["Modelo", "Regras aplicáveis", "Colunas"])
        self.grid.horizontalHeader().setStretchLastSection(True)
        self.grid.verticalHeader().hide()
        self.grid.setAlternatingRowColors(True)
        body.addWidget(self.grid, 1)
        rulesbar = QHBoxLayout()
        rulesbar.addWidget(text_label("Regras da biblioteca", "section"), 1)
        rulesbar.addWidget(button("Selecionar arquivo .md…", self.choose_rules))
        rulesbar.addWidget(button("Abrir e editar regras…", self.edit_rules))
        body.addLayout(rulesbar)
        self.rules_status = text_label("", "muted")
        body.addWidget(self.rules_status)
        body.addWidget(text_label("As referências originais permanecem intactas. Uploads e edições criam cópias locais. Regras em texto e operações executáveis precisam ser revisadas em conjunto.", "notice"))
        self.refresh()

    def refresh(self):
        config = workspace_config(self.root)
        self.model_path.setText("Pasta: " + config.get("models_dir", "(nenhuma)") + f" · {len(config.get('uploaded_models', []))} arquivos importados")
        self.rules_status.setText(str(rules_path(self.root)))
        try:
            layouts = discover(self.root)
        except Exception as error:
            layouts = []
            self.model_path.setText(self.model_path.text() + "\nNão foi possível ler esta biblioteca: " + str(error))
        self.grid.setRowCount(len(layouts))
        for index, layout in enumerate(layouts):
            for col, value in [(0, layout.label), (2, str(len(layout.headers)))]:
                cell = QTableWidgetItem(value)
                cell.setFlags(cell.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.grid.setItem(index, col, cell)
            combo = QComboBox()
            for key, label in FAMILIES.items():
                combo.addItem(label, key)
            combo.setCurrentIndex(combo.findData(layout.family))
            combo.currentIndexChanged.connect(lambda _, c=combo, p=layout.path: self.family_changed(p, c.currentData()))
            self.grid.setCellWidget(index, 1, combo)
        self.grid.setColumnWidth(0, 440)
        self.grid.setColumnWidth(1, 320)
        self.grid.resizeRowsToContents()

    def reload(self):
        try:
            self.refresh()
            self.changed.emit()
        except Exception as error:
            self.notify(str(error))

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Pasta das planilhas de base (leitura recursiva)")
        if folder:
            config = workspace_config(self.root)
            config.update(models_dir=folder, recognize_original_names=False)
            save_config(self.root, config)
            self.reload()

    def upload(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Importar modelos de destino", "", "Modelos Excel (*.xlsx)")
        try:
            for file in files:
                import_model(self.root, file)
            if files:
                self.reload()
        except Exception as error:
            self.notify(str(error))

    def family_changed(self, path, family):
        config = workspace_config(self.root)
        config.setdefault("families", {})[str(path)] = family
        save_config(self.root, config)
        self.changed.emit()

    def choose_rules(self):
        file, _ = QFileDialog.getOpenFileName(self, "Selecionar documentação de regras", "", "Regras Markdown (*.md)")
        if file:
            config = workspace_config(self.root)
            config["rules_path"] = file
            save_config(self.root, config)
            self.reload()
            self.edit_rules()

    def edit_rules(self):
        config = workspace_config(self.root)
        dialog = QDialog(self)
        dialog.setWindowTitle("Revisar e editar regras da biblioteca")
        dialog.resize(1000, 740)
        body = QVBoxLayout(dialog)
        body.addWidget(text_label("Edite o texto e o perfil executável correspondente. Ao salvar, será criada uma revisão local, sem alterar o arquivo escolhido.", "notice"))
        tabs = QTabWidget()
        markdown = QPlainTextEdit()
        try:
            markdown.setPlainText(rules_path(self.root).read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError):
            markdown.setPlainText("# Regras de conversão\n\nDescreva aqui as regras desta biblioteca.")
        executable = QPlainTextEdit()
        generic = {"version": 1, "source_sha256": "recalculado ao salvar", "max_total_rows": 10000, "enabled_modules": [], "rules": []}
        try:
            profile = json.loads(Path(config["profile_path"]).read_text(encoding="utf-8"))
        except (OSError, ValueError, KeyError):
            profile = generic
        executable.setPlainText(json.dumps(profile, ensure_ascii=False, indent=2))
        tabs.addTab(markdown, "Regras em texto (.md)")
        tabs.addTab(executable, "Regras executáveis (.json)")
        guide = QPlainTextEdit()
        guide.setReadOnly(True)
        guide.setPlainText('Módulos opcionais: contacts, clients, products, geography.\nModelo genérico só aplica regras declarativas e integridade técnica.\n\nOperações: required, digits, default, uppercase, enum, length, decimal, date.\nNunca use default para inventar documentos ou códigos ausentes.\nExemplo de regra:\n{\n  "id": "NOME_OBRIGATORIO",\n  "family": "generic",\n  "field": "Nome",\n  "operation": "required",\n  "severity": "ERRO"\n}\n\nfield deve corresponder exatamente a um cabeçalho do destino.\nfamily aceita * ou uma família da biblioteca.\nOperações e módulos estão documentados em docs/REGRAS.md.\nO hash do Markdown é atualizado somente ao aprovar esta revisão.\nNão há execução de Python, shell ou fórmulas no perfil.')
        tabs.addTab(guide, "Como configurar")
        body.addWidget(tabs, 1)
        body.addWidget(button("Começar perfil genérico sem regras de ERP predefinidas", lambda: executable.setPlainText(json.dumps(generic, ensure_ascii=False, indent=2))))
        ack = QCheckBox("Revisei a correspondência entre o texto e as operações executáveis")
        body.addWidget(ack)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Salvar revisão aprovada")
        buttons.rejected.connect(dialog.reject)
        def save():
            if not ack.isChecked():
                self.notify("Revise o texto e as regras executáveis e confirme a revisão antes de salvar.")
                return
            try:
                profile = json.loads(executable.toPlainText())
                save_rule_revision(self.root, markdown.toPlainText(), profile)
                dialog.accept()
                self.reload()
            except (ValueError, OSError) as error:
                self.notify(str(error))
        buttons.accepted.connect(save)
        body.addWidget(buttons)
        dialog.exec()
