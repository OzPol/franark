from dataclasses import replace
import json
from types import SimpleNamespace
import unittest

from franark.core import AgentConfig, AgentResult, Evidence, Outcome, RoleSpec, Task, Toolbox
from franark.runtimes import LimitedRuntime, OpenAIRuntime
from franark.settings import Settings


class FakeResponses:
    def __init__(self):
        self.calls = []
        self.status = "completed"

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(status=self.status, output_text=json.dumps({
            "summary": "Proposed action with a cited excerpt.",
            "evidence_ids": ["submitted-notes"], "artifacts": [],
            "questions": [], "outcome": "proposed"}))


class RuntimeTests(unittest.TestCase):
    def arguments(self):
        return (AgentConfig("worker", "worker", "p"),
                RoleSpec("worker", "Do work", frozenset({"work"}), frozenset()),
                Task("t", "p", "Extract actions", ("Source-backed",),
                     (Evidence("submitted-notes", "synthetic://notes", "ACTION: Prepare report"),)),
                {}, Toolbox(frozenset(), {}))

    def test_adapter_sends_structured_contract_without_remote_storage(self):
        responses = FakeResponses()
        runtime = OpenAIRuntime(Settings(runtime="openai", model="configured-model", api_key="fake"),
                                SimpleNamespace(responses=responses))
        result = runtime.run(*self.arguments())
        self.assertEqual(result.outcome, Outcome.PROPOSED)
        call = responses.calls[0]
        self.assertEqual(call["model"], "configured-model")
        self.assertFalse(call["store"])
        self.assertTrue(call["text"]["format"]["strict"])
        self.assertNotIn("fake", json.dumps(call))

    def test_incomplete_response_is_not_accepted(self):
        responses = FakeResponses()
        responses.status = "incomplete"
        runtime = OpenAIRuntime(Settings(runtime="openai", model="configured-model", api_key="fake"),
                                SimpleNamespace(responses=responses))
        with self.assertRaises(ValueError):
            runtime.run(*self.arguments())

    def test_call_budget_is_enforced_before_another_call(self):
        responses = FakeResponses()
        runtime = LimitedRuntime(OpenAIRuntime(
            Settings(runtime="openai", model="configured-model", api_key="fake"),
            SimpleNamespace(responses=responses)), 1)
        runtime.run(*self.arguments())
        with self.assertRaises(RuntimeError):
            runtime.run(*self.arguments())
        self.assertEqual(len(responses.calls), 1)


if __name__ == "__main__":
    unittest.main()
