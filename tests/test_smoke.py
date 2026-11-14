import json
import unittest
from unittest.mock import patch

from tools.smoke_http import wait_for


class ReadinessTests(unittest.TestCase):
    def test_transient_connection_reset_is_retried_before_readiness(self):
        with patch("tools.smoke_http.fetch", side_effect=[
            ConnectionResetError("Container is starting"), '{"status": "ok"}'
        ]) as fetch, patch("tools.smoke_http.time.sleep"):
            value = wait_for("http://localhost/health", lambda text: json.loads(text)["status"] == "ok")
        self.assertEqual(json.loads(value), {"status": "ok"})
        self.assertEqual(fetch.call_count, 2)
