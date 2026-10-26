"""Local source inventory. Never uploads files or confuses inputs with templates."""
import hashlib
import json
from pathlib import Path

from app.core.catalog import digest, discover, verify_rules
from app.core.importers.reader import inspect, sheets
from app.core.mapping import targets as layout_targets
from app.models import Cancelled, Control

EXTENSIONS = {".xlsx", ".xls", ".csv", ".tsv", ".pdf"}


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def folder_tables(folder, control=None):
    """List individual sheets/tables, including readable failures for the picker."""
    control = control or Control()
    folder = Path(folder).resolve()
    if not folder.is_dir():
        raise ValueError("Escolha uma pasta de fontes existente.")
    found = []
    for path in sorted(folder.rglob("*")):
        control.check()
        if not path.is_file() or path.is_symlink() or path.suffix.lower() not in EXTENSIONS or path.name.startswith("~$"):
            continue
        if len(found) >= 2000:
            raise ValueError("A pasta possui mais de 2.000 tabelas. Escolha uma subpasta menor.")
        try:
            for sheet in sheets(path, control):
                found.append({"path": str(path), "source_sheet": sheet, "title": path.stem + " · " + sheet, "error": ""})
        except Cancelled:
            raise
        except Exception as error:
            found.append({"path": str(path), "source_sheet": "", "title": path.name, "error": str(error)})
    return found


def source_attachments(job):
    return job.get("studio", {}).get("sources", job["attachments"])


def inventory(root, job, control=None):
    """Snapshot IDs bind a recipe to exact input bytes, headers and target models."""
    control = control or Control()
    sources, file_hashes = [], {}
    for item in source_attachments(job):
        control.check()
        if item.get("role") == "reference":
            continue
        path = Path(item["path"])
        if str(path) not in file_hashes:
            file_hashes[str(path)] = digest(path)
        available = [item["source_sheet"]] if item.get("source_sheet") else sheets(path, control)
        for sheet in available:
            source = inspect(path, sheet, item.get("header_row"), item.get("encoding"), item.get("delimiter"), control)
            sources.append({"id": "S" + fingerprint([item["id"], sheet])[:16], "attachment": item["id"],
                            "path": str(path.resolve()), "title": item["title"], "sheet": sheet,
                            "header_row": source.header_row, "encoding": source.encoding, "delimiter": source.delimiter,
                            "format": source.format, "sha256": file_hashes[str(path)],
                            "role": item.get("semantic_role", "auto"),
                            "columns": [{"id": sid, "header": header} for sid, header in zip(source.ids, source.headers)]})
    if not sources:
        raise ValueError("Adicione ao menos uma tabela de origem ao Estúdio.")
    if len(sources) > 200:
        raise ValueError("Selecione no máximo 200 tabelas por projeto.")
    targets = []
    for layout in discover(root):
        targets.append({"id": "T" + fingerprint([str(layout.path), layout.sheet, layout.digest])[:16],
                        "path": str(layout.path), "sheet": layout.sheet, "sha256": layout.digest,
                        "title": layout.label, "family": layout.family, "variant": layout.variant,
                        "columns": layout_targets(layout)})
    if not targets:
        raise ValueError("Configure os modelos de destino em Biblioteca antes de planejar a conversão.")
    return {"sources": sources, "targets": targets, "profile": verify_rules(root),
            "instructions": job.get("studio", {}).get("instructions", ""), "options": job["options"],
            "corrections": job.get("studio", {}).get("corrections", {})}
