"""Transactional run history, measurements and portable relational storage."""
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from uuid import uuid4

from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError

from .database import events, make_engine, measurements, runs


def now():
    return datetime.now(timezone.utc).isoformat()


class RequestConflict(ValueError):
    pass


class Store:
    def __init__(self, path: Path, database_url="", sql_auth="managed_identity"):
        self.path = path
        self.engine = make_engine(path, database_url, sql_auth)

    @contextmanager
    def connection(self):
        with self.engine.begin() as db:
            yield db

    def create(self, title, notes, domain, runtime, request_key, owner_subject="local-pilot"):
        fingerprint = hashlib.sha256(json.dumps([title, notes, domain, runtime]).encode()).hexdigest()
        scoped_key = request_key if owner_subject == "local-pilot" else hashlib.sha256(
            (owner_subject + ":" + request_key).encode()).hexdigest()
        def existing():
            with self.connection() as db:
                row = db.execute(select(runs.c.id, runs.c.fingerprint).where(runs.c.request_key == scoped_key)).mappings().first()
            if row:
                if row["fingerprint"] != fingerprint:
                    raise RequestConflict("This request key already belongs to a different input.")
                return row["id"], False
        found = existing()
        if found:
            return found
        run_id = uuid4().hex
        try:
            with self.connection() as db:
                db.execute(insert(runs).values(id=run_id, request_key=scoped_key,
                    fingerprint=fingerprint, title=title, notes=notes, domain=domain,
                    runtime=runtime, status="queued", created_at=now(), updated_at=now(),
                    message="", owner_subject=owner_subject))
        except IntegrityError:
            found = existing()
            if found:
                return found
            raise
        return run_id, True

    def update(self, run_id, status, message=""):
        with self.connection() as db:
            db.execute(update(runs).where(runs.c.id == run_id).values(status=status, updated_at=now(), message=message))

    def event(self, run_id, kind, step_id, agent_id, result=None):
        with self.connection() as db:
            db.execute(insert(events).values(run_id=run_id, kind=kind, step_id=step_id,
                agent_id=agent_id, result_json=json.dumps(asdict(result)) if result is not None else None,
                created_at=now()))

    def get(self, run_id):
        with self.connection() as db:
            row = db.execute(select(runs).where(runs.c.id == run_id)).mappings().first()
            if row is None:
                return None
            result = dict(row)
            result.pop("request_key")
            result.pop("fingerprint")
            result["events"] = []
            for row in db.execute(select(events).where(events.c.run_id == run_id).order_by(events.c.id)).mappings():
                item = dict(row)
                raw_result = item.pop("result_json")
                item["result"] = json.loads(raw_result) if raw_result else None
                result["events"].append(item)
            return result

    def recent(self, owner_subject=None):
        columns = [runs.c[name] for name in ("id", "title", "domain", "runtime", "status", "created_at", "updated_at", "message")]
        statement = select(*columns).order_by(runs.c.created_at.desc()).limit(100)
        if owner_subject is not None:
            statement = statement.where(runs.c.owner_subject == owner_subject)
        with self.connection() as db:
            return [dict(row) for row in db.execute(statement).mappings()]

    def recover_interrupted(self):
        with self.connection() as db:
            db.execute(update(runs).where(runs.c.status.in_(["running", "queued"])).values(
                status="interrupted", updated_at=now(),
                message="Application restarted during this run. Review recorded steps before starting again."))

    def record_measurement(self, kind, metadata, run_id=None, owner_subject="local-pilot"):
        with self.connection() as db:
            db.execute(insert(measurements).values(run_id=run_id, kind=kind,
                metadata_json=json.dumps(metadata), created_at=now(), owner_subject=owner_subject))

    def measurements(self, limit=100, owner_subject=None):
        statement = select(measurements).order_by(measurements.c.id.desc()).limit(limit)
        if owner_subject is not None:
            statement = statement.where(measurements.c.owner_subject == owner_subject)
        with self.connection() as db:
            return [{"id": row["id"], "run_id": row["run_id"], "kind": row["kind"],
                     "created_at": row["created_at"], "metadata": json.loads(row["metadata_json"])}
                    for row in db.execute(statement).mappings()]

    def ping(self):
        from sqlalchemy import text
        with self.connection() as db:
            return db.execute(text("SELECT 1")).scalar_one() == 1
