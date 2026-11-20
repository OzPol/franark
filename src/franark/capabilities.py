"""Measured, source-preserving information services callable through Toolbox.

Research record: docs/research/methods.md; bibliography: references.bib.
These are engineering adaptations of A01–A06, not simulations of neural
mechanisms. Only A03 promises exact decoding; the other methods return views
and references while the caller retains the authoritative originals.
"""
from __future__ import annotations

import base64
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import time
from typing import Any, Callable
import zlib

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


METHOD_VERSION = "0.1.0"
MAX_INPUT_BYTES = 1_000_000


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def terms(text: str) -> list[str]:
    """Unicode words; no stemming, stop list, embeddings, or model tokenizer."""
    return re.findall(r"\w+", text.casefold())


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Document(Input):
    source_id: str = Field(min_length=1, max_length=200)
    version: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=16000)
    pinned: bool = False


class Selection(Input):
    query: str = Field(min_length=1, max_length=2000)
    documents: list[Document] = Field(min_length=1, max_length=64)
    budget_bytes: int = Field(default=8000, ge=32, le=50000)

    @model_validator(mode="after")
    def unique_sources(self):
        keys = [(doc.source_id, doc.version) for doc in self.documents]
        if len(keys) != len(set(keys)):
            raise ValueError("Each source ID and version pair must be unique.")
        return self


class Delta(Input):
    source_id: str = Field(min_length=1, max_length=200)
    base_version: str = Field(min_length=1, max_length=100)
    current_version: str = Field(min_length=1, max_length=100)
    before: dict[str, Any]
    after: dict[str, Any]


class Packing(Input):
    text: str = Field(max_length=200000)
    level: int = Field(default=6, ge=0, le=9)


class Projection(Input):
    source_id: str = Field(min_length=1, max_length=200)
    version: str = Field(min_length=1, max_length=100)
    record: dict[str, Any]
    fields: list[str] = Field(min_length=1, max_length=128)
    protected_fields: list[str] = Field(default_factory=list, max_length=128)

    @field_validator("fields", "protected_fields")
    @classmethod
    def json_pointers(cls, value):
        if any(not path.startswith("/") or re.search(r"~(?![01])", path)
               or len(path) > 500 for path in value):
            raise ValueError("Fields must be non-root RFC 6901 JSON Pointers.")
        return value


class Summary(Selection):
    relevance_weight: float = Field(default=0.7, ge=0.0, le=1.0)
    max_sentences: int = Field(default=8, ge=1, le=32)


class Snapshot(Input):
    event_id: str = Field(min_length=1, max_length=200)
    timestamp: str = Field(min_length=1, max_length=100)
    state: dict[str, Any]
    critical: bool = False

    @field_validator("timestamp")
    @classmethod
    def timestamp_with_timezone(cls, value):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.utcoffset() is None:
            raise ValueError("Timestamp must contain a timezone.")
        return value


class Timeline(Input):
    source_id: str = Field(min_length=1, max_length=200)
    snapshots: list[Snapshot] = Field(min_length=1, max_length=256)
    heartbeat_seconds: int = Field(default=86400, ge=1, le=31536000)

    @model_validator(mode="after")
    def ordered_events(self):
        stamps = [datetime.fromisoformat(s.timestamp.replace("Z", "+00:00"))
                  for s in self.snapshots]
        if stamps != sorted(stamps):
            raise ValueError("Snapshots must be in chronological order.")
        ids = [s.event_id for s in self.snapshots]
        if len(ids) != len(set(ids)):
            raise ValueError("Event IDs must be unique.")
        return self


def bm25(query: str, texts: list[str], k1: float = 1.2, b: float = 0.75) -> list[float]:
    """Positive-IDF BM25 variant; equation and assumptions in research docs."""
    bags = [Counter(terms(text)) for text in texts]
    lengths = [sum(bag.values()) for bag in bags]
    average = sum(lengths) / max(1, len(lengths)) or 1
    scores = [0.0] * len(texts)
    for term in sorted(set(terms(query))):
        df = sum(term in bag for bag in bags)
        idf = math.log(1 + (len(bags) - df + 0.5) / (df + 0.5))
        for index, bag in enumerate(bags):
            frequency = bag[term]
            denominator = frequency + k1 * (1 - b + b * lengths[index] / average)
            scores[index] += idf * frequency * (k1 + 1) / denominator
    return scores


