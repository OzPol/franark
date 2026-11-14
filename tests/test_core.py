import unittest

from franark.core import (
    Agent, AgentConfig, AgentRegistry, AgentResult, Evidence, Outcome,
    RoleSpec, Step, Task, ToolDenied, Workflow,
)
from reference_demo import build_demo


class StubRuntime:
    def __init__(self, result=None, tool=None):
        self.result = result or AgentResult("prepared", ("source",))
        self.tool = tool

    def run(self, agent, role, task, inputs, tools):
        if self.tool:
            tools.call(self.tool)
        return self.result


def worker(agent_id="worker", project="p", capabilities=frozenset({"work"}),
           role_tools=frozenset(), instance_tools=frozenset(), runtime=None):
    return Agent(
        AgentConfig(agent_id, "custom", project, instance_tools),
        RoleSpec("custom", "Example", capabilities, role_tools),
        runtime or StubRuntime(),
    )


def task(project="p"):
    return Task("t", project, "Do the task", ("Evidence-backed output",),
                (Evidence("source", "synthetic://source", "Synthetic source"),))


class ArchitectureTests(unittest.TestCase):
    def test_injected_specialist_runs_before_review(self):
        workflow, demo_task, registry = build_demo()
        report = workflow.run(demo_task, registry)
        self.assertEqual(report.status, "finished")
        steps = list(report.results)
        self.assertLess(steps.index("facilities"), steps.index("review"))
        self.assertEqual(report.results["review"].outcome, Outcome.ACCEPTED)

    def test_tool_requires_role_instance_and_project_grants(self):
        calls = []
        agent = worker(role_tools=frozenset({"write"}),
                       instance_tools=frozenset({"write"}),
                       runtime=StubRuntime(tool="write"))
        with self.assertRaises(ToolDenied):
            agent.run(task(), {}, frozenset(), {"write": lambda: calls.append(1)})
        self.assertEqual(calls, [])
        agent.run(task(), {}, frozenset({"write"}), {"write": lambda: calls.append(1)})
        self.assertEqual(calls, [1])

    def test_cross_project_routing_and_execution_are_denied(self):
        registry = AgentRegistry()
        agent = worker(project="other")
        registry.register(agent)
        with self.assertRaises(LookupError):
            registry.resolve("p", "work")
        with self.assertRaises(ToolDenied):
            agent.run(task(), {}, frozenset(), {})

    def test_ambiguous_routing_requires_explicit_assignment(self):
        registry = AgentRegistry()
        registry.register(worker("one"))
        registry.register(worker("two"))
        with self.assertRaises(LookupError):
            registry.resolve("p", "work")
        self.assertEqual(registry.resolve("p", "work", "two").config.agent_id, "two")

    def test_same_agent_cannot_review_its_own_output(self):
        registry = AgentRegistry()
        registry.register(worker(capabilities=frozenset({"work", "review.verify"})))
        workflow = Workflow((
            Step("work", "work"),
            Step("review", "review.verify", ("work",), distinct_from=("work",)),
        ))
        with self.assertRaises(LookupError):
            workflow.run(task(), registry)

    def test_review_rejection_stops_downstream_work(self):
        registry = AgentRegistry()
        registry.register(worker())
        registry.register(worker("reviewer", capabilities=frozenset({"review.verify"}),
                                 runtime=StubRuntime(AgentResult(
                                     "needs correction", ("source",), outcome=Outcome.REJECTED))))
        workflow = Workflow((
            Step("work", "work"),
            Step("review", "review.verify", ("work",), distinct_from=("work",)),
            Step("publish", "work", ("review",)),
        ))
        report = workflow.run(task(), registry)
        self.assertEqual(report.status, "rejected")
        self.assertNotIn("publish", report.results)

    def test_unknown_evidence_is_rejected(self):
        agent = worker(runtime=StubRuntime(AgentResult("claim", ("invented",))))
        with self.assertRaises(ValueError):
            agent.run(task(), {}, frozenset(), {})

    def test_acceptance_requires_evidence_and_distinct_review(self):
        registry = AgentRegistry()
        registry.register(worker("qa", capabilities=frozenset({"review.verify"}),
                                 runtime=StubRuntime(AgentResult(
                                     "approved", (), outcome=Outcome.ACCEPTED))))
        with self.assertRaises(ValueError):
            Workflow((Step("review", "review.verify"),)).run(task(), registry)

    def test_injection_preserves_review_separation_from_both_workers(self):
        workflow, demo_task, registry = build_demo()
        review = workflow._steps["review"]
        self.assertEqual(set(review.distinct_from), {"execute", "facilities"})
        self.assertTrue(set(review.distinct_from) <= set(review.dependencies))

    def test_cycle_is_rejected_and_injection_is_atomic(self):
        workflow = Workflow((Step("a", "work"), Step("b", "work", ("a",))))
        with self.assertRaises(ValueError):
            workflow.insert_between("a", "b", Step("c", "work", ("b",)))
        self.assertEqual(set(workflow._steps), {"a", "b"})


if __name__ == "__main__":
    unittest.main()
