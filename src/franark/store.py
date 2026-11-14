"""SQLite run history and append-only workflow events."""
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
from uuid import uuid4


def now():
    return datetime.now(timezone.utc).isoformat()


class RequestConflict(ValueError):
    pass


class Store:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY, request_key TEXT UNIQUE NOT NULL,
                    fingerprint TEXT NOT NULL, title TEXT NOT NULL,
                    notes TEXT NOT NULL, domain TEXT NOT NULL,
                    runtime TEXT NOT NULL, status TEXT NOT NULL,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                    message TEXT NOT NULL DEFAULT ''
                );
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL REFERENCES runs(id),
                    kind TEXT NOT NULL, step_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL, result_json TEXT,
                    created_at TEXT NOT NULL
                );
            """)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def create(self, title, notes, domain, runtime, request_key):
        fingerprint = hashlib.sha256(json.dumps([title, notes, domain, runtime]).encode()).hexdigest()
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute("SELECT id, fingerprint FROM runs WHERE request_key = ?", (request_key,)).fetchone()
            if existing:
                if existing["fingerprint"] != fingerprint:
                    raise RequestConflict("This request key already belongs to a different input.")
                return existing["id"], False
            run_id = uuid4().hex
            db.execute("INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (run_id, request_key, fingerprint, title, notes, domain,
                        runtime, "queued", now(), now(), ""))
            return run_id, True

    def update(self, run_id, status, message=""):
        with self.connection() as db:
            db.execute("UPDATE runs SET status = ?, updated_at = ?, message = ? WHERE id = ?",
                       (status, now(), message, run_id))

    def event(self, run_id, kind, step_id, agent_id, result=None):
        with self.connection() as db:
            db.execute("INSERT INTO events (run_id, kind, step_id, agent_id, result_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                       (run_id, kind, step_id, agent_id,
                        json.dumps(asdict(result)) if result is not None else None, now()))

    def get(self, run_id):
        with self.connection() as db:
            row = db.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
            if row is None:
                return None
            result = dict(row)
            result.pop("request_key")
            result.pop("fingerprint")
            result["events"] = []
            for event in db.execute("SELECT * FROM events WHERE run_id = ? ORDER BY id", (run_id,)):
                item = dict(event)
                raw_result = item.pop("result_json")
                item["result"] = json.loads(raw_result) if raw_result else None
                result["events"].append(item)
            return result

    def recent(self):
        with self.connection() as db:
            return [dict(row) for row in db.execute(
                "SELECT id, title, domain, runtime, status, created_at, updated_at, message FROM runs ORDER BY created_at DESC LIMIT 100")]

    def recover_interrupted(self):
        with self.connection() as db:
            db.execute("UPDATE runs SET status = 'interrupted', updated_at = ?, message = ? WHERE status IN ('running', 'queued')",
                       (now(), "Application restarted during this run. Review recorded steps before starting again."))
