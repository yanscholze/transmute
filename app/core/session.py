"""Sessão de conversão em disco, com snapshots e revisão paginada.

SQLite evita uma cópia integral da base em RAM. O chamador possui a sessão e
deve fechá-la; processamento malsucedido remove o arquivo automaticamente.
"""
import hashlib
import json
import tempfile
from dataclasses import asdict
from pathlib import Path

from app.core.catalog import digest, rules_path, verify_rules
from app.core.importers.reader import records
from app.core.mapping import validate_mapping
from app.core.transformation.engine import transform
from app.models import Control, Issue
from app.storage.database import database


class Session:
    def __init__(self, directory, source, layout, decisions, options, root):
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        handle = tempfile.NamedTemporaryFile(prefix="review-", suffix=".sqlite3", dir=directory, delete=False)
        self.path = Path(handle.name)
        handle.close()
        self.source, self.layout, self.decisions, self.options, self.root = source, layout, decisions, options, root
        self.source_hash = digest(source.path)
        self.rules_hash = digest(rules_path(root))
        self.profile_hash = hashlib.sha256(json.dumps(verify_rules(root), sort_keys=True).encode()).hexdigest()
        self.blank_rows = 0
        self.global_issues = []
        self.ai_events = []
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE records(line INTEGER PRIMARY KEY, raw TEXT, output TEXT, problems TEXT, changes TEXT, severity TEXT, groupkey TEXT);
                CREATE INDEX ix_severity ON records(severity);
                CREATE INDEX ix_group ON records(groupkey);
            """)

    def connect(self):
        return database(self.path)

    def close(self):
        self.path.unlink(missing_ok=True)

    def rows(self, severity="", query="", offset=0, limit=None):
        conditions, params = [], []
        if severity:
            conditions.append("severity=?")
            params.append(severity)
        if query:
            conditions.append("(output LIKE ? ESCAPE '\\' OR CAST(line AS TEXT)=?)")
            term = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            params.extend([f"%{term}%", query])
        sql = "SELECT line,raw,output,problems,changes,severity,groupkey FROM records"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY line"
        if limit is not None:
            sql += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        with self.connect() as db:
            for line, raw, output, problems, changes, level, group in db.execute(sql, params):
                yield {"line": line, "raw": json.loads(raw), "values": json.loads(output), "issues": json.loads(problems), "changes": json.loads(changes), "severity": level, "group": group}

    def stats(self):
        with self.connect() as db:
            result = dict(db.execute("SELECT severity,count(*) FROM records GROUP BY severity"))
        return {"read": sum(result.values()), "valid": result.get("OK", 0), "warnings": result.get("AVISO", 0), "errors": result.get("ERRO", 0), "blank_rows": self.blank_rows}

    def verify(self):
        profile = verify_rules(self.root)
        if digest(rules_path(self.root)) != self.rules_hash or hashlib.sha256(json.dumps(profile, sort_keys=True).encode()).hexdigest() != self.profile_hash:
            raise ValueError("As regras ou o perfil mudaram depois do processamento. Reprocesse antes de exportar.")
        if digest(self.source.path) != self.source_hash:
            raise ValueError("A origem mudou desde o processamento. Leia e processe novamente.")
        if digest(self.layout.path) != self.layout.digest:
            raise ValueError("O modelo mudou desde a leitura. Reabra o modelo e processe novamente.")


def process(root, state, source, layout, decisions, options, control=None):
    control = control or Control()
    profile = verify_rules(root)
    if digest(layout.path) != layout.digest:
        raise ValueError("Modelo modificado após leitura.")
    validate_mapping(source, layout, decisions)
    if options.columns not in {"omit", "full"} or not options.acknowledge_conflicts:
        raise ValueError("Escolha a política de colunas e confirme a leitura dos conflitos.")
    if layout.family == "clientes" and "clients" in profile.get("enabled_modules", ["clients"]) and options.active not in {"yes", "no"}:
        raise ValueError("Responda se todos os clientes devem receber Ativo = ATIVO nesta conversão.")
    session = Session(state / "sessions", source, layout, decisions, options, root)
    groupfield = "Número da OS (externo)" if layout.family == "os" else "Número da venda (externo)" if layout.family == "vendas" else ""
    try:
        with session.connect() as db:
            for n, raw, structural in records(source, control):
                control.check()
                if raw is None:
                    session.blank_rows += 1
                    continue
                values, issues, changes = transform(raw, source, layout, decisions, options, n, profile)
                issues.extend(Issue("ERRO", "ESTRUTURA_LINHA", "", p) for p in structural)
                severity = "ERRO" if any(i.severity == "ERRO" for i in issues) else "AVISO" if any(i.severity == "AVISO" for i in issues) else "OK"
                db.execute("INSERT INTO records VALUES(?,?,?,?,?,?,?)", (n, json.dumps({k: asdict(v) for k, v in raw.items()}, ensure_ascii=False), json.dumps(values, ensure_ascii=False), json.dumps([asdict(i) for i in issues], ensure_ascii=False), json.dumps([asdict(c) for c in changes], ensure_ascii=False), severity, values.get(groupfield, "")))
                if n % 250 == 0:
                    control.progress(n, f"{n:,} linhas lidas".replace(",", "."))
            if layout.variant == "header":
                duplicated = db.execute("SELECT groupkey FROM records GROUP BY groupkey HAVING count(*)>1 LIMIT 1").fetchone()
                if duplicated:
                    session.global_issues.append(Issue("ERRO", "CABECALHO_DUPLICADO", groupfield, "Número externo repetido na base de cabeçalhos; revise sem deduplicação automática."))
        if digest(source.path) != session.source_hash:
            raise ValueError("A origem mudou durante a leitura. Tente novamente com arquivo estável.")
        if not session.stats()["read"]:
            raise ValueError("Não há registros após o cabeçalho escolhido.")
        if source.format == "pdf" and not options.pdf_confirmed:
            session.global_issues.append(Issue("ERRO", "PDF_CONFERENCIA", "", "Confira a tabela extraída com a página do PDF original e confirme a revisão antes de exportar."))
        for warning in source.warnings:
            session.global_issues.append(Issue("AVISO", "LEITURA", "", warning))
        ignored = [h for sid, h in zip(source.ids, source.headers) if not any(d.source == sid and d.target for d in decisions)]
        if ignored:
            session.global_issues.append(Issue("AVISO", "COLUNAS_IGNORADAS", "", f"{len(ignored)} colunas não utilizadas; confira o mapeamento no relatório."))
        return session
    except BaseException:
        session.close()
        raise


def validate_links(main, related=None):
    """Cheque integridade referencial sem excluir/deduplicar nenhum registro."""
    issues = []
    if main.layout.variant in {"header", "items"}:
        if related is None:
            issues.append(Issue("ERRO", "BASE_VINCULADA", "", "Layouts separados exigem cabeçalhos e itens para validar vínculos e exportar as partes em conjunto."))
        elif main.layout.family != related.layout.family or {main.layout.variant, related.layout.variant} != {"header", "items"}:
            issues.append(Issue("ERRO", "MODELOS_VINCULADOS", "", "Selecione os modelos de cabeçalhos e itens da mesma família."))
        elif main.layout.path.parent != related.layout.path.parent:
            issues.append(Issue("ERRO", "VERSOES_VINCULADAS", "", "Use a mesma versão dos modelos para as bases vinculadas."))
        else:
            headers, items = (main, related) if main.layout.variant == "header" else (related, main)
            with headers.connect() as hdb, items.connect() as idb:
                hkeys = {r[0] for r in hdb.execute("SELECT DISTINCT groupkey FROM records")}
                ikeys = {r[0] for r in idb.execute("SELECT DISTINCT groupkey FROM records")}
            if ikeys - hkeys:
                issues.append(Issue("ERRO", "ITENS_ORFAOS", "", f"{len(ikeys - hkeys)} grupos de itens não têm cabeçalho. Nenhuma linha foi descartada."))
            if hkeys - ikeys:
                issues.append(Issue("AVISO", "CABECALHOS_SEM_ITENS", "", f"{len(hkeys - ikeys)} cabeçalhos não têm itens; confirme a origem."))
    return issues
