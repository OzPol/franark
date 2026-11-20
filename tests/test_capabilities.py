import base64
from copy import deepcopy
from importlib.resources import files
import json
import unittest
import zlib

from franark.capabilities import apply_delta, canonical, execute, unpack_lossless


class CapabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.examples = json.loads(files("franark").joinpath("resources/capability_examples.json").read_text())

    def run_method(self, name, **updates):
        arguments = deepcopy(self.examples[name])
        arguments.update(updates)
        return execute(name, arguments)

    def test_selection_keeps_pinned_sources_and_omits_nonmatching_text(self):
        result = self.run_method("memory.select")["result"]
        self.assertEqual({item["source_id"] for item in result["selected"]},
                         {"synthetic-contract", "synthetic-update"})
        self.assertLessEqual(result["selected_bytes"], 1000)
        self.assertEqual(result["omitted"][0]["source_id"], "synthetic-menu")

    def test_budget_failure_never_silently_drops_pinned_evidence(self):
        with self.assertRaises(ValueError):
            self.run_method("memory.select", budget_bytes=32)

    def test_unmatched_query_returns_no_unpinned_evidence(self):
        documents = [{"source_id": "s", "version": "1", "text": "apples oranges"}]
        result = self.run_method("memory.select", query="network", documents=documents)["result"]
        self.assertEqual(result["selected"], [])

    def test_duplicate_source_version_is_rejected(self):
        doc = {"source_id": "s", "version": "1", "text": "Network report"}
        with self.assertRaises(ValueError):
            self.run_method("memory.select", documents=[doc, doc])

    def test_delta_replays_exactly_and_requires_matching_base(self):
        arguments = self.examples["memory.delta"]
        packet = execute("memory.delta", arguments)["result"]
        self.assertEqual(apply_delta(arguments["before"], packet), arguments["after"])
        self.assertTrue(packet["exact_reconstruction_verified"])
        self.assertEqual({item["path"] for item in packet["patch"]}, {"/birthdate", "/meal_count"})
        with self.assertRaises(ValueError):
            apply_delta({"different": "base"}, packet)

    def test_nested_delta_handles_pointer_escaping_types_arrays_and_deletions(self):
        before = {"a/b": {"~": [1, 2]}, "deleted": None, "type": True}
        after = {"a/b": {"~": [1, 3]}, "type": 1, "added": {"": "value"}}
        packet = self.run_method("memory.delta", before=before, after=after)["result"]
        self.assertEqual(canonical(apply_delta(before, packet)), canonical(after))
        self.assertEqual(before["a/b"]["~"], [1, 2])

    def test_lossless_unicode_roundtrip_and_small_input_expansion(self):
        for text in ("", "x", "Özlem \u0131 \U0001f30d\n" * 200):
            measured = self.run_method("memory.pack", text=text)
            self.assertEqual(unpack_lossless(measured["result"]), text)
        measured = self.run_method("memory.pack", text="x")
        self.assertGreater(measured["metrics"]["output_bytes"], measured["metrics"]["input_bytes"])

    def test_lossless_decoder_checks_hash_and_expansion_bound(self):
        packet = self.run_method("memory.pack")["result"]
        packet["source_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            unpack_lossless(packet)
        packet["data_base64"] = base64.b64encode(zlib.compress(b"x" * 10000)).decode()
        with self.assertRaises(ValueError):
            unpack_lossless(packet, max_bytes=100)

    def test_projection_keeps_protected_fields_and_reports_missing(self):
        result = self.run_method("memory.project", fields=["/assessment/meal_support", "/unknown"])["result"]
        self.assertEqual(result["fields"]["/client_id"], "SYN-001")
        self.assertEqual(result["fields"]["/assessment/meal_support"], "requested")
        self.assertNotIn("/contact/phone", result["fields"])
        self.assertEqual(result["missing_fields"], ["/unknown"])

    def test_extractive_summary_references_exact_offsets_including_decimals(self):
        text = "The unit cost was 2.50 dollars. The unit cost was 2.50 dollars. The proposed cost excludes tax."
        result = self.run_method("memory.summarize", query="cost tax",
                                 documents=[{"source_id": "s", "version": "2", "text": text}],
                                 max_sentences=2)["result"]
        self.assertEqual(len(result["sentences"]), 2)
        for sentence in result["sentences"]:
            self.assertEqual(sentence["text"], text[sentence["start_char"]:sentence["end_char"]])
        self.assertTrue(any("excludes tax" in item["text"] for item in result["sentences"]))

    def test_pinned_summary_exceeding_sentence_cap_is_rejected(self):
        doc = {"source_id": "s", "version": "1", "text": "First fact. Second fact.", "pinned": True}
        with self.assertRaises(ValueError):
            self.run_method("memory.summarize", documents=[doc], max_sentences=1)

    def test_timeline_keeps_small_changes_and_critical_unchanged_events(self):
        result = self.run_method("memory.timeline")["result"]
        self.assertEqual([item["event_id"] for item in result["keyframes"]], ["e1", "e3", "e4", "e5"])
        self.assertEqual(result["keyframes"][0]["coalesced_event_ids"], ["e2"])
        self.assertIn("state_change", result["keyframes"][1]["reasons"])
        self.assertIn("critical", result["keyframes"][2]["reasons"])

    def test_timeline_rejects_out_of_order_events(self):
        with self.assertRaises(ValueError):
            self.run_method("memory.timeline", snapshots=list(reversed(self.examples["memory.timeline"]["snapshots"])))

    def test_measurements_include_real_sizes_and_hashes_without_quality_claims(self):
        first = self.run_method("memory.select")
        second = self.run_method("memory.select")
        self.assertEqual(first["metrics"]["input_sha256"], second["metrics"]["input_sha256"])
        self.assertEqual(first["metrics"]["output_bytes"], len(canonical(first["result"])))
        self.assertGreaterEqual(first["metrics"]["elapsed_ms"], 0)
        self.assertIsNone(first["metrics"]["semantic_fidelity"])
        self.assertIsNone(first["metrics"]["model_tokens"])
        self.assertIsNone(first["metrics"]["power_watts"])

    def test_schema_rejects_unrecognized_fields_and_oversized_input(self):
        with self.assertRaises(ValueError):
            self.run_method("memory.pack", email_recipient="not-a-tool")
        with self.assertRaises(ValueError):
            self.run_method("memory.pack", text="a" * 1000001)


if __name__ == "__main__":
    unittest.main()
