"""Versioned synthetic assessment pilot, review gates and explicit exports."""
from __future__ import annotations

import base64
from copy import deepcopy
import csv
from datetime import date
from email.message import EmailMessage
from importlib.resources import files
from io import BytesIO, StringIO
import json
from pathlib import Path
import re
from typing import Any, Literal
from uuid import uuid4
from xml.sax.saxutils import escape

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import insert, or_, select, update
from sqlalchemy.exc import IntegrityError

from .capabilities import canonical, digest
from .database import form_definitions, submissions, submission_events
from .identity import Principal
from .store import RequestConflict, now


class PilotError(ValueError):
    def __init__(self, message, status=409):
        self.status = status
        super().__init__(message)


class FieldDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field_id: str = Field(pattern=r"^[a-z][a-z0-9_]{0,59}$")
    label: str = Field(min_length=1, max_length=150)
    type: Literal["text", "multiline", "date", "integer", "choice", "boolean"]
    required: bool = False
    choices: list[str] = Field(default_factory=list, max_length=50)
    minimum: int | None = None
    maximum: int | None = None
    compare_previous: bool = False
    not_future: bool = False


class FormDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    form_id: str = Field(pattern=r"^[a-z][a-z0-9-]{0,79}$")
    version: str = Field(pattern=r"^[A-Za-z0-9.-]{1,30}$")
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(max_length=2000)
    synthetic: bool = True
    requires_signature: bool = False
    fields: list[FieldDefinition] = Field(min_length=1, max_length=100)
    note_template: str = Field(min_length=1, max_length=10000)
    example: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_definition(self):
        ids = [field.field_id for field in self.fields]
        if len(ids) != len(set(ids)):
            raise ValueError("Form field IDs must be unique.")
        references = set(re.findall(r"\{\{([a-z][a-z0-9_]*)\}\}", self.note_template))
        if not references <= set(ids):
            raise ValueError("Note template references an unknown field.")
        if any(field.type == "choice" and not field.choices for field in self.fields):
            raise ValueError("Choice fields require answer options.")
        return self

    @property
    def key(self):
        return self.form_id + "@" + self.version


class DraftInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    form_key: str = Field(min_length=1, max_length=150)
    client_ref: str = Field(pattern=r"^SYN-[A-Za-z0-9-]{1,90}$")
    answers: dict[str, Any]
    request_key: str = Field(default_factory=lambda: uuid4().hex, min_length=8, max_length=100)
    reviewer_subject: str | None = Field(default=None, max_length=200)


class DraftUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=1)
    answers: dict[str, Any]


class SignatureInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    signer_name: str = Field(min_length=2, max_length=200)
    consent: bool
    ink_png: str = Field(default="", max_length=360000)


class SubmitInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=1)
    signature: SignatureInput | None = None


class ReviewInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=1)
    decision: Literal["approve", "request_changes"]
    resolution: str = Field(min_length=8, max_length=4000)


def _limited_answers(answers):
    try:
        encoded = canonical(answers)
    except (ValueError, TypeError, RecursionError):
        raise PilotError("Answers must contain finite JSON values within the pilot limits.", 422) from None
    if len(answers) > 100 or len(encoded) > 50000:
        raise PilotError("Answers exceed the pilot limits.", 422)


