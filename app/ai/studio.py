"""Structured planning/auditing for all API providers, with explicit payloads.

No provider can execute a recipe, read files on its own, or approve its answer.
Only this local boundary constructs the content shown in the consent dialog.
"""
import json
from contextlib import closing
from itertools import islice

from app.ai.sanitization import shape
from app.ai.providers import ProviderFailure
from app.models import Cancelled, Control
from app.studio.plan import _check, arr, decode, obj, parse, schema, text

PLAN_TASK = """Propose a version-1 conversion recipe for the supplied tables and exact targets.
Each output selects a target ID. Multiple inputs concatenate into that output.
Each input maps target fields from C1/C2... or join_alias.C1 references.
Joins are exact many-to-one lookups: left and right are source column IDs;
required=true makes missing matches an error. No fuzzy match or invented key.
Filters compare exact text with equals/in/not_in/empty/nonempty. Empty filters
select every row. CTP and CTR must be separate outputs; if a combined source
has no confirmed discriminator, ask a question instead of guessing from sign.
OS headers and items must use compatible model versions and the same group.
Pieces and services may concatenate into an items output if user rules confirm
their nature. Stock can enrich products by a unique confirmed code. Every row
of every selected source must reach an output, join or justified exclusion.
Constants are explicit business decisions; never invent identifiers or missing
facts. Exclusions need nonempty filters and a reason. Do not silently deduplicate.
Use empty arrays for unused operations. If anything essential is missing,
return questions and a draft, possibly with no outputs. Never claim execution.
Each output also has rules: [] or approved project field operations required,
digits, default, uppercase, enum, length, decimal, date. Each rule requires id,
field, operation, value (empty when unused), values ([] when unused), input_format
(empty when unused), min (0 default), max (32767 default), severity. Rules must
follow the user's requirements; ask when a date format/default is uncertain.
Never duplicate a library rule's field or invent identifiers via default.
"""


def planning_payload(context, library_rules, *, headers=True, samples=False, conversation=None, previous_plan=None):
    from app.core.importers.reader import inspect, records
    sources = []
    for entry in context["sources"]:
        source = inspect(entry["path"], entry["sheet"], entry["header_row"], entry["encoding"], entry["delimiter"])
        with closing(records(source)) as rows:
            sample = [raw for _, raw, _ in islice(rows, 3) if raw]
        columns = []
        for column in entry["columns"]:
            examples = [row[column["id"]].text if samples else shape(row[column["id"]].text) for row in sample]
            columns.append({"id": column["id"], "header": column["header"] if headers else "[oculto]", "samples": examples})
        sources.append({"id": entry["id"], "title": entry["title"] if headers else "[oculto]", "sheet": entry["sheet"] if headers else "[oculto]", "role": entry["role"], "columns": columns})
    data = {"requested_task": PLAN_TASK, "user_conversion_rules": context["instructions"],
            "library_rules": library_rules, "executable_library_profile": context["profile"],
            "sources": sources, "targets": [{k: t[k] for k in ("id", "title", "family", "variant", "columns")} for t in context["targets"]],
            "conversation": conversation or [], "previous_plan": previous_plan,
            "disclosure": {"source_headers": headers, "real_samples": samples, "max_samples_per_table": 3}}
    if len(json.dumps(data, ensure_ascii=False).encode()) > 768 * 1024:
        raise ValueError("Contexto de IA acima de 768 KB. Reduza as tabelas ou instruções antes de enviar.")
    return data


def request_plan(providers, data, context, control=None):
    return structured(providers, data, schema(context), lambda answer: parse(answer, context), control)


def audit_schema():
    return obj({"summary": text(), "findings": arr(obj({"severity": {"type": "string", "enum": ["ERRO", "AVISO", "INFORMAÇÃO"]},
                                                      "code": text(), "message": text(), "output_id": text()})), "questions": arr(text())})


def audit_payload(plan, audit, sessions, *, samples=False):
    previews = []
    for output, session in sessions.items():
        rows = []
        for row in session.rows(limit=3):
            render = (lambda value: value) if samples else shape
            rows.append({"line": row["line"], "values": {k: render(v) for k, v in row["values"].items()},
                         "changes": [{"field": c["field"], "rule": c["rule"], "before": render(c["before"]), "after": render(c["after"])} for c in row["changes"]],
                         "issues": row["issues"]})
        from dataclasses import asdict
        previews.append({"output_id": output, "statistics": session.stats(), "global_issues": [asdict(i) for i in session.global_issues], "preview": rows})
    # File names are local evidence, unnecessary for a semantic audit request.
    safe_audit = {**audit, "sources": {sid: {k: value[k] for k in ("rows", "sha256")} for sid, value in audit["sources"].items()}}
    return {"requested_task": "Audit this approved conversion plan against full-run counts, exclusions, validations and the bounded previews. Identify missing coverage, unsafe defaults, ambiguous CTP/CTR, OS links and product/stock joins. Do not claim to have inspected unsent rows. Never approve or mutate records.",
            "plan": plan, "execution_audit": safe_audit, "outputs": previews,
            "disclosure": {"real_samples": samples, "max_output_rows_per_table": 3, "scope": "full counts and up to three sampled output rows per table"}}


def request_audit(providers, data, control=None):
    def validate(answer):
        value = decode(answer)
        _check(value, audit_schema())
        ids = {o["id"] for o in data["plan"]["outputs"]} | {""}
        if any(item["output_id"] not in ids for item in value["findings"]):
            raise ValueError("Auditoria referencia saída inexistente.")
        return value
    return structured(providers, data, audit_schema(), validate, control)


def structured(providers, data, output_schema, validate, control=None):
    control = control or Control()
    attempts = []
    for provider in providers:
        control.check()
        try:
            result = validate(provider.generate(data, output_schema, control))
            control.check()
            return result, {"provider": provider.name, "model": provider.model, "attempts": attempts}
        except Cancelled:
            raise
        except Exception as error:
            # Exception text and response bodies may contain private data/keys.
            attempts.append({"provider": provider.name, "outcome": error.code if isinstance(error, ProviderFailure) else "RESPOSTA_INVALIDA"})
    details = "; ".join(a["provider"] + ": " + a["outcome"] for a in attempts)
    raise ValueError("Nenhum provedor retornou um plano/auditoria válido. " + details + ". Em IA e perfis, confira chave, modelo e Testar conexão. O rascunho e o histórico foram preservados.")
