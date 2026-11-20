from dataclasses import replace
import json
from types import SimpleNamespace
import unittest

from franark.core import AgentConfig, AgentResult, Evidence, Outcome, RoleSpec, Task, Toolbox
from franark.runtimes import LimitedRuntime, OpenAIRuntime
from franark.settings import Settings
from franark.capabilities import handlers


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

    def test_model_can_call_a_granted_method_and_usage_is_recorded(self):
        class ToolResponses(FakeResponses):
            def create(self, **kwargs):
                if not self.calls:
                    self.calls.append(kwargs)
                    return SimpleNamespace(status="completed", output_text="", output=[SimpleNamespace(
                        type="function_call", name="memory_pack", call_id="call-1",
                        arguments=json.dumps({"text": "synthetic"}))],
                        usage=SimpleNamespace(input_tokens=12, output_tokens=8))
                return super().create(**kwargs)
        responses, usage, measured = ToolResponses(), [], []
        arguments = list(self.arguments())
        arguments[-1] = Toolbox(frozenset({"memory.pack"}), handlers(measured.append))
        runtime = OpenAIRuntime(Settings(runtime="openai", model="configured-model", api_key="fake"),
                                SimpleNamespace(responses=responses), on_usage=usage.append)
        runtime.run(*arguments)
        self.assertEqual(len(measured), 1)
        self.assertEqual(len(responses.calls), 2)
        self.assertEqual(usage[0]["input_tokens"], 12)
        self.assertEqual(responses.calls[0]["tools"][0]["name"], "memory_pack")
        tool_output = responses.calls[1]["input"][-1]
        self.assertEqual(tool_output["type"], "function_call_output")
        self.assertTrue(json.loads(tool_output["output"])["result"]["exact_reconstruction_verified"])

    def test_model_cannot_invoke_an_ungranted_method(self):
        class ForbiddenResponses(FakeResponses):
            def create(self, **kwargs):
                self.calls.append(kwargs)
                return SimpleNamespace(status="completed", output_text="", output=[SimpleNamespace(
                    type="function_call", name="mail_send", call_id="call-1", arguments="{}")])
        responses = ForbiddenResponses()
        runtime = OpenAIRuntime(Settings(runtime="openai", model="configured-model", api_key="fake"),
                                SimpleNamespace(responses=responses))
        with self.assertRaises(PermissionError):
            runtime.run(*self.arguments())

    def test_tool_rounds_are_included_in_the_model_request_budget(self):
        responses = FakeResponses()
        runtime = OpenAIRuntime(Settings(runtime="openai", model="configured-model", api_key="fake", max_calls=1),
                                SimpleNamespace(responses=responses))
        runtime.run(*self.arguments())
        with self.assertRaises(RuntimeError):
            runtime.run(*self.arguments())
        self.assertEqual(len(responses.calls), 1)


if __name__ == "__main__":
    unittest.main()
