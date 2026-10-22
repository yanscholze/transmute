"""Configura provedores/cofre, testa com estrutura sintética e administra perfis locais."""
import json
import re

from PySide6.QtWidgets import QCheckBox, QComboBox, QFormLayout, QHBoxLayout, QLineEdit, QSpinBox, QVBoxLayout, QWidget

from app.ai.cli import CLIProvider, detect_clis
from app.ai.credentials import credentials
from app.ai.providers import APIProvider
from app.ai.schema import schema
from app.ai.service import suggestions
from app.ui.common import button, text_label


def configured_providers(config, state):
    names = [config["provider"]] + config.get("fallback", [])
    providers = []
    for name in names:
        model = config.get("models", {}).get(name, "")
        if model and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,119}", model):
            raise ValueError("Nome do modelo contém caracteres inválidos.")
        if name == "Claude CLI":
            providers.append(CLIProvider(state / "cli", model, config.get("timeout", 30)))
        else:
            providers.append(APIProvider(name, model, credentials.get(name), config.get("timeout", 30)))
    return providers


class SettingsPane(QWidget):
    def __init__(self, store, state, run_job, notify):
        super().__init__()
        self.store, self.state, self.run_job, self.notify = store, state, run_job, notify
        self.config = store.setting("ai", {"enabled": False, "provider": "OpenAI", "models": {}, "timeout": 30, "fallback": []})
        body = QVBoxLayout(self)
        body.setSpacing(14)
        body.addWidget(text_label("IA e perfis", "title"))
        body.addWidget(text_label("A conversão determinística funciona sem internet e sem credenciais.", "muted"))
        self.enabled = QCheckBox("Habilitar sugestões de mapeamento com IA")
        self.enabled.setChecked(self.config.get("enabled", False))
        body.addWidget(self.enabled)
        form = QFormLayout()
        self.provider = QComboBox()
        self.provider.addItems(["OpenAI", "Gemini", "Claude", "Claude CLI"])
        self.provider.setCurrentText(self.config["provider"])
        form.addRow("Provedor principal", self.provider)
        self.model = QLineEdit(self.config.get("models", {}).get(self.provider.currentText(), ""))
        self.model.setPlaceholderText("ID do modelo disponível na sua conta")
        form.addRow("Modelo", self.model)
        self.key = QLineEdit()
        self.key.setEchoMode(QLineEdit.EchoMode.Password)
        self.key.setPlaceholderText("Nova chave; deixe vazio para manter a existente")
        form.addRow("Chave de API", self.key)
        self.persist = QCheckBox("Guardar no cofre seguro do sistema; se indisponível, somente memória")
        form.addRow("Credenciais", self.persist)
        self.timeout = QSpinBox()
        self.timeout.setRange(5, 120)
        self.timeout.setValue(self.config.get("timeout", 30))
        self.timeout.setSuffix(" segundos")
        form.addRow("Timeout total", self.timeout)
        self.fallback = QLineEdit(", ".join(self.config.get("fallback", [])))
        self.fallback.setPlaceholderText("Opcional: Gemini, Claude (configure chave/modelo de cada um antes)")
        form.addRow("Fallback consentido, em ordem", self.fallback)
        body.addLayout(form)
        actions = QHBoxLayout()
        actions.addWidget(button("Salvar configurações", self.save, True))
        actions.addWidget(button("Testar conexão…", self.test_connection))
        actions.addWidget(button("Remover chave deste provedor", self.delete_key))
        actions.addStretch()
        body.addLayout(actions)
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

    def provider_changed(self, name):
        self.config.setdefault("models", {})[self.previous_provider] = self.model.text().strip()
        self.model.setText(self.config.get("models", {}).get(name, ""))
        self.key.clear()
        self.previous_provider = name

    def save(self, quiet=False):
        name = self.provider.currentText()
        self.config.setdefault("models", {})[name] = self.model.text().strip()
        fallback = [s.strip() for s in self.fallback.text().split(",") if s.strip()]
        if any(p not in ["OpenAI", "Gemini", "Claude", "Claude CLI"] for p in fallback) or name in fallback or len(fallback) != len(set(fallback)):
            self.notify("Fallback precisa usar nomes de provedores distintos, diferentes do principal.")
            return False
        self.config.update(enabled=self.enabled.isChecked(), provider=name, timeout=self.timeout.value(), fallback=fallback)
        try:
            credentials.set(name, self.key.text(), self.persist.isChecked())
        except ValueError as error:
            self.notify(str(error))
        self.key.clear()
        self.store.set_setting("ai", self.config)
        if not quiet:
            self.notify("Configurações salvas. Chaves, quando presentes, ficam no cofre seguro ou apenas na memória desta sessão.")
        return True

    def test_connection(self):
        from PySide6.QtWidgets import QMessageBox
        if not self.save(True):
            return
        if QMessageBox.question(self, "Teste de conexão", "Enviar somente um cabeçalho sintético e um schema aos provedores configurados? Pode consumir cota. Nenhuma base será enviada.", defaultButton=QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        data = {"source_columns": [{"id": "C1", "header": "UF", "masked_samples": []}], "target_columns": ["UF"]}
        try:
            providers = configured_providers(self.config, self.state)
        except ValueError as error:
            self.notify(str(error))
            return
        self.run_job(lambda control: suggestions(providers, data, schema(["C1"], ["UF"]), control), lambda result: self.notify(f"Conexão e schema válidos com {result[1]['provider']}."), "Testando conexão com dados sintéticos…")

    def delete_key(self):
        credentials.delete(self.provider.currentText())
        self.key.clear()
        self.notify("Chave removida da sessão e do cofre, quando existente.")

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
