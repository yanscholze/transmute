"""Persistência mínima: histórico sem células, perfis estruturais e opções sem secrets."""
import json
from datetime import datetime

from app.storage.database import database


class LocalStore:
    def __init__(self, directory):
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path = directory / "history.sqlite3"
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS profiles(id INTEGER PRIMARY KEY, name TEXT, fingerprint TEXT, mapping TEXT);
                CREATE TABLE IF NOT EXISTS history(id INTEGER PRIMARY KEY, created TEXT, layout TEXT, stats TEXT, outcome TEXT);
                CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
            """)

    def connect(self):
        return database(self.path)

    def save_profile(self, name, fingerprint, mapping):
        with self.connect() as db:
            db.execute("INSERT INTO profiles(name,fingerprint,mapping) VALUES(?,?,?)", (name, fingerprint, json.dumps(mapping, ensure_ascii=False)))

    def profiles(self, fingerprint=None):
        with self.connect() as db:
            rows = db.execute("SELECT id,name,fingerprint,mapping FROM profiles ORDER BY id DESC").fetchall()
        return [(i, n, f, json.loads(m)) for i, n, f, m in rows if fingerprint is None or f == fingerprint]

    def delete_profile(self, ident):
        with self.connect() as db:
            db.execute("DELETE FROM profiles WHERE id=?", (ident,))

    def record(self, layout, stats, outcome):
        with self.connect() as db:
            db.execute("INSERT INTO history(created,layout,stats,outcome) VALUES(?,?,?,?)", (datetime.now().astimezone().isoformat(), layout, json.dumps(stats), outcome))

    def history(self):
        with self.connect() as db:
            return db.execute("SELECT created,layout,stats,outcome FROM history ORDER BY id DESC LIMIT 500").fetchall()

    def clear_history(self):
        with self.connect() as db:
            db.execute("DELETE FROM history")
            db.commit()
            db.execute("VACUUM")

    def setting(self, key, default=None):
        with self.connect() as db:
            row = db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def set_setting(self, key, value):
        # Credentials must never reach persistent configuration.
        if any(word in key.lower() for word in ("token", "secret", "password", "api_key")):
            raise ValueError("Credenciais não podem ser gravadas nas configurações.")
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO settings VALUES(?,?)", (key, json.dumps(value)))
