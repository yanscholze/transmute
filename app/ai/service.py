"""Fallback somente entre provedores já consentidos; nenhuma tentativa altera dados."""
from app.ai.schema import parse
from app.models import Cancelled, Control


def suggestions(providers, data, output_schema, control=None):
    control = control or Control()
    control.check()
    attempts = []
    source_ids = [c["id"] for c in data["source_columns"]]
    for provider in providers:
        control.check()
        try:
            answer = provider.generate(data, output_schema, control)
            parsed = parse(answer, source_ids, data["target_columns"])
            control.check()
            event = {"provider": provider.name, "model": provider.model, "sent": "cabeçalhos conforme consentimento e até três estatísticas mascaradas por coluna", "count": len(parsed), "attempts": attempts}
            return parsed, event
        except Cancelled:
            raise
        except Exception:
            attempts.append({"provider": provider.name, "outcome": "failed_or_invalid_schema"})
    raise ValueError("Nenhum provedor configurado retornou sugestões válidas. Confira as configurações; o mapeamento manual continua disponível.")
