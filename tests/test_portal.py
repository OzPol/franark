from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from fastapi.testclient import TestClient

from franark.app import create_app
from franark.settings import Settings


class PortalTests(unittest.TestCase):
    def setUp(self):
        self.folder = TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.client = TestClient(create_app(Settings(data_dir=Path(self.folder.name))))
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)
        self.form = self.client.get("/api/portal/forms").json()[0]

    def create(self, answers=None, request_key="synthetic-request-001"):
        payload = {"form_key": "workflow-pilot@1.0", "client_ref": "SYN-001",
                   "answers": deepcopy(self.form["example"] if answers is None else answers), "request_key": request_key}
        response = self.client.post("/api/portal/submissions", json=payload)
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def submit(self, record, consent=True):
        response = self.client.post(f"/api/portal/submissions/{record['id']}/submit", json={
            "expected_revision": record["revision"], "signature": {"signer_name": "Synthetic signer", "consent": consent}})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def approve(self, record):
        response = self.client.post(f"/api/portal/submissions/{record['id']}/review", json={
            "expected_revision": record["revision"], "decision": "approve",
            "resolution": "Checked the synthetic answers and source values."})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_complete_pilot_and_exports(self):
        record = self.create()
        self.assertEqual(record["state"], "draft")
        self.assertEqual(self.client.get(f"/api/portal/submissions/{record['id']}/export/json").status_code, 409)
        record = self.submit(record)
        self.assertEqual(record["state"], "ready_for_review")
        self.assertEqual(record["signature"]["signed_payload_sha256"], record["payload_sha256"])
        self.assertIn("Synthetic Example", record["note"])
        record = self.approve(record)
        for format in ("json", "csv", "md", "pdf"):
            response = self.client.get(f"/api/portal/submissions/{record['id']}/export/{format}")
            self.assertEqual(response.status_code, 200, response.text[:100])
            if format == "pdf":
                self.assertTrue(response.content.startswith(b"%PDF-"))
            if format == "json":
                self.assertFalse(response.json()["vendor_import_ready"])

    def test_changed_birthdate_has_prior_source_and_requires_review(self):
        original = self.approve(self.submit(self.create()))
        answers = deepcopy(self.form["example"])
        answers["birthdate"] = "1940-02-11"
        changed = self.submit(self.create(answers, "synthetic-request-002"))
        self.assertEqual(changed["state"], "needs_review")
        finding = changed["findings"][0]
        self.assertEqual(finding["previous_submission_id"], original["id"])
        self.assertEqual(finding["previous_value"], "1940-02-10")
        self.assertEqual(finding["current_value"], "1940-02-11")
        draft = self.client.get(f"/api/portal/submissions/{changed['id']}/export/eml")
        self.assertEqual(draft.status_code, 200)
        self.assertIn("X-Unsent: 1", draft.text)
        self.assertNotIn("1940-02-10", draft.text)
        self.assertNotIn("1940-02-11", draft.text)

    def test_submitted_answers_are_immutable_and_correction_clears_signature(self):
        record = self.submit(self.create())
        path = f"/api/portal/submissions/{record['id']}"
        self.assertEqual(self.client.put(path, json={"expected_revision": record["revision"], "answers": {}}).status_code, 409)
        corrected = self.client.post(path + "/correction", json={"request_key": "correction-001"}).json()
        self.assertEqual(corrected["state"], "draft")
        self.assertEqual(corrected["supersedes_id"], record["id"])
        self.assertIsNone(corrected["signature"])
        original = self.client.get(path).json()
        self.assertEqual(original["answers"], record["answers"])

    def test_missing_answers_and_wrong_types_prevent_approval(self):
        answers = deepcopy(self.form["example"])
        del answers["observations"]
        answers["units"] = "two"
        record = self.submit(self.create(answers))
        self.assertTrue(all(finding["severity"] == "error" for finding in record["findings"]))
        response = self.client.post(f"/api/portal/submissions/{record['id']}/review", json={
            "expected_revision": record["revision"], "decision": "approve", "resolution": "Review attempted."})
        self.assertEqual(response.status_code, 409)

    def test_stale_draft_update_conflicts_without_overwriting(self):
        record = self.create()
        path = f"/api/portal/submissions/{record['id']}"
        payload = {"expected_revision": 1, "answers": {**record["answers"], "units": 3}}
        self.assertEqual(self.client.put(path, json=payload).status_code, 200)
        payload["answers"]["units"] = 9
        self.assertEqual(self.client.put(path, json=payload).status_code, 409)
        self.assertEqual(self.client.get(path).json()["answers"]["units"], 3)

    def test_duplicate_requests_are_idempotent_and_conflicting_input_rejected(self):
        first = self.create()
        second = self.create()
        self.assertEqual(first["id"], second["id"])
        payload = {"form_key": "workflow-pilot@1.0", "client_ref": "SYN-001", "answers": {}, "request_key": "synthetic-request-001"}
        self.assertEqual(self.client.post("/api/portal/submissions", json=payload).status_code, 409)

    def test_signature_consent_and_invalid_ink_are_rejected(self):
        record = self.create()
        path = f"/api/portal/submissions/{record['id']}/submit"
        payload = {"expected_revision": 1, "signature": {"signer_name": "Synthetic signer", "consent": False}}
        self.assertEqual(self.client.post(path, json=payload).status_code, 422)
        payload["signature"].update(consent=True, ink_png="data:image/png;base64,bm90LXB uZw==")
        self.assertEqual(self.client.post(path, json=payload).status_code, 422)

    def test_approved_correction_blocks_export_of_superseded_record(self):
        record = self.approve(self.submit(self.create()))
        correction = self.client.post(f"/api/portal/submissions/{record['id']}/correction", json={"request_key": "correction-001"}).json()
        self.approve(self.submit(correction))
        self.assertEqual(self.client.get(f"/api/portal/submissions/{record['id']}/export/json").status_code, 409)

    def test_no_model_fallback_is_claimed_when_unconfigured(self):
        record = self.submit(self.create())
        response = self.client.post(f"/api/portal/submissions/{record['id']}/ai-review", json={"expected_revision": record["revision"]})
        self.assertEqual(response.status_code, 503)
        self.assertIsNone(self.client.get(f"/api/portal/submissions/{record['id']}").json()["ai_review"])

    def test_readiness_contains_no_secret_and_reports_actual_backend(self):
        setup = self.client.get("/api/setup").json()
        self.assertEqual(setup["deployment_target"], "SFC tenant")
        self.assertEqual(setup["database"], "sqlite")
        self.assertTrue(setup["database_reachable"])
        self.assertGreater(len(setup["checklist"]), 0)
        self.assertEqual(self.client.get("/portal").status_code, 200)

    def test_csv_preview_escapes_spreadsheet_formulas(self):
        answers = {**self.form["example"], "client_name": "=1+1"}
        record = self.approve(self.submit(self.create(answers)))
        output = self.client.get(f"/api/portal/submissions/{record['id']}/export/csv").text
        self.assertIn("'=1+1", output)