def _budget(items, budget, relevant):
    """Whole-item greedy packing, including JSON envelope bytes; never truncate."""
    selected = [item for item in items if item["pinned"]]
    pinned_bytes = len(canonical(selected))
    if pinned_bytes > budget:
        raise ValueError("Pinned evidence exceeds the byte budget; increase it.")
    for item in items:
        if item["pinned"] or not relevant(item):
            continue
        if len(canonical([*selected, item])) <= budget:
            selected.append(item)
    return selected


def select_context(payload: Selection):
    scores = bm25(payload.query, [doc.text for doc in payload.documents])
    ranked = [{**doc.model_dump(), "score": round(score, 8)}
              for doc, score in zip(payload.documents, scores)]
    ranked.sort(key=lambda item: -item["score"])
    selected = _budget(ranked, payload.budget_bytes, lambda item: item["score"] > 0)
    keys = {(item["source_id"], item["version"]) for item in selected}
    return {"selected": selected, "selected_bytes": len(canonical(selected)),
            "omitted": [{"source_id": doc.source_id, "version": doc.version}
                        for doc in payload.documents if (doc.source_id, doc.version) not in keys],
            "complete": len(selected) == len(payload.documents),
            "limitations": ["Lexical retrieval can miss synonyms and necessary context. No factual-coverage guarantee."]}


def _pointer(key: str) -> str:
    return key.replace("~", "~0").replace("/", "~1")


def _diff(before, after, path=""):
    if isinstance(before, dict) and isinstance(after, dict):
        output = [{"op": "remove", "path": f"{path}/{_pointer(key)}"}
                  for key in sorted(before.keys() - after.keys())]
        for key in sorted(after):
            location = f"{path}/{_pointer(key)}"
            if key not in before:
                output.append({"op": "add", "path": location, "value": deepcopy(after[key])})
            else:
                output.extend(_diff(before[key], after[key], location))
        return output
    # JSON numeric 1 and 1.0 compare by canonical encoding here. Arrays are atomic.
    if canonical(before) == canonical(after):
        return []
    return [{"op": "replace", "path": path, "value": deepcopy(after)}]


def apply_delta(before: dict, packet: dict) -> dict:
    """Apply only this implementation's add/remove/replace patch subset."""
    if digest(before) != packet["base_sha256"]:
        raise ValueError("Base state does not match the delta.")
    result = deepcopy(before)
    for operation in packet["patch"]:
        path = operation["path"]
        if path == "":
            result = deepcopy(operation["value"])
            continue
        keys = [part.replace("~1", "/").replace("~0", "~") for part in path[1:].split("/")]
        parent = result
        for key in keys[:-1]:
            parent = parent[key]
        if operation["op"] == "remove":
            del parent[keys[-1]]
        elif operation["op"] in {"add", "replace"}:
            parent[keys[-1]] = deepcopy(operation["value"])
        else:
            raise ValueError("Unsupported patch operation.")
    if digest(result) != packet["current_sha256"]:
        raise ValueError("Reconstructed state does not match the delta.")
    return result


def state_delta(payload: Delta):
    packet = {"source_id": payload.source_id, "base_version": payload.base_version,
              "current_version": payload.current_version,
              "base_sha256": digest(payload.before), "current_sha256": digest(payload.after),
              "patch": _diff(payload.before, payload.after)}
    packet["exact_reconstruction_verified"] = apply_delta(payload.before, packet) == payload.after
    packet["limitations"] = ["Requires the exact base state. Field differences do not establish which value is correct."]
    return packet


def unpack_lossless(packet: dict, max_bytes: int = 200000) -> str:
    packed = base64.b64decode(packet["data_base64"], validate=True)
    decoder = zlib.decompressobj()
    raw = decoder.decompress(packed, max_bytes + 1)
    if len(raw) > max_bytes or not decoder.eof or decoder.unused_data:
        raise ValueError("Compressed payload is too large, incomplete, or contains trailing data.")
    if hashlib.sha256(raw).hexdigest() != packet["source_sha256"]:
        raise ValueError("Decoded payload hash differs from the source.")
    return raw.decode("utf-8")


