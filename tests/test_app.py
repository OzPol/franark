from pathlib import Path
from tempfile import TemporaryDirectory
import time
import unittest

from fastapi.testclient import TestClient

from franark.app import create_app
from franark.pipeline import SAMPLE_NOTES
from franark.settings import Settings
from franark.store import RequestConflict, Store


class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self.folder = TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.settings = Settings(data_dir=Path(self.folder.name), api_key="never-expose-this")
        self.client = TestClient(create_app(self.settings))
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def payload(self):
        return {"title": "Synthetic IT notes", "notes": SAMPLE_NOTES,
                "domain": "it", "request_key": "request-12345678"}

    def wait_for_run(self, run_id):
        for _ in range(100):
            response = self.client.get(f"/api/runs/{run_id}").json()
            if response["status"] not in {"queued", "running"}:
                return response
            time.sleep(.02)
        self.fail("Demo run did not finish.")

    def test_demo_persists_ten_steps_and_export(self):
        created = self.client.post("/api/runs", json=self.payload())
        self.assertEqual(created.status_code, 202)
        run_id = created.json()["run_id"]
        run = self.wait_for_run(run_id)
        self.assertEqual(run["status"], "finished")
        self.assertEqual(len([e for e in run["events"] if e["kind"] == "result"]), 10)
        self.assertEqual(run["events"][-1]["result"]["outcome"], "accepted")
        export = self.client.get(f"/api/runs/{run_id}/report")
        self.assertIn("Gather the current device inventory", export.text)
        self.assertIn("DEMO", export.text)
        other_store = Store(Path(self.folder.name) / "franark.sqlite3")
        self.assertEqual(other_store.get(run_id)["status"], "finished")

    def test_duplicate_request_does_not_create_another_run(self):
        first = self.client.post("/api/runs", json=self.payload()).json()
        self.wait_for_run(first["run_id"])
        second = self.client.post("/api/runs", json=self.payload()).json()
        self.assertEqual(first["run_id"], second["run_id"])
        self.assertFalse(second["created"])
        self.assertEqual(len(self.client.get("/api/runs").json()), 1)

    def test_other_domain_workflows_finish_with_their_expected_steps(self):
        for domain, expected in (("general", 8), ("wellsky", 9), ("software", 9)):
            payload = self.payload()
            payload.update(domain=domain, request_key=f"request-{domain}-12345")
            created = self.client.post("/api/runs", json=payload).json()
            record = self.wait_for_run(created["run_id"])
            self.assertEqual(record["status"], "finished", domain)
            results = [event for event in record["events"] if event["kind"] == "result"]
            self.assertEqual(len(results), expected)

    def test_same_request_key_with_changed_content_conflicts(self):
        first = self.client.post("/api/runs", json=self.payload()).json()
        self.wait_for_run(first["run_id"])
        payload = self.payload()
        payload["notes"] += "Changed input"
        self.assertEqual(self.client.post("/api/runs", json=payload).status_code, 409)

    def test_key_is_absent_from_config_and_homepage(self):
        config = self.client.get("/api/config")
        self.assertNotIn("never-expose-this", config.text)
        self.assertEqual(len(config.json()["roles"]), 10)
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_capability_api_and_history_store_telemetry_without_source_content(self):
        config = self.client.get("/api/capabilities").json()
        self.assertEqual(len(config["methods"]), 6)
        self.assertEqual(self.client.get("/lab").status_code, 200)
        payload = {"name": "memory.pack", "arguments": {"text": "synthetic-private-document"}}
        response = self.client.post("/api/capabilities/execute", json=payload)
        self.assertEqual(response.status_code, 200)
        history = self.client.get("/api/measurements")
        self.assertEqual(len(history.json()), 1)
        self.assertNotIn("synthetic-private-document", history.text)
        self.assertNotIn("data_base64", history.text)
        self.assertNotIn("never-expose-this", history.text)

    def test_capability_api_rejects_invalid_inputs_and_cross_origin_calls(self):
        path = "/api/capabilities/execute"
        payload = {"name": "memory.pack", "arguments": {"text": "synthetic"}}
        self.assertEqual(self.client.post(path, json={"name": "mail.send", "arguments": {}}).status_code, 422)
        self.assertEqual(self.client.post(path, json=payload, headers={"origin": "https://other.example"}).status_code, 403)
        self.assertEqual(self.client.post(path, json={"name": "memory.pack", "arguments": {"text": "x" * 1001001}}).status_code, 413)

    def test_other_origin_cannot_submit_work(self):
        response = self.client.post("/api/runs", json=self.payload(),
                                    headers={"Origin": "https://unrelated.example"})
        self.assertEqual(response.status_code, 403)

    def test_unknown_run_and_invalid_input(self):
        self.assertEqual(self.client.get("/api/runs/unknown").status_code, 404)
        self.assertEqual(self.client.post("/api/runs", json={"notes": "short"}).status_code, 422)

    def test_model_mode_requires_credentials_and_model(self):
        settings = Settings(runtime="openai", data_dir=Path(self.folder.name) / "model")
        with TestClient(create_app(settings)) as client:
            self.assertEqual(client.post("/api/runs", json=self.payload()).status_code, 400)
            self.assertEqual(client.get("/api/runs").json(), [])

    def test_restart_records_interruption_without_replaying(self):
        store = self.client.app.state.store
        run_id, _ = store.create("Interrupted", SAMPLE_NOTES, "it", "demo", "interrupted-123")
        store.update(run_id, "running")
        store.recover_interrupted()
        self.assertEqual(store.get(run_id)["status"], "interrupted")
        self.assertEqual(store.get(run_id)["events"], [])


if __name__ == "__main__":
    unittest.main()