class ModelReviewTests(unittest.TestCase):
    def test_fake_client_review_is_cached_and_cannot_approve(self):
        class Responses:
            calls = 0
            def create(self, **kwargs):
                self.calls += 1
                return SimpleNamespace(status="completed", output_text=json.dumps({
                    "summary": "Check the recorded unit count against the assessment source.", "evidence_ids": ["assessment"],
                    "artifacts": [], "questions": [], "outcome": "proposed"}))
        responses = Responses()
        with TemporaryDirectory() as folder, TestClient(create_app(Settings(
            data_dir=Path(folder), runtime="openai", api_key="synthetic-key", model="synthetic-model"),
            model_client=SimpleNamespace(responses=responses))) as client:
            form = client.get("/api/portal/forms").json()[0]
            record = client.post("/api/portal/submissions", json={"form_key": "workflow-pilot@1.0", "client_ref": "SYN-001", "answers": form["example"]}).json()
            record = client.post(f"/api/portal/submissions/{record['id']}/submit", json={"expected_revision": 1,
                "signature": {"signer_name": "Synthetic signer", "consent": True}}).json()
            path = f"/api/portal/submissions/{record['id']}/ai-review"
            reviewed = client.post(path, json={"expected_revision": record["revision"]})
            self.assertEqual(reviewed.status_code, 200, reviewed.text)
            self.assertEqual(reviewed.json()["state"], "ready_for_review")
            self.assertEqual(reviewed.json()["ai_review"]["model"], "synthetic-model")
            self.assertEqual(client.post(path, json={"expected_revision": reviewed.json()["revision"]}).status_code, 200)
            self.assertEqual(responses.calls, 1)


if __name__ == "__main__":
    unittest.main()
