"""Validações objetivas, sem inventar obrigatoriedade a partir de exemplos.

Família genérica aplica apenas integridade técnica; suas regras de negócio
precisam ser declaradas. Documentos inválidos são preservados para correção.
"""
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from app.core.mapping import norm
from app.models import Issue

UFS = set("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split())
ITEM_CODES = {"00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "99"}


def identifier(field):
    key = norm(field)
    return any(s in key for s in ["cpf", "cnpj", "inscricao", "cep", "telefone", "celular", "fax", "renavam", "chassi", "codigo", "referencia", "numero", "agencia", "conta", "idveiculo"]) or key in {"id", "rg", "ncm", "cest", "cst", "cfopdentro", "cfopfora", "tipodoitem"}


def money_field(field):
    return (field.startswith(("Preço", "Valor", "Custo", "Percentual", "Peso", "Quantidade", "Estoque"))
            or field in {"Desconto do item", "Quilometragem"})


def decimal_value(value):
    if not re.fullmatch(r"[+-]?(?:\d+|\d{1,3}(?:\.\d{3})+)(?:,\d+)?", value) and not re.fullmatch(r"[+-]?\d+(?:\.\d+)?", value):
        raise ValueError("Número em formato não reconhecido.")
    if "," in value:
        value = value.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"[+-]?\d{1,3}(?:\.\d{3})+", value):
        raise ValueError("Separador ambíguo: confirme o valor usando vírgula decimal ou sem milhar.")
    try:
        result = Decimal(value)
    except InvalidOperation as error:
        raise ValueError("Número inválido.") from error
    if not result.is_finite():
        raise ValueError("Número não finito.")
    return result


def document_valid(value):
    if not value.isascii() or not value.isdigit() or len(value) not in {11, 14} or len(set(value)) == 1:
        return False
    base = value[:-2]
    for step in range(2):
        weights = list(range(len(base) + 1, 1, -1)) if len(value) == 11 else ([5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2] if step == 0 else [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
        residue = sum(int(v) * w for v, w in zip(base, weights)) % 11
        base += str(0 if residue < 2 else 11 - residue)
    return base == value


def validate_values(values, layout, modules=None):
    modules = modules if modules is not None else ["contacts", "clients", "products", "geography"]
    issues = []
    for field, value in values.items():
        if not value:
            continue
        if len(value) > 32767 or re.search(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", value):
            issues.append(Issue("ERRO", "CELULA_EXCEL", field, "Conteúdo excede limite de célula ou contém controle incompatível com XLSX."))
        if layout.family == "generic":
            continue
        key = norm(field)
        if key == "cpfcnpj" and not document_valid(value):
            issues.append(Issue("ERRO", "DOC_INVALIDO", field, "CPF/CNPJ inválido: verifique comprimento e dígitos verificadores; não foi corrigido."))
        if key.endswith("cep") and (not re.fullmatch(r"[0-9]{8}", value)):
            issues.append(Issue("ERRO", "CEP_INVALIDO", field, "CEP precisa conter os oito dígitos fornecidos pela origem."))
        if key.endswith("uf") and value not in UFS:
            issues.append(Issue("ERRO", "UF_INVALIDA", field, "Sigla de UF inválida."))
        if money_field(field):
            try:
                decimal_value(value)
            except ValueError as error:
                issues.append(Issue("ERRO", "NUMERO_INVALIDO", field, str(error)))
        if field.startswith("Data ") or field == "Data de Nascimento":
            try:
                datetime.strptime(value, "%d/%m/%Y")
            except ValueError:
                issues.append(Issue("ERRO", "DATA_INVALIDA", field, "Informe data válida DD/MM/AAAA."))
        if field.startswith("Hora "):
            if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?", value):
                issues.append(Issue("ERRO", "HORA_INVALIDA", field, "Hora inválida; use HH:MM ou HH:MM:SS."))
    if "geography" in modules and layout.family in {"clientes", "fornecedores"} and not values.get("UF"):
        issues.append(Issue("ERRO", "UF_AUSENTE", "UF", "UF obrigatória; confirme endereço/localidade em fonte confiável e registre evidência."))
    if "products" in modules and layout.family == "produtos":
        code = values.get("Tipo do Item", "")
        if not code or code not in ITEM_CODES:
            issues.append(Issue("ERRO", "TIPO_ITEM", "Tipo do Item", "Categoria do sistema não confirmada. Use código textual 00–10 ou 99 apoiado pela origem."))
    if layout.family in {"os", "vendas"}:
        field = "Número da OS (externo)" if layout.family == "os" else "Número da venda (externo)"
        if not values.get(field):
            issues.append(Issue("ERRO", "VINCULO_AUSENTE", field, "Identificação obrigatória para preservar vínculos e dividir arquivos com segurança."))
    return issues
