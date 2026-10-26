"""Orquestra arquivos de uma importação sem misturar tabelas de famílias distintas.

Todas as abas/tabelas detectadas são representadas. Falha de arquivo não apaga
os demais e fica explícita no manifesto. Exportação valida todos os grupos
antes de publicar um diretório único, com rollback em cancelamento/erro.
"""
import copy
import json
import re
import shutil
import tempfile
import uuid
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

from app.core.catalog import discover
from app.core.exporters.writer import export
from app.core.importers.reader import inspect, sheets
from app.core.mapping import suggest
from app.core.session import process, validate_links
from app.models import Cancelled, Control, Decision, Options


def options_from(data):
    allowed = Options.__dataclass_fields__
    return Options(**{k: v for k, v in data.items() if k in allowed and k != "overrides"})


def groups(job, sessions):
    grouped, singles = defaultdict(list), []
    for item in job["attachments"]:
        session = sessions.get(item["id"])
        if not session:
            continue
        if session.layout.family in {"os", "vendas"} and session.layout.variant in {"header", "items"}:
            key = (session.layout.family, str(session.layout.path.parent), item.get("group", "principal"))
            grouped[key].append(session)
        else:
            singles.append([session])
    result = singles
    for linked in grouped.values():
        if len(linked) != 2 or {s.layout.variant for s in linked} != {"header", "items"}:
            raise ValueError("Há cabeçalhos/itens sem um par único. Em Revisar arquivo, confira os modelos e use Grupo de vínculo para separar os lotes.")
        result.append(linked)
    return result


def process_import(root, state, job, control=None):
    control = control or Control()
    job = copy.deepcopy(job)
    job.pop("link_message", None)
    layouts = {(str(layout.path), layout.sheet): layout for layout in discover(root)}
    sessions, expanded = {}, []
    try:
        for original in job["attachments"]:
            control.check()
            if original.get("role") == "reference":
                reference = {**original, "status": "Documento de apoio", "message": "Não convertido por escolha explícita."}
                reference.pop("stats", None)
                expanded.append(reference)
                continue
            try:
                available = [original["source_sheet"]] if original.get("source_sheet") else sheets(original["path"], control)
                for index, sheet in enumerate(available):
                    item = copy.deepcopy(original)
                    if len(available) > 1:
                        item["id"] = original["id"] if index == 0 else uuid.uuid4().hex
                        item["title"] = original["title"] + " · " + sheet
                    item["source_sheet"] = sheet
                    expanded.append(item)
            except Cancelled:
                raise
            except Exception as error:
                expanded.append({**original, "status": "Precisa de revisão", "message": str(error)})
        for index, item in enumerate(expanded):
            control.check()
            if item.get("role") == "reference" or not item.get("source_sheet"):
                continue
            control.progress(index, f"Arquivo {index + 1}/{len(expanded)} · {item['title']}")
            try:
                layout = layouts.get((item["layout_path"], item["layout_sheet"]))
                if layout is None or layout.family != item["family"]:
                    raise ValueError("Modelo não disponível para esta categoria. Abra Revisar arquivo e escolha outro modelo.")
                source = inspect(item["path"], item["source_sheet"], item.get("header_row"), item.get("encoding"), item.get("delimiter"), control)
                if item.get("mapping") and item.get("source_headers") and item["source_headers"] != source.headers:
                    raise ValueError("A estrutura da origem mudou. Abra Revisar arquivo e refaça o mapeamento antes de processar.")
                decisions = [Decision(**d) for d in item["mapping"]] if item.get("mapping") else suggest(source, layout)
                options = options_from(item.get("options", job["options"]))
                options.overrides = {(c["line"], c["field"]): c["value"] for c in item.get("corrections", [])}
                session = process(root, state, source, layout, decisions, options, control)
                sessions[item["id"]] = session
                item.update(header_row=source.header_row, encoding=source.encoding, delimiter=source.delimiter,
                            mapping=[asdict(d) for d in decisions], stats=session.stats(), source_headers=source.headers, source_sha256=session.source_hash)
                pending = session.stats()["errors"] or any(p.severity == "ERRO" for p in session.global_issues)
                item["status"] = "Precisa de revisão" if pending else "Pronto para exportar"
                item["message"] = "\n".join(p.message for p in session.global_issues if p.severity == "ERRO")
            except Cancelled:
                raise
            except Exception as error:
                item.pop("stats", None)
                item.update(status="Precisa de revisão", message=str(error))
        job["attachments"] = expanded
        job["status"] = "Revisar pendências" if any(i["status"] == "Precisa de revisão" for i in expanded) else "Pronta para exportar"
        try:
            for group in groups(job, sessions):
                messages = [p.message for p in validate_links(group[0], group[1] if len(group) > 1 else None) if p.severity == "ERRO"]
                if messages:
                    job["status"] = "Revisar pendências"
                    job["link_message"] = "\n".join(messages)
        except ValueError as error:
            job["status"] = "Revisar pendências"
            job["link_message"] = str(error)
        return job, sessions
    except BaseException:
        for session in sessions.values():
            session.close()
        raise


