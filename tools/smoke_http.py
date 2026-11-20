"""Check the running demo installation over HTTP, including a complete workflow."""
import argparse
from http.client import HTTPException
import json
import time
from urllib.error import URLError
from urllib.request import Request, urlopen
from uuid import uuid4


def fetch(url, payload=None, raw=False):
    body = json.dumps(payload).encode() if payload is not None else None
    request = Request(url, data=body, headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=3) as response:
        content = response.read()
        return content if raw else content.decode()


def wait_for(url, check):
    deadline = time.monotonic() + 30
    while True:
        try:
            content = fetch(url)
            if check(content):
                return content
        except (URLError, OSError, HTTPException):
            if time.monotonic() >= deadline:
                raise
        if time.monotonic() >= deadline:
            raise TimeoutError("Service did not become ready within 30 seconds.")
        time.sleep(.2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8765")
    parser.add_argument("--docs-url", default="http://127.0.0.1:8766")
    parser.add_argument("--skip-docs", action="store_true")
    args = parser.parse_args()
    wait_for(args.url + "/health", lambda content: json.loads(content)["status"] == "ok")
    config = json.loads(fetch(args.url + "/api/config"))
    if config["runtime"] != "demo":
        raise SystemExit("Select demo mode before running this installation check.")
    result = json.loads(fetch(args.url + "/api/runs", {
        "title": "Installation smoke test", "notes": config["sample_notes"],
        "domain": "it", "request_key": uuid4().hex,
    }))
    run_id = result["run_id"]
    deadline = time.monotonic() + 30
    while True:
        record = json.loads(fetch(args.url + "/api/runs/" + run_id))
        if record["status"] not in {"queued", "running"}:
            break
        if time.monotonic() >= deadline:
            raise SystemExit("Demo workflow did not finish within 30 seconds.")
        time.sleep(.2)
    assert record["status"] == "finished", record["message"]
    results = [event for event in record["events"] if event["kind"] == "result"]
    assert len(results) == 10
    assert results[-1]["result"]["outcome"] == "accepted"
    assert "DEMO" in fetch(args.url + "/api/runs/" + run_id + "/report")
    assert "Assessment and review" in fetch(args.url + "/portal")
    assert "System diagrams" in fetch(args.url + "/architecture")
    for name in ("context", "stack", "workflow", "records"):
        assert "<svg" in fetch(args.url + "/assets/diagrams/" + name + ".svg")
    form = json.loads(fetch(args.url + "/api/portal/forms"))[0]
    assessment = json.loads(fetch(args.url + "/api/portal/submissions", {
        "form_key": "workflow-pilot@1.0", "client_ref": "SYN-SMOKE-" + uuid4().hex[:8],
        "answers": form["example"], "request_key": uuid4().hex,
    }))
    path = args.url + "/api/portal/submissions/" + assessment["id"]
    assessment = json.loads(fetch(path + "/submit", {
        "expected_revision": assessment["revision"],
        "signature": {"signer_name": "Synthetic installation signer", "consent": True},
    }))
    assert assessment["state"] == "ready_for_review"
    assessment = json.loads(fetch(path + "/review", {
        "expected_revision": assessment["revision"], "decision": "approve",
        "resolution": "Synthetic installation record checked against the fixture.",
    }))
    assert assessment["state"] == "approved"
    assert fetch(path + "/export/pdf", raw=True).startswith(b"%PDF-")
    assert json.loads(fetch(path + "/export/json"))["vendor_import_ready"] is False
    if not args.skip_docs:
        wait_for(args.docs_url, lambda content: "Franark" in content)
    print("HTTP checks passed: application, ten-step agent workflow, assessment submission/review, PDF/JSON exports, diagrams" +
          (", and documentation." if not args.skip_docs else "."))


if __name__ == "__main__":
    main()
