"""Configura provedores/cofre, testa com estrutura sintética e administra perfis locais."""
import json

from PySide6.QtWidgets import QCheckBox, QComboBox, QFileDialog, QFormLayout, QHBoxLayout, QLineEdit, QScrollArea, QSpinBox, QVBoxLayout, QWidget

from app.ai.cli import detect_clis
from app.ai.configuration import MODEL_ENV, configured_providers, model_for, readiness
from app.ai.credentials import ENVIRONMENT_KEYS, credentials
from app.ai.environment import read_environment_file
from app.ai.schema import schema
from app.ai.service import suggestions
from app.ui.common import button, text_label


class SettingsPane(QWidget):
    def __init__(self, store, state, run_job, notify):
        super().__init__()
        self.store, self.state, self.run_job, self.notify = store, state, run_job, notify
        self.config = store.setting("ai", {"enabled": False, "provider": "OpenAI", "models": {}, "timeout": 60, "fallback": []})
        self.key_drafts = {}
        outer = QVBoxLayout(self)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        inner = QWidget()
        self.scroll.setWidget(inner)
        outer.addWidget(self.scroll, 1)
        body = QVBoxLayout(inner)
        body.setSpacing(14)
        body.addWidget(text_label("IA e perfis", "title"))
        body.addWidget(text_label("Configure OpenAI, Gemini e Claude separadamente. O Estúdio usa a IA para planejar e auditar as conversões.", "muted"))
        self.enabled = QCheckBox("Habilitar IA neste aplicativo")
        self.enabled.setChecked(self.config.get("enabled", False))
        body.addWidget(self.enabled)
        form = QFormLayout()
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.provider = QComboBox()
        self.provider.addItems(["OpenAI", "Gemini", "Claude", "Claude CLI"])
        self.provider.setCurrentText(self.config["provider"])
        form.addRow("Configurar credencial/modelo de", self.provider)
        self.primary = QComboBox()
        self.primary.addItems(["OpenAI", "Gemini", "Claude", "Claude CLI"])
        self.primary.setCurrentText(self.config["provider"])
        form.addRow("Usar como provedor principal", self.primary)
        self.model = QLineEdit(model_for(self.config, self.provider.currentText()))
        self.model.setPlaceholderText("ID do modelo disponível na sua conta")
        form.addRow("Modelo", self.model)
        self.key = QLineEdit()
        self.key.setEchoMode(QLineEdit.EchoMode.Password)
        self.key.setPlaceholderText("Nova chave; deixe vazio para manter a existente")
        form.addRow("Chave de API", self.key)
        # Native Windows checkboxes do not wrap their text. Keep the control
        # short and put the explanation in a wrapping label below the form.
        self.persist = QCheckBox("Guardar no cofre seguro do sistema")
        form.addRow("Credenciais", self.persist)
        self.timeout = QSpinBox()
        self.timeout.setRange(5, 300)
        self.timeout.setValue(self.config.get("timeout", 60))
        self.timeout.setSuffix(" segundos")
        form.addRow("Timeout total", self.timeout)
        self.fallback = QLineEdit(", ".join(self.config.get("fallback", [])))
        self.fallback.setPlaceholderText("Opcional: Gemini, Claude (configure chave/modelo de cada um antes)")
        form.addRow("Fallback consentido, em ordem", self.fallback)
        body.addLayout(form)
        body.addWidget(text_label("Sem um cofre disponível, as chaves digitadas ficam somente na memória desta sessão.", "muted"))
        self.readiness = text_label("", "notice")
        body.addWidget(self.readiness)
        body.addWidget(button("Importar credenciais de arquivo local…", self.import_credentials))
        actions = QHBoxLayout()
        self.save_button = button("Salvar configurações", self.save, True)
        actions.addWidget(self.save_button)
        actions.addWidget(button("Testar este provedor…", self.test_connection))
        actions.addWidget(button("Remover chave deste provedor", self.delete_key))
        actions.addStretch()
        # Credentials/controls stay reachable even when the form is scrolled.
        outer.addLayout(actions)
        body.addWidget(text_label("Cada consulta exibe o conteúdo que será enviado e solicita consentimento. Fallback envia o mesmo conteúdo apenas aos provedores listados. Chaves nunca são gravadas no arquivo de configuração.", "notice"))
        body.addWidget(button("Detectar ferramentas CLI instaladas", self.detect))
        self.cli_status = text_label("CLI é opcional. Detecção não comprova login nem conectividade.", "muted")
        body.addWidget(self.cli_status)
        body.addWidget(text_label("Mapeamentos locais salvos", "section"))
        row = QHBoxLayout()
        self.profiles = QComboBox()
        row.addWidget(self.profiles, 1)
        row.addWidget(button("Ver perfil", self.view_profile))
        row.addWidget(button("Remover perfil", self.remove_profile))
        body.addLayout(row)
        body.addStretch()
        self.previous_provider = self.provider.currentText()
        self.provider.currentTextChanged.connect(self.provider_changed)
        self.refresh_profiles()
        self.refresh_readiness()

    def provider_changed(self, name):
        self.config.setdefault("models", {})[self.previous_provider] = self.model.text().strip()
        self.key_drafts[self.previous_provider] = self.key.text()
        self.model.setText(model_for(self.config, name))
        self.key.setText(self.key_drafts.get(name, ""))
        self.previous_provider = name
        self.refresh_readiness()

    def import_credentials(self):
        path, _ = QFileDialog.getOpenFileName(self, "Importar chaves/modelos localmente (sem envio à internet)", "", "Arquivos de ambiente (*)")
        if not path:
            return
        self.key_drafts[self.provider.currentText()] = self.key.text()
        self.config.setdefault("models", {})[self.provider.currentText()] = self.model.text().strip()
        values = read_environment_file(path)
        found = []
        for provider, variables in ENVIRONMENT_KEYS.items():
            secret = next((values[v] for v in variables if values.get(v)), "")
            if secret:
                self.key_drafts[provider] = secret
                found.append(provider)
            if values.get(MODEL_ENV[provider]):
                self.config.setdefault("models", {})[provider] = values[MODEL_ENV[provider]]
        if not found:
            self.notify("Nenhuma chave reconhecida. O arquivo deve conter OPENAI_API_KEY, GEMINI_API_KEY/GOOGLE_API_KEY ou ANTHROPIC_API_KEY. Arquivos grandes, links simbólicos e texto inválido não são importados.")
            return
        self.key.setText(self.key_drafts.get(self.provider.currentText(), ""))
        self.model.setText(model_for(self.config, self.provider.currentText()))
        if self.save(quiet=True):
            self.notify("Credenciais importadas localmente para: " + ", ".join(found) + ". Escolha o provedor principal e use Testar este provedor. Nenhum teste externo foi executado automaticamente.")

    def refresh_readiness(self):
        self.readiness.setText("\n".join(f"{r['provider']}: modelo {'configurado' if r['model'] else 'pendente'} · chave {'disponível' if r['credential'] else 'pendente'}" for r in readiness(self.config)) + "\nPresença de configuração não comprova conexão. Use Testar conexão para validar sua conta. Variáveis aceitas: OPENAI_API_KEY, GEMINI_API_KEY e ANTHROPIC_API_KEY.")

    def save(self, quiet=False):
        name = self.provider.currentText()
        primary = self.primary.currentText()
        self.config.setdefault("models", {})[name] = self.model.text().strip()
        fallback = [s.strip() for s in self.fallback.text().split(",") if s.strip()]
        if any(p not in ["OpenAI", "Gemini", "Claude", "Claude CLI"] for p in fallback) or primary in fallback or len(fallback) != len(set(fallback)):
            self.notify("Fallback precisa usar nomes de provedores distintos, diferentes do principal.")
            return False
        self.config.update(enabled=self.enabled.isChecked(), provider=primary, timeout=self.timeout.value(), fallback=fallback)
        drafts = {**self.key_drafts, name: self.key.text()}
        for provider, secret in drafts.items():
            if provider != "Claude CLI":
                try:
                    credentials.set(provider, secret, self.persist.isChecked())
                except ValueError as error:
                    self.notify(provider + ": " + str(error))
        self.key.clear()
        self.key_drafts.clear()
        self.store.set_setting("ai", self.config)
        self.refresh_readiness()
        if not quiet:
            self.notify("Configurações salvas. Chaves, quando presentes, ficam no cofre seguro ou apenas na memória desta sessão.")
        return True

    def test_connection(self):
        from PySide6.QtWidgets import QMessageBox
        if not self.save(True):
            return
        if QMessageBox.question(self, "Teste de conexão", "Enviar somente um cabeçalho sintético e um schema a " + self.provider.currentText() + "? Pode consumir cota. Nenhuma base será enviada.", defaultButton=QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        data = {"source_columns": [{"id": "C1", "header": "UF", "masked_samples": []}], "target_columns": ["UF"]}
        try:
            providers = configured_providers({**self.config, "provider": self.provider.currentText(), "fallback": []}, self.state)
        except ValueError as error:
            self.notify(str(error))
            return
        self.run_job(lambda control: suggestions(providers, data, schema(["C1"], ["UF"]), control), lambda result: self.notify(f"Conexão e schema válidos com {result[1]['provider']}."), "Testando conexão com dados sintéticos…")

    def delete_key(self):
        credentials.delete(self.provider.currentText())
        self.key_drafts.pop(self.provider.currentText(), None)
        self.key.clear()
        self.refresh_readiness()
        self.notify("Chave removida da sessão e do cofre, quando existente. Variáveis de ambiente são administradas fora do app e continuam disponíveis quando definidas.")

    def detect(self):
        self.run_job(detect_clis, lambda result: self.cli_status.setText("\n".join(f"{x['name']}: {x['reason']}" for x in result)), "Inspecionando --help das ferramentas CLI…")

    def refresh_profiles(self):
        self.saved_profiles = self.store.profiles()
        self.profiles.clear()
        for ident, name, _, _ in self.saved_profiles:
            self.profiles.addItem(f"{ident} · {name}", ident)

    def view_profile(self):
        if self.profiles.currentIndex() >= 0:
            self.notify(json.dumps(self.saved_profiles[self.profiles.currentIndex()][3], ensure_ascii=False, indent=2))

    def remove_profile(self):
        if self.profiles.currentData() is not None:
            self.store.delete_profile(self.profiles.currentData())
            self.refresh_profiles()
