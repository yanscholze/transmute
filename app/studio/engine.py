"""Execute an approved composition locally, retaining Cell types and row lineage.

SQLite staging/indexes avoid keeping client tables in RAM. Joins are exact and
many-to-one: duplicate lookup keys fail instead of multiplying/deleting rows.
Every selected source row must be consumed or explicitly excluded with a reason.
"""
import copy
import json
import sqlite3
import tempfile
from dataclasses import asdict
from pathlib import Path

from app.core.batch import groups, options_from
from app.core.catalog import discover
from app.core.importers.reader import inspect, records
from app.core.session import process, validate_links
from app.models import Cell, Control, Decision, Issue, Source
from app.studio.catalog import fingerprint, inventory, source_attachments
from app.studio.plan import matches, parse, verify_approval


def cells(text):
    return {key: Cell(**value) for key, value in json.loads(text).items()}


def reliable_key(cell, options):
    if cell.kind in {"formula", "error"}:
        return False
    return cell.kind != "number" or (options.numeric_identifiers_confirmed and len(cell.text) <= 15)


def row_identity(source, line, joins, raw):
    """Bind a correction to original lineage and mapped cells, not output position."""
    packed = {k: asdict(v) if isinstance(v, Cell) else v for k, v in raw.items()}
    return fingerprint({"source": source, "line": line, "joins": joins, "raw": packed})


