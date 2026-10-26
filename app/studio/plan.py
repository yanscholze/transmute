"""Closed recipe language: split, concatenate and exact many-to-one lookup.

Models never provide code. Local validation checks the JSON contract AND every
source, field, alias and target reference independently of the provider.
"""
import json
import re
import copy

from app.studio.catalog import fingerprint
from app.core.validation.values import identifier
from app.core.rules.declarative import OPERATIONS, validate_profile


def obj(properties):
    return {"type": "object", "additionalProperties": False, "properties": properties, "required": list(properties)}


def arr(items):
    return {"type": "array", "items": items}


def text():
    return {"type": "string"}


def schema(context):
    source = {"type": "string", "enum": [s["id"] for s in context["sources"]]}
    target = {"type": "string", "enum": [t["id"] for t in context["targets"]]}
    filters = arr(obj({"column": text(), "operator": {"type": "string", "enum": ["equals", "in", "not_in", "nonempty", "empty"]}, "values": arr(text())}))
    joins = arr(obj({"source": source, "alias": text(), "left": text(), "right": text(), "required": {"type": "boolean"}}))
    inputs = arr(obj({"source": source, "filters": filters, "joins": joins,
                      "fields": arr(obj({"target": text(), "source": text()})),
                      "constants": arr(obj({"target": text(), "value": text()}))}))
    rule = obj({"id": text(), "field": text(), "operation": {"type": "string", "enum": sorted(OPERATIONS)}, "value": text(), "values": arr(text()),
                "input_format": text(), "min": {"type": "integer"}, "max": {"type": "integer"}, "severity": {"type": "string", "enum": ["ERRO", "AVISO", "INFORMAÇÃO"]}})
    return obj({"version": {"type": "integer", "enum": [1]}, "summary": text(), "questions": arr(text()),
                "outputs": arr(obj({"id": text(), "title": text(), "target": target, "group": text(), "inputs": inputs, "rules": arr(rule)})),
                "exclusions": arr(obj({"source": source, "filters": filters, "reason": text()}))})


def _check(value, spec, depth=0):
    if depth > 18:
        raise ValueError("Plano excede a profundidade permitida.")
    kind = spec["type"]
    valid = {"object": isinstance(value, dict), "array": isinstance(value, list), "string": isinstance(value, str),
             "integer": type(value) is int, "boolean": type(value) is bool}[kind]
    if not valid or ("enum" in spec and value not in spec["enum"]):
        raise ValueError("Plano contém tipo ou referência inválida.")
    if kind == "object":
        if set(value) != set(spec["properties"]):
            raise ValueError("Plano contém campos ausentes ou não permitidos.")
        for key, item in value.items():
            _check(item, spec["properties"][key], depth + 1)
    elif kind == "array":
        if len(value) > 500:
            raise ValueError("Plano contém operações demais.")
        for item in value:
            _check(item, spec["items"], depth + 1)
    elif kind == "string" and len(value) > 8000:
        raise ValueError("Campo textual do plano excede o limite.")


def decode(text):
    """Strict JSON at the trust boundary; duplicate keys cannot hide decisions."""
    def unique(pairs):
        result = {}
        for key, item in pairs:
            if key in result:
                raise ValueError("Plano contém chaves JSON duplicadas.")
            result[key] = item
        return result
    if not isinstance(text, str) or len(text.encode()) > 1024 * 1024:
        raise ValueError("Plano acima de 1 MB ou resposta de tipo inválido.")
    return json.loads(text, object_pairs_hook=unique)


