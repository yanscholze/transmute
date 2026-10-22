"""Interpretador fechado de regras: nenhum eval, Python ou comando do usuário.

Markdown é documentação; o perfil JSON explicita o comportamento determinístico.
Acrescentar uma operação exige implementá-la aqui e testar sua semântica.
"""
import re
from datetime import datetime

from app.core.validation.values import decimal_value, identifier
from app.models import Change, Issue

MODULES = {"contacts", "clients", "products", "geography"}
OPERATIONS = {"required", "digits", "default", "uppercase", "enum", "length", "decimal", "date"}
ALLOWED = {"id", "family", "field", "operation", "value", "values", "min", "max", "severity", "input_format"}


def validate_profile(profile):
    if not isinstance(profile, dict) or type(profile.get("max_total_rows")) is not int or not 2 <= profile["max_total_rows"] <= 10000:
        raise ValueError("Perfil precisa de max_total_rows inteiro entre 2 e 10000.")
    if profile.get("version", 1) != 1 or set(profile) - {"version", "source_sha256", "max_total_rows", "enabled_modules", "rules", "conflicts", "source"}:
        raise ValueError("Versão de perfil ou atributos desconhecidos; revise a compatibilidade antes de executar.")
    modules = profile.get("enabled_modules", sorted(MODULES))
    if not isinstance(modules, list) or any(m not in MODULES for m in modules):
        raise ValueError("Módulo de regras desconhecido.")
    rules = profile.get("rules", [])
    if not isinstance(rules, list) or len(rules) > 1000:
        raise ValueError("Lista de regras inválida ou excessiva.")
    ids = set()
    for r in rules:
        if not isinstance(r, dict) or set(r) - ALLOWED or not all(isinstance(r.get(k), str) and r[k] for k in ["id", "field", "operation"]):
            raise ValueError("Regra precisa de id, field e operation e não pode conter atributos desconhecidos.")
        if r["id"] in ids or r["operation"] not in OPERATIONS or r.get("severity", "ERRO") not in {"ERRO", "AVISO", "INFORMAÇÃO"}:
            raise ValueError("ID duplicado, operação ou severidade inválida.")
        if r.get("family", "*") not in {"*", "generic", "clientes", "fornecedores", "produtos", "veiculos", "pagar", "receber", "os", "vendas"}:
            raise ValueError("Família desconhecida na regra.")
        if r["operation"] == "default" and not isinstance(r.get("value"), str):
            raise ValueError("Default precisa de value textual explícito.")
        if r["operation"] == "default" and identifier(r["field"]):
            raise ValueError("Não é permitido inventar identificadores ausentes por valor padrão.")
        if r["operation"] == "enum" and (not isinstance(r.get("values"), list) or not all(isinstance(v, str) for v in r["values"])):
            raise ValueError("Enum precisa de values, lista de textos.")
        if r["operation"] == "length" and (type(r.get("min", 0)) is not int or type(r.get("max", 32767)) is not int or not 0 <= r.get("min", 0) <= r.get("max", 32767) <= 32767):
            raise ValueError("Limites de comprimento inválidos.")
        ids.add(r["id"])


def apply(values, family, profile):
    issues, changes = [], []
    for rule in profile.get("rules", []):
        if rule.get("family", "*") not in {"*", family}:
            continue
        field, op = rule["field"], rule["operation"]
        if field not in values:
            # A profile targeting another template must never create accidental columns.
            continue
        before = after = values[field]
        problem = ""
        if op == "required" and not before:
            problem = "Campo obrigatório ausente pela regra declarativa."
        elif op == "default" and not before:
            after = rule["value"]
        elif op == "uppercase":
            after = before.upper()
        elif before:
            if op == "digits":
                if re.fullmatch(r"[0-9. /()\-]+", before):
                    after = re.sub(r"[. /()\-]", "", before)
                else:
                    problem = "Identificador contém conteúdo não reconhecido; nenhuma letra foi removida."
            elif op == "enum" and before not in rule["values"]:
                problem = "Valor não pertence à enumeração declarada."
            elif op == "length" and not rule.get("min", 0) <= len(before) <= rule.get("max", 32767):
                problem = "Comprimento fora dos limites declarados."
            elif op == "decimal":
                try:
                    after = format(decimal_value(before), "f").replace(".", ",")
                except ValueError as error:
                    problem = str(error)
            elif op == "date":
                try:
                    after = datetime.strptime(before, rule.get("input_format", "%d/%m/%Y")).strftime("%d/%m/%Y")
                except (ValueError, TypeError):
                    problem = "Data não corresponde ao formato declarado."
        if after != before:
            values[field] = after
            changes.append(Change(field, before, after, rule["id"]))
        if problem:
            issues.append(Issue(rule.get("severity", "ERRO"), rule["id"], field, problem))
    return issues, changes
