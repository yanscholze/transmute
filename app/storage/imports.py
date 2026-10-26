"""Importações nomeadas: referências persistentes sem duplicar bases completas.

As referências a arquivos são necessárias para reabrir uma importação. Dados
de revisão completos continuam em sessões temporárias. Correções manuais
necessárias à retomada podem conter dados pessoais e ficam no manifesto local.
A tabela nova preserva histórico,
perfis e configurações existentes na mesma base SQLite.
"""
import json
import copy
import uuid
from datetime import datetime

FAMILIES = {"veiculos": "Veículos", "clientes": "Clientes", "fornecedores": "Fornecedores",
            "produtos": "Produtos e serviços", "os": "Ordens de serviço", "vendas": "Vendas",
            "pagar": "Contas a pagar", "receber": "Contas a receber", "generic": "Outra tabela"}


def now():
    # Multiple saves/new jobs within one second must still sort chronologically.
    return datetime.now().astimezone().isoformat(timespec="microseconds")


class ImportStore:
    def __init__(self, local):
        self.local = local
        with local.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS imports_v1(id TEXT PRIMARY KEY, manifest TEXT NOT NULL)")
        # No worker survives app shutdown. Preserve its manifest and show recovery.
        for job in self.list():
            if job["status"] == "Em processamento":
                job["status"] = "Interrompida"
                self.save(job)

    def create(self, name, categories, attachments, options, mode="classic"):
        name = name.strip()
        if not name or len(name) > 120:
            raise ValueError("Dê um nome à importação, com até 120 caracteres.")
        if not categories or any(c not in FAMILIES for c in categories):
            raise ValueError("Selecione ao menos uma categoria válida.")
        if not attachments or any(a["family"] not in categories for a in attachments):
            raise ValueError("Adicione arquivos e classifique-os nas categorias selecionadas.")
        if mode not in {"classic", "studio"}:
            raise ValueError("Modo de conversão desconhecido.")
        if mode == "classic" and set(categories) - {a["family"] for a in attachments}:
            raise ValueError("Adicione ao menos um arquivo a cada categoria selecionada.")
        job = {"id": uuid.uuid4().hex, "name": name, "created": now(), "updated": now(), "status": "Aguardando processamento",
               "categories": categories, "attachments": attachments, "options": options, "exports": []}
        job["mode"] = mode
        if mode == "studio":
            job["studio"] = {"instructions": "", "sources": copy.deepcopy(attachments), "plan": None, "approval": None}
        self.save(job)
        return job

    def save(self, job):
        job["updated"] = now()
        with self.local.connect() as db:
            db.execute("INSERT OR REPLACE INTO imports_v1 VALUES(?,?)", (job["id"], json.dumps(job, ensure_ascii=False)))

    def get(self, identifier):
        with self.local.connect() as db:
            row = db.execute("SELECT manifest FROM imports_v1 WHERE id=?", (identifier,)).fetchone()
        if not row:
            raise ValueError("Importação não encontrada.")
        return json.loads(row[0])

    def list(self):
        with self.local.connect() as db:
            jobs = [json.loads(r[0]) for r in db.execute("SELECT manifest FROM imports_v1")]
        return sorted(jobs, key=lambda j: j["updated"], reverse=True)
