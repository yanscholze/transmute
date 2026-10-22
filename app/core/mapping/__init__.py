"""Mapeamento determinístico: igualdade, aliases revisados e semelhança incerta.

Confiança é metadado de sugestão, não permissão para resolver conflitos.
Diferença de caixa entre os campos de natureza/código do item é significativa.
"""
import re
import unicodedata
from collections import Counter
from difflib import SequenceMatcher

from app.models import Decision


def norm(value):
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower())


ALIASES = {
    "Razão Social / Nome": ["nome", "nome cliente", "razao social", "razao social cliente", "nome fornecedor"],
    "CPF/CNPJ": ["cpf", "cnpj", "cpf cnpj", "documento fiscal"],
    "Inscrição Estadual": ["ie"], "RG": ["rg", "ie/rg", "ie/eg"],
    "Inscrição Municipal": ["im"], "E-mail": ["email", "correio eletronico"],
    "Telefone": ["fone", "telefone principal"], "Celular": ["cel", "whatsapp"],
    "Município": ["cidade"], "UF": ["estado", "sigla estado"],
    "CEP": ["codigo postal"], "Número da OS (externo)": ["numero os", "os", "nro os"],
    "Número da venda (externo)": ["numero venda", "nro venda"],
    "Descrição": ["nome produto", "descricao produto", "nome servico"],
    "Produto/Serviço (identificação)": ["produto servico", "servico", "produto"],
    "Produto (identificação)": ["produto"], "Cliente (identificação)": ["cliente"],
    "Fornecedor (identificação)": ["fornecedor"], "Quilometragem": ["km"],
    "Data de abertura": ["data abertura"], "Valor unitário": ["preco unitario"],
    "Tipo do item": ["natureza", "natureza do item"],
    "Tipo do Item": ["codigo tipo do item", "codigo sped", "tipo item sped"],
}


def targets(layout):
    result = list(layout.headers)
    if layout.family in {"clientes", "fornecedores"} and "RG" not in result:
        result.append("RG")
    if layout.family == "produtos" and "Tipo do Item" not in result:
        result.append("Tipo do Item")
    return result


def suggest(source, layout, saved=None):
    saved = saved or {}
    dest = targets(layout)
    counts = Counter(norm(h) for h in source.headers)
    decisions = []
    used = set()
    for sid, header in zip(source.ids, source.headers):
        chosen, confidence, origin = "", 0., "Não utilizado"
        # Case is significant for the two product fields; never collapse them.
        if header in dest:
            chosen, confidence, origin = header, 1., "Exato"
        elif header in saved and saved[header] in dest:
            chosen, confidence, origin = saved[header], .85, "Histórico local"
        else:
            matches = [d for d in dest if norm(header) == norm(d) or norm(header) in [norm(a) for a in ALIASES.get(d, [])]]
            if len(matches) == 1:
                chosen, confidence, origin = matches[0], .96, "Regra de cabeçalho"
            elif not matches:
                ratios = sorted(((SequenceMatcher(None, norm(header), norm(d)).ratio(), d) for d in dest), reverse=True)
                if ratios and ratios[0][0] >= .72 and (len(ratios) == 1 or ratios[0][0] - ratios[1][0] > .1):
                    confidence, chosen = ratios[0]
                    origin = "Semelhança · revisar"
        if chosen in used or counts[norm(header)] > 1:
            confidence = min(confidence, .5)
        if chosen:
            used.add(chosen)
        decisions.append(Decision(sid, chosen, confidence, origin, confidence >= .95))
    return decisions


def validate_mapping(source, layout, decisions):
    """Garanta colunas existentes, destino único e confirmação de sugestões."""
    seen = set()
    for d in decisions:
        if d.source not in source.ids or (d.target and d.target not in targets(layout)):
            raise ValueError("Mapeamento contém coluna inexistente.")
        if d.source in seen:
            raise ValueError("Coluna de origem repetida no mapeamento.")
        seen.add(d.source)
        if d.target and not d.confirmed:
            raise ValueError(f"Confirme a sugestão para {d.target} antes de processar.")
    mapped = [d.target for d in decisions if d.target]
    if len(mapped) != len(set(mapped)):
        raise ValueError("Duas origens apontam ao mesmo destino. Escolha explicitamente uma delas.")
    if not mapped:
        raise ValueError("Mapeie ao menos uma coluna.")
