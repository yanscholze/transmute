"""Única fronteira de envio externo: conteúdo de célula vira estatística, nunca amostra literal."""
import re

from app.core.mapping import ALIASES, norm, targets


def shape(value):
    """No literal cell content leaves this boundary."""
    if not value:
        return {"kind": "empty", "length": 0}
    kind = "digits" if re.fullmatch(r"[0-9]+", value) else "email-like" if "@" in value else "mixed" if any(c.isdigit() for c in value) else "text"
    return {"kind": kind, "length": len(value), "digits": sum(c.isdigit() for c in value)}


def payload(source, layout, sample, include_headers=False):
    safe_names = {norm(v): key for key, names in ALIASES.items() for v in [key, *names]}
    safe_names.update({norm(t): t for t in targets(layout)})
    columns = []
    for sid, header in zip(source.ids, source.headers):
        label = header[:120] if include_headers else header if header in targets(layout) else safe_names.get(norm(header), "[cabeçalho não reconhecido]")
        examples = [shape(raw[sid].text) for _, raw, _ in sample if raw and sid in raw][:3]
        columns.append({"id": sid, "header": label, "masked_samples": examples})
    return {"source_columns": columns, "target_columns": targets(layout), "purpose": "mapping_suggestions_only"}
