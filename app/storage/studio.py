"""Append-only local conversation/revision/run history; no credential storage."""
import json
from datetime import datetime


class StudioHistory:
    def __init__(self, local):
        self.local = local
        with local.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS studio_events(id INTEGER PRIMARY KEY, job_id TEXT NOT NULL, created TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL)")
            db.execute("CREATE INDEX IF NOT EXISTS studio_job ON studio_events(job_id,id)")

    def append(self, job_id, kind, payload):
        with self.local.connect() as db:
            result = db.execute("INSERT INTO studio_events(job_id,created,kind,payload) VALUES(?,?,?,?)",
                                (job_id, datetime.now().astimezone().isoformat(), kind, json.dumps(payload, ensure_ascii=False)))
            return result.lastrowid

    def list(self, job_id):
        with self.local.connect() as db:
            return [{"id": i, "created": c, "kind": k, "payload": json.loads(p)} for i, c, k, p in
                    db.execute("SELECT id,created,kind,payload FROM studio_events WHERE job_id=? ORDER BY id", (job_id,))]
