from importlib.resources import files
import time

from .core import Agent, AgentConfig, AgentRegistry, Evidence, Step, Task, Workflow, load_roles
from .runtimes import DemoRuntime, LimitedRuntime, OpenAIRuntime
from .capabilities import METHODS, handlers


SAMPLE_NOTES = """Synthetic IT meeting
ACTION: IT manager | Gather the current device inventory | Due date not stated
ACTION: Oz | Review the support contract and last three invoices | Due date not stated
Question: Can support requests be grouped by recurring issue?
"""


def role_catalog():
    return load_roles(str(files("franark").joinpath("resources/roles.json")))


def build_workflow(domain):
    steps = [
        Step("plan", "project.plan"),
        Step("dispatch", "workflow.dispatch", ("plan",)),
        Step("research", "requirements.analyze", ("dispatch",)),
    ]
    predecessor = "research"
    capabilities = {
        "general": [], "it": ["it.assess", "procurement.analyze"],
        "wellsky": ["wellsky.investigate"], "software": ["software.build"],
    }[domain]
    for index, capability in enumerate(capabilities):
        step_id = f"specialist_{index + 1}"
        steps.append(Step(step_id, capability, (predecessor,)))
        predecessor = step_id
    steps.extend([
        Step("work", "operations.execute", (predecessor, "dispatch")),
        Step("review", "review.verify", ("work", predecessor), distinct_from=("work", predecessor)),
        Step("status", "project.report", ("review", "work")),
        Step("draft", "reports.prepare", ("status", "work")),
        Step("review_draft", "review.verify", ("draft",), distinct_from=("draft",)),
    ])
    return Workflow(tuple(steps))


def run_saved(store, run_id, settings):
    store.update(run_id, "running")
    started = time.perf_counter_ns()
    runtime = None
    try:
        record = store.get(run_id)
        runtime = LimitedRuntime(
            DemoRuntime() if settings.runtime == "demo" else OpenAIRuntime(
                settings, on_usage=lambda usage: store.record_measurement("model", usage, run_id)),
            settings.max_calls,
        )
        registry = AgentRegistry()
        for role_id, role in role_catalog().items():
            registry.register(Agent(AgentConfig(role_id, role_id, "local", role.allowed_tools), role, runtime))
        task = Task(
            run_id, "local",
            "Prepare a source-backed action list and management draft from these notes. "
            "Leave priorities unranked unless a priority policy is explicitly provided. "
            "Record nonblocking questions and continue useful draft work.",
            ("Every action is traceable to the submitted notes.",
             "Missing owners, deadlines, and unobserved behavior remain explicit.",
             "Reviewer and worker are different instances."),
            (Evidence("submitted-notes", f"local-run://{run_id}/notes", record["notes"]),),
        )
        report = build_workflow(record["domain"]).run(
            task, registry,
            project_grants=frozenset(METHODS),
            tool_handlers=handlers(lambda measured: store.record_measurement(
                "capability", {key: value for key, value in measured.items() if key != "result"}, run_id)),
            on_event=lambda kind, step_id, agent_id, result: store.event(
                run_id, kind, step_id, agent_id, result),
        )
        store.update(run_id, report.status, f"{runtime.calls} agent calls completed.")
    except Exception as exc:
        # Do not persist provider exception text, request payloads, or credentials.
        store.update(run_id, "failed", f"Run stopped ({type(exc).__name__}). See the troubleshooting guide before retrying.")
    finally:
        store.record_measurement("workflow", {
            "elapsed_ms": (time.perf_counter_ns() - started) / 1e6,
            "runtime": settings.runtime, "model": settings.model,
            "agent_calls": runtime.calls if runtime else 0,
            "model_requests": getattr(runtime.delegate, "request_count", 0) if runtime else 0,
            "max_calls": settings.max_calls, "max_tool_rounds": settings.max_tool_rounds,
        }, run_id)


def markdown_report(record):
    output = [f"# {record['title']}", "", f"Runtime: {record['runtime']}",
              f"Status: {record['status']}", ""]
    for event in record["events"]:
        if event["result"]:
            result = event["result"]
            output += [f"## {event['step_id']} · {event['agent_id']}", "",
                       result["summary"], "", f"Outcome: {result['outcome']}", ""]
            if result["questions"]:
                output += ["Questions:", ""] + [f"- {q}" for q in result["questions"]] + [""]
    return "\n".join(output)