def validate_answers(form: FormDefinition, answers: dict, previous: dict | None = None):
    findings = []
    known = {field.field_id for field in form.fields}
    for unknown in answers.keys() - known:
        findings.append({"id": f"{unknown}.unknown", "field": unknown, "severity": "error", "message": "The answer does not belong to this form version."})
    for field in form.fields:
        value = answers.get(field.field_id)
        empty = value is None or (isinstance(value, str) and not value.strip())
        message = None
        if empty:
            if field.required:
                message = f"{field.label} is required."
        elif field.type == "integer":
            if type(value) is not int:
                message = f"{field.label} must be an integer."
            elif field.minimum is not None and value < field.minimum or field.maximum is not None and value > field.maximum:
                message = f"{field.label} is outside the configured range."
        elif field.type == "boolean":
            if type(value) is not bool:
                message = f"{field.label} must be yes or no."
        elif not isinstance(value, str) or len(value) > 4000:
            message = f"{field.label} must contain at most 4000 text characters."
        elif field.type == "choice" and value not in field.choices:
            message = f"{field.label} is not one of the permitted answers."
        elif field.type == "date":
            try:
                parsed = date.fromisoformat(value)
                if parsed.isoformat() != value or field.not_future and parsed > date.today():
                    raise ValueError("Date outside the permitted format/range.")
            except ValueError:
                message = f"{field.label} requires a valid permitted date in YYYY-MM-DD format."
        if message:
            findings.append({"id": f"{field.field_id}.validation", "field": field.field_id, "severity": "error", "message": message})
        elif not empty and field.compare_previous and previous is not None and field.field_id in previous and previous[field.field_id] != value:
            findings.append({"id": f"{field.field_id}.changed", "field": field.field_id, "severity": "warning",
                             "message": f"{field.label} differs from the previous approved record. This may be an intended correction; please confirm the value.",
                             "previous_value": previous[field.field_id], "current_value": value})
    return findings


def render_note(form: FormDefinition, answers: dict):
    def substitute(match):
        value = answers.get(match.group(1))
        if value is None or value == "":
            return "Not recorded"
        if type(value) is bool:
            return "Yes" if value else "No"
        return str(value)
    return re.sub(r"\{\{([a-z][a-z0-9_]*)\}\}", substitute, form.note_template)


def verify_signature(signature: SignatureInput, payload_sha256: str, actor: Principal):
    if not signature.consent or not signature.signer_name.strip():
        raise PilotError("Signature acknowledgement requires a signer name and consent.", 422)
    if signature.ink_png:
        if not signature.ink_png.startswith("data:image/png;base64,"):
            raise PilotError("Signature ink must be a PNG.", 422)
        try:
            raw = base64.b64decode(signature.ink_png.split(",", 1)[1], validate=True)
            if len(raw) > 256000:
                raise ValueError("Ink exceeds the size limit.")
            from PIL import Image
            with Image.open(BytesIO(raw)) as image:
                if image.format != "PNG" or image.width * image.height > 2_000_000:
                    raise ValueError("Invalid signature dimensions.")
                image.verify()
        except Exception:
            raise PilotError("Signature PNG is invalid or exceeds the size limit.", 422) from None
    return {**signature.model_dump(), "recorded_at": now(), "witness_subject": actor.subject,
            "signed_payload_sha256": payload_sha256, "assurance": "synthetic pilot acknowledgement; no signature-provider validation"}


