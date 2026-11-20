from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from importlib.resources import files
from threading import BoundedSemaphore
from uuid import uuid4
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .pipeline import SAMPLE_NOTES, markdown_report, role_catalog, run_saved
from .settings import Settings
from .store import RequestConflict, Store
from .capabilities import MAX_INPUT_BYTES, catalog, execute


class RunRequest(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    notes: str = Field(min_length=10, max_length=20000)
    domain: Literal["general", "it", "wellsky", "software"] = "general"
    request_key: str = Field(default_factory=lambda: uuid4().hex, min_length=8, max_length=100)


class CapabilityRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    arguments: dict


def create_app(settings=None):
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app):
        app.state.store = Store(settings.data_dir / "franark.sqlite3")
        app.state.store.recover_interrupted()
        app.state.executor = ThreadPoolExecutor(max_workers=1)
        app.state.slots = BoundedSemaphore(3)
        yield
        app.state.executor.shutdown(wait=True)

    app = FastAPI(title="Franark", version="0.1.0", lifespan=lifespan)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"])

    @app.middleware("http")
    async def check_origin(request, call_next):
        origin = request.headers.get("origin")
        if request.method in {"POST", "PUT", "PATCH", "DELETE"} and origin:
            allowed = {str(request.base_url).rstrip("/")}
            if origin not in allowed:
                return JSONResponse({"detail": "Use the Franark tab for this action."}, status_code=403)
        if request.method == "POST" and request.url.path == "/api/capabilities/execute":
            if len(await request.body()) > MAX_INPUT_BYTES + 1000:
                return JSONResponse({"detail": "Capability request is too large."}, status_code=413)
        return await call_next(request)

    @app.get("/", response_class=HTMLResponse)
    def index():
        return files("franark").joinpath("static/index.html").read_text()

    @app.get("/lab", response_class=HTMLResponse)
    def lab():
        return files("franark").joinpath("static/lab.html").read_text()

    @app.get("/api/capabilities")
    def capabilities():
        resources = files("franark").joinpath("resources")
        import json
        return {"methods": catalog(),
                "examples": json.loads(resources.joinpath("capability_examples.json").read_text()),
                "references": json.loads(resources.joinpath("method_references.json").read_text()),
                "access": "Local development only; no Microsoft sign-in or business connectors configured."}

    @app.post("/api/capabilities/execute")
    def execute_capability(payload: CapabilityRequest, request: Request):
        try:
            measured = execute(payload.name, payload.arguments)
        except (ValueError, TypeError, RecursionError):
            raise HTTPException(422, "Inputs rejected. Check required fields, source IDs, limits, and pinned-evidence budget.") from None
        request.app.state.store.record_measurement(
            "capability", {key: value for key, value in measured.items() if key != "result"})
        return measured

    @app.get("/api/measurements")
    def measurements(request: Request):
        return request.app.state.store.measurements()

    @app.get("/health")
    def health():
        return {"status": "ok", "version": "0.1.0"}

    @app.get("/api/config")
    def config():
        return {
            "runtime": settings.runtime, "model": settings.model,
            "configured": settings.runtime == "demo" or bool(settings.api_key and settings.model),
            "max_calls": settings.max_calls, "sample_notes": SAMPLE_NOTES,
            "roles": [{"role_id": key, "display_name": value.display_name, "purpose": value.purpose} for key, value in role_catalog().items()],
        }

    @app.get("/api/runs")
    def runs(request: Request):
        return request.app.state.store.recent()

    @app.post("/api/runs", status_code=202)
    def create_run(payload: RunRequest, request: Request):
        if settings.runtime == "openai" and not (settings.api_key and settings.model):
            raise HTTPException(400, "Set OPENAI_API_KEY and FRANARK_MODEL in .env, then restart the app.")
        state = request.app.state
        if not state.slots.acquire(blocking=False):
            raise HTTPException(429, "Three runs are already queued or running. Wait for one to finish.")
        try:
            run_id, created = state.store.create(payload.title, payload.notes, payload.domain,
                                                 settings.runtime, payload.request_key)
        except RequestConflict as exc:
            state.slots.release()
            raise HTTPException(409, str(exc)) from exc
        except Exception:
            state.slots.release()
            raise
        if created:
            try:
                future = state.executor.submit(run_saved, state.store, run_id, settings)
                future.add_done_callback(lambda _: state.slots.release())
            except Exception:
                state.slots.release()
                state.store.update(run_id, "failed", "Worker could not start. Restart the app before retrying.")
                raise
        else:
            state.slots.release()
        return {"run_id": run_id, "created": created}

    @app.get("/api/runs/{run_id}")
    def run(run_id: str, request: Request):
        record = request.app.state.store.get(run_id)
        if record is None:
            raise HTTPException(404, "Run not found.")
        return record

    @app.get("/api/runs/{run_id}/report", response_class=PlainTextResponse)
    def report(run_id: str, request: Request):
        record = request.app.state.store.get(run_id)
        if record is None:
            raise HTTPException(404, "Run not found.")
        return PlainTextResponse(markdown_report(record), headers={
            "Content-Disposition": 'attachment; filename="franark-report.md"'})

    return app


app = create_app()
