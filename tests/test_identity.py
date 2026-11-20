from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from cryptography.hazmat.primitives.asymmetric import rsa
import jwt
from fastapi.testclient import TestClient

from franark.app import create_app
from franark.identity import EntraAuthenticator
from franark.settings import Settings

TENANT = "11111111-1111-4111-8111-111111111111"
CLIENT = "22222222-2222-4222-8222-222222222222"


class IdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def setUp(self):
        self.folder = TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.settings = Settings(data_dir=Path(self.folder.name), auth_mode="entra", tenant_id=TENANT,
            client_id=CLIENT, public_origin="https://sfc-pilot.example.test", allowed_hosts=("sfc-pilot.example.test",))
        key_client = SimpleNamespace(get_signing_key_from_jwt=lambda token: SimpleNamespace(key=self.key.public_key()))
        self.authenticator = EntraAuthenticator(self.settings, key_client)
        self.client = TestClient(create_app(self.settings, authenticator=self.authenticator), base_url="https://sfc-pilot.example.test")
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def token(self, subject="employee-a", roles=None, **overrides):
        now = datetime.now(timezone.utc)
        claims = {"exp": now + timedelta(minutes=5), "iat": now, "iss": f"https://login.microsoftonline.com/{TENANT}/v2.0",
                  "aud": CLIENT, "tid": TENANT, "oid": subject, "roles": roles if roles is not None else ["Franark.Pilot"]}
        claims.update(overrides)
        return {"Authorization": "Bearer " + jwt.encode(claims, self.key, algorithm="RS256")}

    def test_missing_token_or_forged_principal_header_is_denied(self):
        self.assertEqual(self.client.get("/api/identity").status_code, 401)
        self.assertEqual(self.client.get("/api/identity", headers={"X-MS-CLIENT-PRINCIPAL": "forged"}).status_code, 401)

    def test_valid_assigned_sfc_token_and_platform_token_work(self):
        headers = self.token()
        response = self.client.get("/api/identity", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["subject"], "employee-a")
        self.assertEqual(response.headers["cache-control"], "no-store")
        token = headers["Authorization"][7:]
        self.assertEqual(self.client.get("/api/identity", headers={"X-MS-TOKEN-AAD-ID-TOKEN": token}).status_code, 200)

    def test_foreign_tenant_wrong_audience_issuer_and_expiry_are_rejected(self):
        for overrides in ({"tid": CLIENT}, {"aud": "other-app"}, {"iss": "https://wrong.example"},
                          {"exp": datetime.now(timezone.utc) - timedelta(minutes=5)}):
            self.assertEqual(self.client.get("/api/identity", headers=self.token(**overrides)).status_code, 401)

    def test_unassigned_identity_and_non_matching_roles_are_denied(self):
        for roles in ([], ["Admin"], ["AnotherApplication.Admin"]):
            self.assertEqual(self.client.get("/api/identity", headers=self.token(roles=roles)).status_code, 403)

    def test_wrong_signature_and_algorithm_are_denied(self):
        other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        valid = jwt.decode(self.token()["Authorization"][7:], options={"verify_signature": False})
        for token in (jwt.encode(valid, other, algorithm="RS256"), jwt.encode(valid, "synthetic-hmac-key-at-least-32-characters", algorithm="HS256")):
            self.assertEqual(self.client.get("/api/identity", headers={"Authorization": "Bearer " + token}).status_code, 401)

    def test_ownership_prevents_cross_user_reads_and_request_key_collisions(self):
        a, b = self.token(), self.token(subject="employee-b")
        payload = {"title": "Synthetic ownership run", "notes": "ACTION: Check the synthetic record", "domain": "general", "request_key": "shared-key-123"}
        first = self.client.post("/api/runs", json=payload, headers=a).json()
        second = self.client.post("/api/runs", json=payload, headers=b).json()
        self.assertNotEqual(first["run_id"], second["run_id"])
        self.assertEqual(self.client.get("/api/runs/" + first["run_id"], headers=b).status_code, 404)
        self.assertEqual(self.client.get("/api/runs/" + first["run_id"] + "/report", headers=b).status_code, 404)
        self.assertEqual(len(self.client.get("/api/runs", headers=b).json()), 1)

    def test_portal_record_scope_and_review_roles_are_enforced(self):
        a, b = self.token(), self.token(subject="employee-b")
        reviewer = self.token(subject="assigned-reviewer", roles=["Franark.Reviewer"])
        form = self.client.get("/api/portal/forms", headers=a).json()[0]
        record = self.client.post("/api/portal/submissions", headers=a, json={"form_key": "workflow-pilot@1.0",
            "client_ref": "SYN-001", "answers": form["example"], "reviewer_subject": "assigned-reviewer"}).json()
        path = "/api/portal/submissions/" + record["id"]
        self.assertEqual(self.client.get(path, headers=b).status_code, 404)
        self.assertEqual(self.client.get(path, headers=reviewer).status_code, 200)
        submitted = self.client.post(path + "/submit", headers=a, json={"expected_revision": 1,
            "signature": {"signer_name": "Synthetic signer", "consent": True}}).json()
        review = {"expected_revision": submitted["revision"], "decision": "approve", "resolution": "Checked the synthetic example."}
        self.assertEqual(self.client.post(path + "/review", headers=a, json=review).status_code, 403)
        self.assertEqual(self.client.post(path + "/review", headers=reviewer, json=review).status_code, 200)

    def test_non_admin_cannot_read_setup_or_another_users_measurements(self):
        a, b = self.token(), self.token(subject="employee-b")
        self.assertEqual(self.client.get("/api/setup", headers=a).status_code, 403)
        self.client.post("/api/capabilities/execute", headers=a, json={"name": "memory.pack", "arguments": {"text": "synthetic"}})
        self.assertEqual(self.client.get("/api/measurements", headers=b).json(), [])

    def test_local_mode_cannot_be_exposed_on_an_external_host(self):
        with self.assertRaises(ValueError):
            Settings(allowed_hosts=("sfc.example.test",))
        with self.assertRaises(ValueError):
            replace(self.settings, tenant_id="", client_id="")


if __name__ == "__main__":
    unittest.main()