class Portal:
    def __init__(self, store, public_origin="http://127.0.0.1:8765"):
        self.store = store
        self.public_origin = public_origin
        for data in json.loads(files("franark").joinpath("resources/pilot_forms.json").read_text()):
            self.register_form(FormDefinition.model_validate(data))

    def register_form(self, form):
        if not form.synthetic:
            raise PilotError("The current pilot accepts synthetic form definitions only.", 422)
        encoded = json.dumps(form.model_dump(), ensure_ascii=False)
        with self.store.connection() as db:
            row = db.execute(select(form_definitions).where(form_definitions.c.form_key == form.key)).mappings().first()
        if row:
            if digest(json.loads(row["definition_json"])) != digest(form.model_dump()):
                raise PilotError("An existing form version cannot be overwritten.")
            return
        try:
            with self.store.connection() as db:
                db.execute(insert(form_definitions).values(form_key=form.key, definition_json=encoded, created_at=now()))
        except IntegrityError:
            return self.register_form(form)

    def forms(self):
        with self.store.connection() as db:
            return [json.loads(row[0]) for row in db.execute(select(form_definitions.c.definition_json))]

    def form(self, key):
        with self.store.connection() as db:
            raw = db.execute(select(form_definitions.c.definition_json).where(form_definitions.c.form_key == key)).scalar_one_or_none()
        if raw is None:
            raise PilotError("Form version not found.", 404)
        return FormDefinition.model_validate_json(raw)

    def _event(self, db, record_id, actor, action, detail):
        db.execute(insert(submission_events).values(submission_id=record_id, actor_subject=actor.subject,
            action=action, detail_json=json.dumps(detail, ensure_ascii=False), created_at=now()))

    def list(self, actor):
        columns = [submissions.c[key] for key in ("id", "client_ref", "form_key", "state", "revision", "created_at", "updated_at")]
        statement = select(*columns).order_by(submissions.c.created_at.desc()).limit(100)
        if not actor.is_admin:
            statement = statement.where(or_(submissions.c.owner_subject == actor.subject,
                submissions.c.reviewer_subject == actor.subject))
        with self.store.connection() as db:
            return [dict(row) for row in db.execute(statement).mappings()]

    def get(self, record_id, actor):
        with self.store.connection() as db:
            row = db.execute(select(submissions).where(submissions.c.id == record_id)).mappings().first()
            if row is None or not (actor.is_admin or actor.subject in {row["owner_subject"], row["reviewer_subject"]}):
                raise PilotError("Submission not found.", 404)
            result = dict(row)
            result.pop("request_key")
            result.pop("fingerprint")
            for field in ("answers", "signature", "findings", "ai_review"):
                raw = result.pop(field + "_json")
                result[field] = json.loads(raw) if raw else None
            result["events"] = [{"action": item["action"], "actor_subject": item["actor_subject"],
                                 "created_at": item["created_at"], "detail": json.loads(item["detail_json"])}
                                for item in db.execute(select(submission_events).where(
                                    submission_events.c.submission_id == record_id).order_by(submission_events.c.id)).mappings()]
        result["form"] = self.form(result["form_key"]).model_dump()
        return result

    def create(self, payload: DraftInput, actor, supersedes_id=None):
        _limited_answers(payload.answers)
        form = self.form(payload.form_key)
        if not form.synthetic:
            raise PilotError("Only synthetic pilot forms are enabled.", 422)
        request_key = digest([actor.subject, payload.request_key])
        fingerprint = digest([payload.form_key, payload.client_ref, payload.answers, payload.reviewer_subject, supersedes_id])
        with self.store.connection() as db:
            row = db.execute(select(submissions.c.id, submissions.c.fingerprint).where(submissions.c.request_key == request_key)).mappings().first()
        if row:
            if row["fingerprint"] != fingerprint:
                raise RequestConflict("The request key belongs to different assessment input.")
            return self.get(row["id"], actor)
        record_id = uuid4().hex
        body_hash = digest([payload.form_key, payload.client_ref, payload.answers])
        try:
            with self.store.connection() as db:
                db.execute(insert(submissions).values(id=record_id, request_key=request_key, fingerprint=fingerprint,
                    form_key=payload.form_key, client_ref=payload.client_ref, owner_subject=actor.subject,
                    reviewer_subject=payload.reviewer_subject, state="draft", revision=1,
                    answers_json=json.dumps(payload.answers, ensure_ascii=False), findings_json="[]", note="",
                    payload_sha256=body_hash, supersedes_id=supersedes_id, created_at=now(), updated_at=now()))
                self._event(db, record_id, actor, "draft_created", {"revision": 1, "payload_sha256": body_hash})
        except IntegrityError:
            return self.create(payload, actor, supersedes_id)
        return self.get(record_id, actor)

    def _change(self, record, actor, expected_revision, values, action, detail):
        with self.store.connection() as db:
            changed = db.execute(update(submissions).where(submissions.c.id == record["id"],
                submissions.c.revision == expected_revision, submissions.c.state == record["state"]).values(
                    **values, revision=expected_revision + 1, updated_at=now()))
            if changed.rowcount != 1:
                raise PilotError("The record changed. Reload it before retrying.")
            self._event(db, record["id"], actor, action, {**detail, "revision": expected_revision + 1})
        return self.get(record["id"], actor)

    def edit(self, record_id, payload: DraftUpdate, actor):
        record = self.get(record_id, actor)
        if record["state"] != "draft" or not (actor.is_admin or record["owner_subject"] == actor.subject):
            raise PilotError("Only an owned draft can be edited.")
        _limited_answers(payload.answers)
        return self._change(record, actor, payload.expected_revision,
            {"answers_json": json.dumps(payload.answers, ensure_ascii=False),
             "payload_sha256": digest([record["form_key"], record["client_ref"], payload.answers])}, "draft_updated", {})

    def submit(self, record_id, payload: SubmitInput, actor):
        record = self.get(record_id, actor)
        if record["state"] != "draft" or not (actor.is_admin or record["owner_subject"] == actor.subject):
            raise PilotError("Only an owned draft can be submitted.")
        form = self.form(record["form_key"])
        signature = verify_signature(payload.signature, record["payload_sha256"], actor) if payload.signature else None
        if form.requires_signature and signature is None:
            raise PilotError("This test form requires a signature acknowledgement.", 422)
        statement = select(submissions.c.id, submissions.c.revision, submissions.c.answers_json).where(submissions.c.client_ref == record["client_ref"],
            submissions.c.form_key == record["form_key"], submissions.c.state == "approved").order_by(submissions.c.updated_at.desc()).limit(1)
        if not actor.is_admin:
            statement = statement.where(submissions.c.owner_subject == actor.subject)
        with self.store.connection() as db:
            previous = db.execute(statement).mappings().first()
        findings = validate_answers(form, record["answers"], json.loads(previous["answers_json"]) if previous else None)
        for finding in findings:
            if finding["severity"] == "warning" and previous:
                finding["previous_submission_id"] = previous["id"]
                finding["previous_revision"] = previous["revision"]
        return self._change(record, actor, payload.expected_revision,
            {"state": "needs_review" if findings else "ready_for_review",
             "signature_json": json.dumps(signature, ensure_ascii=False) if signature else None,
             "findings_json": json.dumps(findings, ensure_ascii=False), "note": render_note(form, record["answers"])},
            "submitted", {"finding_ids": [finding["id"] for finding in findings], "payload_sha256": record["payload_sha256"]})

    def review(self, record_id, payload: ReviewInput, actor):
        record = self.get(record_id, actor)
        if not actor.can_review or not (actor.is_admin or record["reviewer_subject"] == actor.subject):
            raise PilotError("An assigned reviewer role is required.", 403)
        if record["state"] not in {"needs_review", "ready_for_review"}:
            raise PilotError("The submission is not awaiting review.")
        if payload.decision == "approve" and any(finding["severity"] == "error" for finding in record["findings"]):
            raise PilotError("Validation errors require a corrected draft before approval.")
        return self._change(record, actor, payload.expected_revision,
            {"state": "approved" if payload.decision == "approve" else "changes_requested"},
            "reviewed", {"decision": payload.decision, "resolution": payload.resolution,
                         "synthetic_self_review": actor.subject == record["owner_subject"]})

    def correct(self, record_id, request_key, actor):
        record = self.get(record_id, actor)
        if record["state"] == "draft" or not (actor.is_admin or record["owner_subject"] == actor.subject):
            raise PilotError("A submitted, owned record is required for a correction draft.")
        return self.create(DraftInput(form_key=record["form_key"], client_ref=record["client_ref"],
            answers=deepcopy(record["answers"]), request_key=request_key,
            reviewer_subject=record["reviewer_subject"]), actor, supersedes_id=record_id)

    def save_ai_review(self, record_id, revision, actor, result):
        record = self.get(record_id, actor)
        if record["state"] not in {"needs_review", "ready_for_review"}:
            raise PilotError("AI review requires a submitted record awaiting human review.")
        return self._change(record, actor, revision, {"ai_review_json": json.dumps(result, ensure_ascii=False)},
                            "ai_review_drafted", {"model": result["model"], "business_state_unchanged": True})

    def export(self, record_id, format, actor):
        record = self.get(record_id, actor)
        if format != "eml" and record["state"] != "approved":
            raise PilotError("Human approval is required before export.")
        if format != "eml":
            with self.store.connection() as db:
                newer = db.execute(select(submissions.c.id).where(submissions.c.supersedes_id == record_id,
                    submissions.c.state == "approved").limit(1)).scalar_one_or_none()
            if newer:
                raise PilotError("A newer approved correction supersedes this record.")
        if format == "json":
            output, media = canonical({"format": "franark-pilot-record-v1", "vendor_import_ready": False, "record": record}), "application/json"
        elif format == "csv":
            def cell(value):
                value = str(value)
                return "'" + value if value.startswith(("=", "+", "-", "@", "\t", "\r")) else value
            stream = StringIO()
            writer = csv.writer(stream)
            writer.writerow(["client_ref", "form_key", "payload_sha256", *record["answers"].keys()])
            writer.writerow([cell(record["client_ref"]), cell(record["form_key"]), record["payload_sha256"], *[cell(value) for value in record["answers"].values()]])
            output, media = stream.getvalue().encode("utf-8-sig"), "text/csv"
        elif format == "md":
            output, media = (record["note"] + "\n\nSynthetic pilot · submission " + record_id + "\n").encode(), "text/markdown"
        elif format == "pdf":
            output, media = render_pdf(record), "application/pdf"
        elif format == "eml":
            if not record["findings"]:
                raise PilotError("No findings are available for a review notification.")
            message = EmailMessage()
            message["Subject"] = "Please review one detail in a synthetic assessment"
            message["X-Unsent"] = "1"
            message.set_content("Hello,\n\nCould you check the flagged details in synthetic assessment " + record_id +
                "? A value may be an intended correction; please confirm the information before release.\n\n" +
                "Review record: " + self.public_origin + "/portal?record=" + record_id + "\n\nThank you.\n")
            output, media = message.as_bytes(), "message/rfc822"
        else:
            raise PilotError("Unsupported pilot export format.", 422)
        with self.store.connection() as db:
            self._event(db, record_id, actor, "export_generated", {"format": format, "bytes": len(output), "destination_transfer": False})
        return output, media


