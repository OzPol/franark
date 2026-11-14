"""Check the running demo installation over HTTP, including a complete workflow."""
import argparse
import json
import time
from urllib.error import URLError
from urllib.request import Request, urlopen
from uuid import uuid4


def fetch(url, payload=None):
    body = json.dumps(payload).encode() if payload is not None else None
    request = Request(url, data=body, headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=3) as response:
        return response.read().decode()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8765")
    parser.add_argument("--docs-url", default="http://127.0.0.1:8766")
    parser.add_argument("--skip-docs", action="store_true")
    args = parser.parse_args()
    deadline = time.monotonic() + 30
    while True:
        try:
            assert json.loads(fetch(args.url + "/health"))["status"] == "ok"
            break
        except (URLError, TimeoutError):
            if time.monotonic() >= deadline:
                raise
            time.sleep(.5)
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
    if not args.skip_docs:
        assert "Franark" in fetch(args.docs_url)
    print("HTTP checks passed: application, ten-step workflow, report" +
          (", and documentation." if not args.skip_docs else "."))


if __name__ == "__main__":
    main()