def pack_lossless(payload: Packing):
    raw = payload.text.encode("utf-8")
    packet = {"format": "zlib+deflate+base64", "source_sha256": hashlib.sha256(raw).hexdigest(),
              "data_base64": base64.b64encode(zlib.compress(raw, payload.level)).decode("ascii")}
    packet["exact_reconstruction_verified"] = unpack_lossless(packet, max_bytes=max(1, len(raw))) == payload.text
    packet["source_bytes"] = len(raw)
    packet["limitations"] = ["Lossless storage encoding, not a shorter LLM prompt. Small inputs may grow after envelope/base64 overhead."]
    return packet


def _get(record, path):
    value = record
    for key in path[1:].split("/"):
        key = key.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            if not re.fullmatch(r"0|[1-9][0-9]*", key):
                raise KeyError(key)
            value = value[int(key)]
        else:
            value = value[key]
    return deepcopy(value)


def project_record(payload: Projection):
    fields, missing = {}, []
    for path in dict.fromkeys([*payload.protected_fields, *payload.fields]):
        try:
            fields[path] = _get(payload.record, path)
        except (KeyError, IndexError, TypeError):
            missing.append(path)
    return {"source_id": payload.source_id, "version": payload.version,
            "source_sha256": digest(payload.record), "fields": fields,
            "missing_fields": missing,
            "limitations": ["Explicit field projection; no learned manifold or semantic adequacy guarantee. The original record remains necessary."]}


def _cosine(left, right):
    numerator = sum(value * right.get(term, 0) for term, value in left.items())
    norm = math.sqrt(sum(value * value for value in left.values()) * sum(value * value for value in right.values()))
    return numerator / norm if norm else 0.0


def summarize_extractively(payload: Summary):
    candidates = []
    for doc in payload.documents:
        for match in re.finditer(r"\S[\s\S]*?(?:[.!?](?=\s|$)|\n|$)", doc.text):
            start, end = match.span()
            while start < end and doc.text[start].isspace():
                start += 1
            while end > start and doc.text[end - 1].isspace():
                end -= 1
            if start == end:
                continue
            candidates.append({"source_id": doc.source_id, "version": doc.version,
                               "start_char": start, "end_char": end,
                               "text": doc.text[start:end], "pinned": doc.pinned})
    if len(candidates) > 500:
        raise ValueError("More than 500 sentences; split the source packet explicitly.")
    if sum(item["pinned"] for item in candidates) > payload.max_sentences:
        raise ValueError("Pinned evidence exceeds the sentence limit; increase it.")
    scores = bm25(payload.query, [item["text"] for item in candidates])
    maximum = max(scores, default=0) or 1
    bags = [Counter(terms(item["text"])) for item in candidates]
    selected = [index for index, item in enumerate(candidates) if item["pinned"]]
    def representation(indices):
        return [candidates[index] for index in sorted(indices)]
    if len(canonical(representation(selected))) > payload.budget_bytes:
        raise ValueError("Pinned evidence exceeds the byte budget; increase it.")
    remaining = [index for index in range(len(candidates)) if index not in selected and scores[index] > 0]
    while remaining and len(selected) < payload.max_sentences:
        def mmr(index):
            redundancy = max((_cosine(bags[index], bags[other]) for other in selected), default=0)
            return payload.relevance_weight * scores[index] / maximum - (1 - payload.relevance_weight) * redundancy
        best = max(remaining, key=mmr)
        remaining.remove(best)
        if len(canonical(representation([*selected, best]))) <= payload.budget_bytes:
            selected.append(best)
    chosen = representation(selected)
    return {"sentences": chosen, "candidate_sentences": len(candidates),
            "selected_bytes": len(canonical(chosen)),
            "omitted_sentences": len(candidates) - len(chosen),
            "limitations": ["Extractive BM25+MMR baseline. Exact excerpts preserve wording, but omitted qualifications can still change interpretation. No NLI audit or semantic-drift score is claimed."]}


def event_timeline(payload: Timeline):
    kept = []
    previous_hash = None
    last_kept_time = None
    for index, event in enumerate(payload.snapshots):
        stamp = datetime.fromisoformat(event.timestamp.replace("Z", "+00:00"))
        state_hash = digest(event.state)
        reasons = []
        if index == 0:
            reasons.append("initial")
        elif state_hash != previous_hash:
            reasons.append("state_change")
        if event.critical:
            reasons.append("critical")
        if last_kept_time and (stamp - last_kept_time).total_seconds() >= payload.heartbeat_seconds:
            reasons.append("heartbeat")
        if index == len(payload.snapshots) - 1:
            reasons.append("final")
        if reasons:
            kept.append({**event.model_dump(), "state_sha256": state_hash,
                         "reasons": reasons, "coalesced_event_ids": []})
            last_kept_time = stamp
        else:
            kept[-1]["coalesced_event_ids"].append(event.event_id)
        previous_hash = state_hash
    return {"source_id": payload.source_id, "keyframes": kept,
            "input_events": len(payload.snapshots), "retained_events": len(kept),
            "limitations": ["Coalesces identical consecutive states only. Not statistical surprise detection, event-log storage, or a substitute for original timestamps and records."]}