def render_pdf(record):
    import reportlab
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
    font_path = Path(reportlab.__file__).parent / "fonts" / "Vera.ttf"
    if "FranarkVera" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("FranarkVera", str(font_path)))
    styles = getSampleStyleSheet()
    for style in styles.byName.values():
        style.fontName = "FranarkVera"
        style.textColor = colors.black
    stream = BytesIO()
    document = SimpleDocTemplate(stream, title="Franark synthetic assessment", author="Franark", invariant=1)
    parts = [Paragraph("Synthetic assessment pilot", styles["Title"]),
             Paragraph("Workflow test document. Not an official 701 assessment or provider-certified signature.", styles["Normal"]), Spacer(1, 14)]
    for line in record["note"].splitlines():
        parts.append(Paragraph(escape(line) or " ", styles["Normal"]))
        parts.append(Spacer(1, 6))
    signature = record["signature"]
    if signature:
        parts += [Spacer(1, 12), Paragraph("Acknowledgement: " + escape(signature["signer_name"]), styles["Normal"])]
        if signature["ink_png"]:
            image = Image(BytesIO(base64.b64decode(signature["ink_png"].split(",", 1)[1])))
            image._restrictSize(300, 90)
            parts.append(image)
        parts.append(Paragraph("Recorded: " + escape(signature["recorded_at"]), styles["Normal"]))
    parts += [Spacer(1, 14), Paragraph("Submission: " + record["id"], styles["Normal"]),
              Paragraph("Payload SHA-256: " + record["payload_sha256"], styles["Normal"])]
    document.build(parts)
    return stream.getvalue()