def execute(root, state, original, control=None):
    control = control or Control()
    job = copy.deepcopy(original)
    studio = job.setdefault("studio", {})
    context = inventory(root, job, control)
    plan = parse(studio.get("plan", {}), context, executable=True)
    verify_approval(plan, context, studio.get("approval"))
    studio.setdefault("sources", copy.deepcopy(source_attachments(job)))
    sources = {s["id"]: s for s in context["sources"]}
    target_info = {t["id"]: t for t in context["targets"]}
    layouts = {(str(t.path), t.sheet): t for t in discover(root)}
    dependencies = {s["path"]: s["sha256"] for s in sources.values()}
    sessions, outputs = {}, []
    audit = {"plan_hash": fingerprint(plan), "context_hash": fingerprint(context), "sources": {}, "outputs": {}, "exclusions": [], "unassigned_rows": 0}
    state = Path(state)
    state.mkdir(exist_ok=True, parents=True)
    try:
        with tempfile.TemporaryDirectory(prefix="composition-", dir=state) as directory:
            db = sqlite3.connect(str(Path(directory) / "sources.sqlite3"))
            try:
                db.executescript("""
                    CREATE TABLE rows(source TEXT,line INTEGER,cells TEXT,problems TEXT,PRIMARY KEY(source,line));
                    CREATE TABLE used(source TEXT,line INTEGER,kind TEXT);
                    CREATE INDEX ix_used ON used(source,line);
                    CREATE TABLE lookup(source TEXT,column_id TEXT,key TEXT,line INTEGER,cells TEXT,problems TEXT,UNIQUE(source,column_id,key));
                """)
                for sid, entry in sources.items():
                    control.check()
                    source = inspect(entry["path"], entry["sheet"], entry["header_row"], entry["encoding"], entry["delimiter"], control)
                    count = 0
                    for line, raw, structural in records(source, control):
                        if raw is None:
                            continue
                        db.execute("INSERT INTO rows VALUES(?,?,?,?)", (sid, line, json.dumps({k: asdict(v) for k, v in raw.items()}, ensure_ascii=False), json.dumps(structural)))
                        count += 1
                    audit["sources"][sid] = {"rows": count, "sha256": entry["sha256"], "file": Path(entry["path"]).name, "sheet": entry["sheet"]}
                indexed = set()
                for output in plan["outputs"]:
                    control.check()
                    target = target_info[output["target"]]
                    layout = layouts[(target["path"], target["sheet"])]
                    first = sources[output["inputs"][0]["source"]]
                    mapped = {field["target"] for entry in output["inputs"] for field in entry["fields"] + entry["constants"]}
                    virtual = Source(Path(first["path"]), output["title"], 1, [field for field in target["columns"] if field in mapped], format="studio")
                    decisions = [Decision(sid, field, 1.0, "Plano aprovado", True) for sid, field in zip(virtual.ids, virtual.headers)]
                    options = options_from(job["options"])
                    corrections = studio.get("corrections", {}).get(output["id"], [])
                    if any(type(c.get("line")) is not int or c["line"] < 2 or c.get("field") not in target["columns"] or not isinstance(c.get("value"), str) for c in corrections):
                        raise ValueError("Correção local contém linha, campo ou valor inválido.")
                    options.overrides = {(v["line"], v["field"]): v["value"] for v in corrections}

                    def composed_rows(route=output, source=virtual):
                        sequence = 1
                        for entry in route["inputs"]:
                            for join in entry["joins"]:
                                key = (join["source"], join["right"])
                                if key in indexed:
                                    continue
                                for line, packed, problems in db.execute("SELECT line,cells,problems FROM rows WHERE source=? ORDER BY line", (join["source"],)):
                                    value = cells(packed)[join["right"]]
                                    if not value.text:
                                        continue
                                    if not reliable_key(value, options):
                                        raise ValueError("Chave de junção contém fórmula, erro ou número com possível perda de zeros. Corrija a fonte ou use chave textual confiável.")
                                    try:
                                        db.execute("INSERT INTO lookup VALUES(?,?,?,?,?,?)", (*key, value.text, line, packed, problems))
                                    except sqlite3.IntegrityError:
                                        raise ValueError("Chave duplicada na tabela de consulta. A junção exige chave única; nenhuma linha foi deduplicada.") from None
                                indexed.add(key)
                            for line, packed, structural in db.execute("SELECT line,cells,problems FROM rows WHERE source=? ORDER BY line", (entry["source"],)):
                                control.check()
                                raw = cells(packed)
                                if not matches(raw, entry["filters"]):
                                    continue
                                joined, problems = [], json.loads(structural)
                                for join in entry["joins"]:
                                    key = raw[join["left"]]
                                    if not reliable_key(key, options) and key.text:
                                        raise ValueError("Chave da origem não é textual confiável. Revise os identificadores antes de cruzar tabelas.")
                                    match = db.execute("SELECT line,cells,problems FROM lookup WHERE source=? AND column_id=? AND key=?", (join["source"], join["right"], key.text)).fetchone() if key.text else None
                                    if not match:
                                        if join["required"]:
                                            problems.append("Junção obrigatória sem correspondência: " + join["alias"])
                                        other = {c["id"]: Cell() for c in sources[join["source"]]["columns"]}
                                    else:
                                        other = cells(match[1])
                                        problems.extend(json.loads(match[2]))
                                        joined.append({"alias": join["alias"], "source": join["source"], "line": match[0]})
                                        db.execute("INSERT INTO used VALUES(?,?,?)", (join["source"], match[0], "lookup"))
                                    raw.update({join["alias"] + "." + k: v for k, v in other.items()})
                                values = {field["target"]: raw[field["source"]] for field in entry["fields"]}
                                values.update({field["target"]: Cell(field["value"], "text", "Constante do plano aprovado") for field in entry["constants"]})
                                sequence += 1
                                db.execute("INSERT INTO used VALUES(?,?,?)", (entry["source"], line, route["id"]))
                                mapped_raw = {sid: values.get(field, Cell()) for sid, field in zip(source.ids, source.headers)}
                                identity = row_identity(entry["source"], line, joined, mapped_raw)
                                for correction in corrections:
                                    if correction["line"] == sequence and correction.get("origin_hash") != identity:
                                        options.overrides.pop((sequence, correction["field"]), None)
                                        problems.append("Correção local desatualizada: a origem, os campos ou a posição desta linha mudaram. O valor antigo não foi aplicado. Confira a linha em Resultados ou descarte as correções pendentes.")
                                yield sequence, mapped_raw, problems, {"source": entry["source"], "line": line, "joins": joined, "fields": entry["fields"], "constants": entry["constants"]}

                    session = process(root, state, virtual, layout, decisions, options, control, record_iter=composed_rows(), dependencies=dependencies, allow_empty=True, project_rules=output["rules"])
                    if any(c["line"] > session.stats()["read"] + 1 for c in corrections):
                        session.global_issues.append(Issue("ERRO", "CORRECAO_SEM_LINHA", "", "Há correções antigas sem linha correspondente nesta saída. Revise ou descarte as correções pendentes em Resultados."))
                    if any(s["format"] == "pdf" for s in sources.values()) and not options.pdf_confirmed:
                        session.global_issues.append(Issue("ERRO", "PDF_CONFERENCIA", "", "Confira as tabelas extraídas com os PDFs originais nas fontes antes de exportar."))
                    session.ai_events.append({"kind": "approved_composition", "plan_sha256": audit["plan_hash"], "context_sha256": audit["context_hash"], "sources": audit["sources"]})
                    session.studio_context_hash = audit["context_hash"]
                    sessions[output["id"]] = session
                    stats = session.stats()
                    pending = stats["errors"] or any(p.severity == "ERRO" for p in session.global_issues)
                    outputs.append({"id": output["id"], "title": output["title"], "path": first["path"], "source_sheet": output["title"],
                                    "family": layout.family, "layout_path": str(layout.path), "layout_sheet": layout.sheet, "group": output["group"] or "principal",
                                    "role": "source", "stats": stats, "status": "Precisa de revisão" if pending else "Pronto para exportar", "message": ""})
                    audit["outputs"][output["id"]] = {**stats, **session.audit_counts(control)}
                for exclusion in plan["exclusions"]:
                    count = 0
                    for line, packed in db.execute("SELECT line,cells FROM rows WHERE source=?", (exclusion["source"],)):
                        control.check()
                        if matches(cells(packed), exclusion["filters"]):
                            db.execute("INSERT INTO used VALUES(?,?,?)", (exclusion["source"], line, "explicit_exclusion"))
                            count += 1
                    audit["exclusions"].append({"source": exclusion["source"], "rows": count, "reason": exclusion["reason"]})
                audit["unassigned_rows"] = db.execute("SELECT count(*) FROM rows r WHERE NOT EXISTS(SELECT 1 FROM used u WHERE u.source=r.source AND u.line=r.line)").fetchone()[0]
                if audit["unassigned_rows"]:
                    for session in sessions.values():
                        session.global_issues.append(Issue("ERRO", "LINHAS_SEM_DESTINO", "", f"{audit['unassigned_rows']} linhas não receberam destino ou exclusão justificada. Revise filtros e cruzamentos; nenhuma linha pode desaparecer silenciosamente."))
                # Financial splits must be disjoint even when both routes look valid.
                financial = [o["id"] for o in outputs if o["family"] in {"pagar", "receber"}]
                financial_uses = {}
                for oid in financial:
                    for origin in sessions[oid].lineage():
                        key = (origin["source_id"], origin["source_line"])
                        if key in financial_uses and financial_uses[key] != oid:
                            sessions[oid].global_issues.append(Issue("ERRO", "FINANCEIRO_DUPLICADO", "", "Uma linha financeira atingiu mais de uma saída. CTP/CTR exigem filtros inequívocos."))
                        financial_uses[key] = oid
            finally:
                db.close()
        for session in sessions.values():
            session.verify()  # Includes source changes while composition was running.
        job["attachments"] = outputs
        messages = []
        try:
            for group in groups(job, sessions):
                messages.extend(p.message for p in validate_links(group[0], group[1] if len(group) > 1 else None) if p.severity == "ERRO")
        except ValueError as error:
            messages.append(str(error))
        job.pop("link_message", None)
        if messages:
            job["link_message"] = "\n".join(messages)
        pending = messages or any(s.stats()["errors"] or any(i.severity == "ERRO" for i in s.global_issues) for s in sessions.values())
        job["status"] = "Revisar pendências" if pending else "Pronta para exportar"
        for item in outputs:
            issues = [i.message for i in sessions[item["id"]].global_issues if i.severity == "ERRO"]
            if issues:
                item.update(status="Precisa de revisão", message="\n".join(issues))
        studio["last_run"] = audit
        studio.pop("ai_audit", None)  # Previous audit remains in immutable history.
        return job, sessions
    except BaseException:
        for session in sessions.values():
            session.close()
        raise


def verify_export(job, sessions):
    if job.get("mode") != "studio":
        return
    if not sessions:
        raise ValueError("Execute o plano aprovado antes de exportar.")
    first = next(iter(sessions.values()))
    context = inventory(first.root, job)
    studio = job["studio"]
    verify_approval(studio["plan"], context, studio.get("approval"))
    audit = studio.get("ai_audit", {})
    if audit.get("context_sha256") == fingerprint(context) and not audit.get("reviewed") and any(f["severity"] == "ERRO" for f in audit.get("findings", [])):
        raise ValueError("A auditoria IA tem apontamentos de erro. Confira-os e registre sua revisão na aba Auditoria antes de exportar.")
    if any(getattr(s, "studio_context_hash", None) != fingerprint(context) for s in sessions.values()):
        raise ValueError("A composição foi alterada. Execute novamente antes de exportar.")
