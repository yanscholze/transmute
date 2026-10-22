"""Diálogo de consentimento com payload exato e aplicação de sugestões não confirmadas."""
import json

from PySide6.QtWidgets import QCheckBox, QDialog, QDialogButtonBox, QTextEdit, QVBoxLayout

from app.ai.sanitization import payload
from app.ai.schema import schema
from app.ai.service import suggestions
from app.core.mapping import targets
from app.models import Decision
from app.ui.common import text_label
from app.ui.settings import configured_providers


def suggest_mapping(conversion):
    config = conversion.store.setting("ai", {})
    if not config.get("enabled"):
        conversion.notify("Ative IA e configure um provedor em Configurações. O mapeamento manual está disponível sem IA.")
        return
    index = conversion.map_tabs.currentIndex()
    if index >= len(conversion.mappings):
        conversion.notify("Selecione a aba de mapeamento da base que deseja analisar.")
        return
    mapping = conversion.mappings[index]
    dialog = QDialog(conversion)
    dialog.setWindowTitle("Revisar envio externo")
    dialog.resize(760, 560)
    body = QVBoxLayout(dialog)
    body.addWidget(text_label("Serão enviados os dados abaixo ao provedor e aos fallbacks configurados: " + ", ".join([config["provider"], *config.get("fallback", [])])))
    raw_headers = QCheckBox("Incluir cabeçalhos originais (podem conter informações do cliente)")
    body.addWidget(raw_headers)
    preview = QTextEdit()
    preview.setReadOnly(True)
    body.addWidget(preview, 1)
    def refresh():
        data = payload(mapping.source, mapping.layout, mapping.sample, raw_headers.isChecked())
        preview.setPlainText(json.dumps(data, ensure_ascii=False, indent=2))
    raw_headers.toggled.connect(refresh)
    refresh()
    body.addWidget(text_label("Valores de células são substituídos por tipo, comprimento e quantidade de dígitos. A IA só pode sugerir destinos. Toda sugestão exige confirmação.", "notice"))
    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
    buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Autorizar envio e consultar")
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    body.addWidget(buttons)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return
    data = payload(mapping.source, mapping.layout, mapping.sample, raw_headers.isChecked())
    try:
        providers = configured_providers(config, conversion.state)
    except ValueError as error:
        conversion.notify(str(error))
        return
    def applied(result):
        values, event = result
        # Keep existing confirmed matches; never silently replace human decisions.
        current = mapping.get_decisions()
        used_targets = {d.target for d in current if d.confirmed and d.target}
        count = 0
        for value in values:
            pos = mapping.source.ids.index(value["source_column"])
            if current[pos].confirmed or value["target_column"] in used_targets:
                continue
            current[pos] = Decision(value["source_column"], value["target_column"], value["confidence"], f"IA · {event['provider']}", False, value["reason"])
            used_targets.add(value["target_column"])
            count += 1
        mapping.decisions = current
        mapping.ai_events = getattr(mapping, "ai_events", []) + [event]
        mapping.render()
        conversion.notify(f"{count} sugestões apresentadas. Confira e confirme cada uma antes de processar.")
    conversion.run_job(lambda control: suggestions(providers, data, schema(mapping.source.ids, targets(mapping.layout)), control), applied, "Consultando sugestões de mapeamento…")