def parse(value, context, executable=False):
    if isinstance(value, str):
        value = decode(value)
    _check(value, schema(context))
    if executable and (value["questions"] or not value["outputs"]):
        raise ValueError("Resolva as perguntas e defina os destinos antes de aprovar o plano.")
    sources = {s["id"]: {c["id"] for c in s["columns"]} for s in context["sources"]}
    targets = {t["id"]: set(t["columns"]) for t in context["targets"]}
    target_families = {t["id"]: t["family"] for t in context["targets"]}
    output_ids, used = set(), set()
    for output in value["outputs"]:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,59}", output["id"]) or output["id"] in output_ids:
            raise ValueError("IDs de saída precisam ser únicos e conter apenas letras, números, _ ou -.")
        output_ids.add(output["id"])
        if not output["title"].strip() or not output["inputs"]:
            raise ValueError("Cada destino precisa de título e pelo menos uma origem.")
        validate_profile({"max_total_rows": 10000, "enabled_modules": [], "rules": output["rules"]})
        library_fields = {r["field"] for r in context["profile"].get("rules", []) if r.get("family", "*") in {"*", target_families[output["target"]]}}
        if any(r["field"] not in targets[output["target"]] for r in output["rules"]):
            raise ValueError("Regra do projeto referencia campo inexistente no destino.")
        if any(r["field"] in library_fields for r in output["rules"]):
            raise ValueError("Um campo já possui regra na Biblioteca. Revise essa regra antes de propor uma operação paralela para o mesmo campo.")
        for entry in output["inputs"]:
            used.add(entry["source"])
            columns = set(sources[entry["source"]])
            aliases = set()
            for join in entry["joins"]:
                if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,39}", join["alias"]) or join["alias"] in aliases:
                    raise ValueError("Aliases de junção inválidos ou repetidos.")
                aliases.add(join["alias"])
                if join["left"] not in sources[entry["source"]] or join["right"] not in sources[join["source"]]:
                    raise ValueError("Chave de junção inexistente.")
                columns.update(join["alias"] + "." + c for c in sources[join["source"]])
                used.add(join["source"])
            mapped = set()
            for field in entry["fields"] + entry["constants"]:
                if field["target"] not in targets[output["target"]] or field["target"] in mapped:
                    raise ValueError("Campo de destino inexistente ou definido mais de uma vez.")
                mapped.add(field["target"])
                if "source" in field and field["source"] not in columns:
                    raise ValueError("Campo de origem inexistente no plano.")
                declared_nature = field["target"] == "Tipo do item" and field.get("value") in {"Serviço", "Mercadoria"}
                if "value" in field and identifier(field["target"]) and not declared_nature:
                    raise ValueError("Constantes não podem fabricar identificadores. Mapeie uma fonte confiável para esse campo.")
            if not mapped:
                raise ValueError("Uma rota precisa mapear pelo menos um campo.")
            _filters(entry["filters"], sources[entry["source"]])
    for exclusion in value["exclusions"]:
        if not exclusion["reason"].strip() or not exclusion["filters"]:
            raise ValueError("Exclusão exige motivo e filtro explícitos.")
        used.add(exclusion["source"])
        _filters(exclusion["filters"], sources[exclusion["source"]])
    if executable and used != set(sources):
        raise ValueError("Há tabelas sem destino, consulta por chave ou exclusão justificada no plano.")
    return value


def _filters(filters, columns):
    for condition in filters:
        if condition["column"] not in columns or (condition["operator"] in {"equals", "in", "not_in"} and not condition["values"]):
            raise ValueError("Filtro referencia coluna inexistente ou valores vazios.")
        if condition["operator"] == "equals" and len(condition["values"]) != 1:
            raise ValueError("Filtro equals exige exatamente um valor.")


def matches(row, filters):
    """Exact text comparison: never infer CTP/CTR from sign, case or a filename."""
    for item in filters:
        value = row[item["column"]].text
        op = item["operator"]
        if (op in {"equals", "in"} and value not in item["values"]) or (op == "not_in" and value in item["values"]):
            return False
        if (op == "empty" and value != "") or (op == "nonempty" and value == ""):
            return False
    return True


def approve(value, context):
    plan = parse(value, context, executable=True)
    return {"plan_hash": fingerprint(plan), "context_hash": fingerprint(context)}


def review_fingerprint(context):
    """The review checkbox itself must not invalidate the proposal it confirms."""
    reviewed = copy.deepcopy(context)
    reviewed["options"]["acknowledge_conflicts"] = True
    return fingerprint(reviewed)


def verify_approval(plan, context, approval):
    if not approval or approve(plan, context) != approval:
        raise ValueError("O plano, as fontes, os modelos ou as regras mudaram. Revise e aprove novamente antes de executar.")
