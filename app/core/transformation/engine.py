"""Regras de domínio confirmadas no Markdown e trilha antes/depois.

O motor recebe apenas dados/opções, sem UI, rede ou escrita na origem. Toda
mutação de saída passa por put() para carregar uma regra identificável.
"""
import re

from app.core.mapping import norm, targets
from app.core.validation.values import ITEM_CODES, identifier, money_field, validate_values
from app.models import Change, Issue


def transform(raw, source, layout, decisions, options, row, profile=None):
    profile = profile or {}
    modules = profile.get("enabled_modules", ["contacts", "clients", "products", "geography"])
    values = dict.fromkeys(targets(layout), "")
    issues, changes = [], []
    origin = {}

    def put(field, value, rule):
        before = values.get(field, "")
        if value != before:
            changes.append(Change(field, before, value, rule))
            values[field] = value

    for decision in decisions:
        if not decision.target:
            continue
        field = decision.target
        cell = raw.get(decision.source)
        if cell is None:
            continue
        origin[field] = source.headers[source.ids.index(decision.source)]
        values[field] = cell.text
        correction = options.overrides.get((row, field))
        if correction is not None:
            put(field, correction, "REVISAO_USUARIO")
        if cell.kind in {"formula", "error"} and correction is None:
            issues.append(Issue("ERRO", "CELULA_ORIGEM", field, cell.note))
        if identifier(field) and cell.text and cell.kind == "number" and correction is None:
            severity = "AVISO" if options.numeric_identifiers_confirmed and len(cell.text) <= 15 else "ERRO"
            issues.append(Issue(severity, "IDENTIFICADOR_NUMERICO", field, "Identificador numérico na origem; confira no original, pois zeros ou precisão podem ter sido perdidos."))
        if cell.kind == "formatted_number":
            changes.append(Change(field, cell.text, values[field], "FORMATO_EXCEL_ZEROS"))
        if cell.kind == "number" and money_field(field) and correction is None:
            put(field, cell.text.replace(".", ","), "NUMERO_EXCEL_DECIMAL")

    # Allow reviewed values for missing destination fields as well.
    for (line, field), value in options.overrides.items():
        if line == row and field in values and field not in origin:
            put(field, value, "REVISAO_USUARIO")

    for field in list(values):
        value = values[field]
        key = norm(field)
        if not value:
            continue
        if layout.family != "generic" and (key == "cpfcnpj" or key.endswith("cep") or key in {"rg", "inscricaoestadual", "inscricaomunicipal"}):
            # Only known punctuation is removable. Letters are never stripped from an identifier.
            if re.fullmatch(r"[0-9. /()\-]+", value):
                put(field, re.sub(r"[. /()\-]", "", value), "DOCUMENTO_FORMATACAO")
        if "contacts" in modules and layout.family != "generic" and any(x in key for x in ("telefone", "celular", "fax")):
            clean = re.sub(r"[()+.\-\s]", "", value)
            if not re.fullmatch(r"[0-9]{8,15}", clean) or len(set(clean)) == 1:
                put(field, "", "CONTATO_INVALIDO_VAZIO")
                issues.append(Issue("AVISO", "CONTATO_INVALIDO", field, "Contato inválido removido da saída; preservado na origem e auditoria."))
            else:
                put(field, clean, "CONTATO_FORMATACAO")
        if "contacts" in modules and layout.family != "generic" and "email" in key:
            if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
                put(field, "", "CONTATO_INVALIDO_VAZIO")
                issues.append(Issue("AVISO", "EMAIL_INVALIDO", field, "E-mail inválido ficou vazio na saída."))

    if layout.family in {"clientes", "fornecedores"}:
        doc = values.get("CPF/CNPJ", "")
        if len(doc) == 11 and doc.isdigit() and values.get("Inscrição Estadual"):
            src = norm(origin.get("Inscrição Estadual", ""))
            if src in {"rg", "ierg", "ieeg"} and not values.get("RG"):
                put("RG", values["Inscrição Estadual"], "CPF_RG_SEPARADO")
                put("Inscrição Estadual", "", "CPF_SEM_IE")
            else:
                issues.append(Issue("ERRO", "CPF_COM_IE", "Inscrição Estadual", "Pessoa física não deve ter IE. Revise a origem; só mova para RG se confirmado."))
        if len(doc) == 14 and values.get("RG"):
            src = norm(origin.get("RG", ""))
            if src in {"ierg", "ieeg"}:
                issues.append(Issue("ERRO", "IE_RG_AMBIGUO", "RG", "Campo composto para CNPJ: confirme que é IE e remapeie explicitamente."))
        if "geography" in modules and (not options.geography_confirmed or not options.geography_evidence.strip()):
            issues.append(Issue("ERRO", "UF_SEM_EVIDENCIA", "UF", "Confirme a compatibilidade de UF/endereço/localidade e registre fonte da verificação."))
        if layout.family == "clientes" and "clients" in modules:
            if options.active == "yes":
                put("Ativo", "ATIVO", "CLIENTES_ATIVO_CONFIRMADO")
            if not values.get("Regime Tributário"):
                put("Regime Tributário", "Normal", "REGIME_NORMAL")

    if layout.family == "produtos" and "products" in modules:
        nature = values.get("Tipo do item", "")
        code = values.get("Tipo do Item", "")
        service = norm(nature) in {"servico", "servicos"} or code == "09"
        if code in ITEM_CODES and code != "09" and norm(nature) in {"servico", "servicos"}:
            issues.append(Issue("ERRO", "NATUREZA_CONFLITO", "Tipo do Item", "Natureza serviço conflita com código informado; revise antes de exportar."))
        if code == "09" and norm(nature) == "produto":
            issues.append(Issue("ERRO", "NATUREZA_CONFLITO", "Tipo do item", "Natureza produto conflita com código 09 de serviço."))
        def tax(field, value, rule):
            if values.get(field) and values[field] != value:
                issues.append(Issue("AVISO", "REGRA_SOBRE_ORIGEM", field, "Valor de origem difere da regra documentada. Alteração registrada na revisão."))
            put(field, value, rule)
        if service:
            tax("Tipo do Item", "09", "SERVICO_CODIGO")
            tax("Situação tributária", "SERVIÇOS", "SERVICO_TRIBUTACAO")
            tax("CFOP Dentro", "5933", "SERVICO_CFOP")
            tax("CFOP Fora", "6933", "SERVICO_CFOP")
        elif norm(nature) == "produto" or code in ITEM_CODES:
            if not values.get("Situação tributária"):
                put("Situação tributária", "VENDA NORMAL", "MERCADORIA_TRIBUTACAO")
            status = values.get("Situação tributária")
            if status == "VENDA NORMAL":
                tax("CFOP Dentro", "5.102", "VENDA_NORMAL_CFOP")
                tax("CFOP Fora", "6.102", "VENDA_NORMAL_CFOP")
            if status == "OLEOS E LUBRIFICANTES" and not options.oil_cfop_evidence.strip():
                issues.append(Issue("ERRO", "OLEO_CFOP", "CFOP Dentro", "Confirme os CFOP ST na base aplicável e registre evidência; não são presumidos."))
            if status == "OLEOS E LUBRIFICANTES" and (not values.get("CFOP Dentro") or not values.get("CFOP Fora")):
                issues.append(Issue("ERRO", "OLEO_CFOP_AUSENTE", "CFOP Dentro", "Informe ambos os CFOP confirmados para óleos/lubrificantes."))
            text = norm(values.get("Descrição", ""))
            if "oleo" in text or "lubrificant" in text:
                issues.append(Issue("AVISO", "OLEO_REVISAR", "Descrição", "Revise se é óleo vendido ou peça relacionada; classificação automática não aplicada."))
        else:
            issues.append(Issue("ERRO", "NATUREZA_AUSENTE", "Tipo do item", "Confirme a natureza do item na origem."))

    from app.core.rules.declarative import apply
    declared_issues, declared_changes = apply(values, layout.family, profile)
    issues.extend(declared_issues)
    changes.extend(declared_changes)
    issues.extend(validate_values(values, layout, modules))
    return values, issues, changes
