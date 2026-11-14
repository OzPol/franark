"""Dry-run example: inject a specialist into a generic workflow."""

from pathlib import Path

from franark.core import (
    Agent, AgentConfig, AgentRegistry, AgentResult, Evidence, Outcome,
    RoleSpec, Step, Task, Workflow, load_roles,
)


class DemoRuntime:
    """Deterministic demonstration. Does not call an AI model or a real tool."""

    def run(self, agent, role, task, inputs, tools):
        output = f"DEMO ONLY: {agent.agent_id} ({role.role_id}) processed {list(inputs)}"
        return AgentResult(
            summary=output,
            evidence_ids=("synthetic-meeting",),
            outcome=Outcome.ACCEPTED if role.role_id == "reviewer" else Outcome.PROPOSED,
        )


def build_demo():
    from franark.pipeline import role_catalog
    roles = role_catalog()
    runtime = DemoRuntime()
    registry = AgentRegistry()
    for agent_id, role_id in [
        ("pm", "project_manager"), ("dispatcher", "coordinator"),
        ("worker", "worker"), ("qa", "reviewer"),
        ("writer", "communications"),
    ]:
        registry.register(Agent(AgentConfig(agent_id, role_id, "sfc-demo"),
                                roles[role_id], runtime))

    # Add a new domain without editing Agent, AgentRegistry, or Workflow.
    facilities = RoleSpec(
        role_id="facilities_analyst", purpose="Assess facilities requirements.",
        capabilities=frozenset({"facilities.assess"}), allowed_tools=frozenset(),
    )
    registry.register(Agent(
        AgentConfig("facilities-1", facilities.role_id, "sfc-demo"),
        facilities, runtime,
    ))
    workflow = Workflow((
        Step("plan", "project.plan"),
        Step("dispatch", "workflow.dispatch", ("plan",)),
        Step("execute", "operations.execute", ("dispatch",)),
        Step("review", "review.verify", ("execute",), distinct_from=("execute",)),
        Step("report", "project.report", ("review",)),
        Step("draft", "reports.prepare", ("report",)),
        Step("review_draft", "review.verify", ("draft",), distinct_from=("draft",)),
    ))
    workflow.insert_between("execute", "review", Step("facilities", "facilities.assess"))
    task = Task(
        "demo-001", "sfc-demo", "Demonstrate a pluggable workflow.",
        ("Inserted specialist runs before the review.",),
        (Evidence("synthetic-meeting", "synthetic://meeting", "Synthetic demonstration"),),
    )
    return workflow, task, registry


if __name__ == "__main__":
    workflow, task, registry = build_demo()
    report = workflow.run(task, registry)
    print("DEMO ONLY. No AI calls, connected accounts, or external actions.")
    for event in report.events:
        print(event)
    print(f"Run status: {report.status}")