@dataclass(frozen=True)
class Method:
    name: str
    label: str
    origin: str
    model: type[Input]
    function: Callable
    references: tuple[str, ...]
    description: str


METHODS = {
    method.name: method for method in (
        Method("memory.select", "Budgeted evidence selection", "A01", Selection, select_context,
               ("robertson2009", "lucene991"), "Rank supplied evidence with BM25 and select whole documents within a byte budget; preserve pinned evidence."),
        Method("memory.delta", "Versioned state differences", "A02", Delta, state_delta,
               ("rfc6902",), "Compute an exact, version-bound JSON Patch subset between supplied records; never decide which value is correct."),
        Method("memory.pack", "Lossless repeated-pattern encoding", "A03", Packing, pack_lossless,
               ("rfc1951",), "Encode text with DEFLATE in a zlib/base64 envelope and verify exact reconstruction. For storage, not prompt compression."),
        Method("memory.project", "Task-specific field projection", "A04", Projection, project_record,
               ("rfc6901",), "Return requested and protected fields with source/version references and explicit missing-field results."),
        Method("memory.summarize", "Source-linked extractive briefing", "A05", Summary, summarize_extractively,
               ("carbonell1998", "robertson2009", "lucene991"), "Select verbatim sentences using BM25 relevance and MMR redundancy control, retaining source offsets. Does not guarantee semantic completeness."),
        Method("memory.timeline", "Event-boundary timeline", "A06", Timeline, event_timeline,
               ("fowler2005",), "Coalesce identical consecutive snapshots while retaining every state change, critical event, heartbeat and final state."),
    )
}


def catalog():
    return [{"name": method.name, "label": method.label, "origin": method.origin,
             "version": METHOD_VERSION, "description": method.description,
             "references": list(method.references), "input_schema": method.model.model_json_schema()}
            for method in METHODS.values()]


def execute(name: str, arguments: dict) -> dict:
    """One measured execution; no network, SQL access, mail, or hidden storage."""
    if name not in METHODS:
        raise ValueError("Unknown information capability.")
    raw = canonical(arguments)
    if len(raw) > MAX_INPUT_BYTES:
        raise ValueError("Input exceeds the one-megabyte capability limit.")
    method = METHODS[name]
    payload = method.model.model_validate(arguments)
    wall_start, cpu_start = time.perf_counter_ns(), time.thread_time_ns()
    result = method.function(payload)
    serialized = canonical(result)
    cpu_ns, elapsed_ns = time.thread_time_ns() - cpu_start, time.perf_counter_ns() - wall_start
    return {"method": name, "method_version": METHOD_VERSION,
            "implementation_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "references": list(method.references), "result": result,
            "metrics": {"elapsed_ms": elapsed_ns / 1e6, "cpu_ms": cpu_ns / 1e6,
                        "input_bytes": len(raw), "output_bytes": len(serialized),
                        "input_to_output_ratio": len(raw) / len(serialized),
                        "input_sha256": hashlib.sha256(raw).hexdigest(),
                        "output_sha256": hashlib.sha256(serialized).hexdigest(),
                        "model_requests": 0, "model_tokens": None,
                        "semantic_fidelity": None, "power_watts": None}}


def handlers(recorder=None):
    def handler(name):
        def invoke(**arguments):
            result = execute(name, arguments)
            if recorder:
                recorder(result)
            return result
        return invoke
    return {name: handler(name) for name in METHODS}


def openai_tools(names):
    """Non-strict JSON-schema tools: Pydantic handles arbitrary JSON records.

    Strict mode cannot represent arbitrary record keys. All arguments are
    independently validated and bounded by execute() before execution.
    """
    return [{"type": "function", "name": name.replace(".", "_"),
             "description": METHODS[name].description,
             "parameters": METHODS[name].model.model_json_schema(), "strict": False}
            for name in names if name in METHODS]