def export_import(job, sessions, destination, control=None, reports_only=False, detailed_audit=False):
    control = control or Control()
    if not reports_only and job.get("mode") == "studio":
        from app.studio.engine import verify_export
        verify_export(job, sessions)
    pending = [a for a in job["attachments"] if a.get("role") != "reference" and (a.get("status") != "Pronto para exportar" or a["id"] not in sessions)]
    if not reports_only and pending:
        raise ValueError("Há arquivos pendentes ou que precisam ser reprocessados. Revise-os ou exporte apenas o relatório da importação.")
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^\w-]+", "_", job["name"]).strip("_")[:60] or "Importacao"
    final = destination / (slug + "_" + uuid.uuid4().hex[:8])
    staging = Path(tempfile.mkdtemp(prefix=".importacao-", dir=destination))
    try:
        diagnostics = staging / "Parciais"
        diagnostics.mkdir()
        output_root = diagnostics if reports_only else staging / "Tratadas"
        output_root.mkdir(exist_ok=True)
        export_groups = [[session] for session in sessions.values()] if reports_only else groups(job, sessions)
        for index, group in enumerate(export_groups, 1):
            control.check()
            path = export(group, output_root, control, reports_only=reports_only, detailed_audit=detailed_audit)
            folder = output_root / f"{index:02d}_{group[0].layout.family}"
            path.rename(folder)
            if not reports_only:
                target = diagnostics / folder.name
                target.mkdir()
                for name in ["diagnostico.md", "relatorio.json", "resumo.txt"]:
                    shutil.copy2(folder / name, target / name)
        report = {"name": job["name"], "categories": job["categories"], "status": job["status"],
                  "files": [{k: a.get(k) for k in ["title", "family", "role", "source_sheet", "status", "message", "stats"]} for a in job["attachments"]]}
        if job.get("mode") == "studio":
            studio = job.get("studio", {})
            for name, data in [("plano_aprovado.json", studio.get("plan")), ("auditoria_composicao.json", studio.get("last_run")), ("auditoria_ia.json", studio.get("ai_audit"))]:
                (diagnostics / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            (diagnostics / "instrucoes_do_projeto.md").write_text(studio.get("instructions", ""), encoding="utf-8")
        (staging / "importacao.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        lines = [job["name"], "", *[f"{a['title']} — {a.get('status', 'Aguardando')}" for a in job["attachments"]]]
        (staging / "resumo.txt").write_text("\n".join(lines), encoding="utf-8")
        (diagnostics / "diagnostico_importacao.md").write_text("# " + job["name"] + "\n\n" + "\n".join(f"- {a['title']}: {a.get('status', 'Aguardando')}\n  {a.get('message', '')}" for a in job["attachments"]), encoding="utf-8")
        control.check()
        staging.rename(final)
        return final
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
