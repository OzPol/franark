"""Provider-neutral agent, registry, tool, and workflow contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Callable, Mapping, Protocol


@dataclass(frozen=True)
class RoleSpec:
    role_id: str
    purpose: str
    capabilities: frozenset[str]
    allowed_tools: frozenset[str]
    instructions: str = ""
    display_name: str = ""


@dataclass(frozen=True)
class AgentConfig:
    agent_id: str
    role_id: str
    project_id: str
    allowed_tools: frozenset[str] = frozenset()


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    locator: str
    description: str


@dataclass(frozen=True)
class Task:
    task_id: str
    project_id: str
    instruction: str
    acceptance_criteria: tuple[str, ...]
    evidence: tuple[Evidence, ...] = ()


class Outcome(str, Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    NEEDS_INPUT = "needs_input"


@dataclass(frozen=True)
class AgentResult:
    summary: str
    evidence_ids: tuple[str, ...] = ()
    artifacts: tuple[str, ...] = ()
    questions: tuple[str, ...] = ()
    outcome: Outcome = Outcome.PROPOSED


class ToolDenied(PermissionError):
    pass


class Toolbox:
    """Allowlist checks around trusted callbacks; not a code-isolation boundary.

    A production adapter must expose only these mediated tools to a model.
    Tool implementations must independently enforce resource/action scope.
    """

    def __init__(
        self,
        allowed: frozenset[str],
        handlers: Mapping[str, Callable[..., Any]],
    ) -> None:
        self._allowed = allowed
        self._handlers = handlers

    def call(self, name: str, **arguments: Any) -> Any:
        if name not in self._allowed or name not in self._handlers:
            raise ToolDenied(f"Tool {name!r} is not available to this agent.")
        return self._handlers[name](**arguments)


class RuntimeAdapter(Protocol):
    """Implement once for a model SDK, local model, or deterministic test runner."""

    def run(
        self,
        agent: AgentConfig,
        role: RoleSpec,
        task: Task,
        inputs: Mapping[str, AgentResult],
        tools: Toolbox,
    ) -> AgentResult: ...


@dataclass
class Agent:
    config: AgentConfig
    role: RoleSpec
    runtime: RuntimeAdapter

    def run(
        self,
        task: Task,
        inputs: Mapping[str, AgentResult],
        project_grants: frozenset[str],
        tool_handlers: Mapping[str, Callable[..., Any]],
    ) -> AgentResult:
        if task.project_id != self.config.project_id:
            raise ToolDenied("Agent and task belong to different projects.")
        allowed = (
            self.role.allowed_tools & self.config.allowed_tools & project_grants
        )
        result = self.runtime.run(
            self.config,
            self.role,
            task,
            MappingProxyType(dict(inputs)),
            Toolbox(allowed, tool_handlers),
        )
        if not isinstance(result, AgentResult):
            raise TypeError("Runtime must return AgentResult.")
        known = {item.evidence_id for item in task.evidence}
        if not set(result.evidence_ids) <= known:
            raise ValueError("Result references evidence absent from the task packet.")
        return result


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, Agent] = {}

    def register(self, agent: Agent) -> None:
        if agent.config.agent_id in self._agents:
            raise ValueError("Duplicate agent ID.")
        if agent.role.role_id != agent.config.role_id:
            raise ValueError("Agent configuration and role do not match.")
        if not agent.config.allowed_tools <= agent.role.allowed_tools:
            raise ValueError("Instance tools exceed the role tool ceiling.")
        self._agents[agent.config.agent_id] = agent

    def resolve(
        self,
        project_id: str,
        capability: str,
        agent_id: str | None = None,
        excluded: frozenset[str] = frozenset(),
    ) -> Agent:
        candidates = [
            agent for agent in self._agents.values()
            if agent.config.project_id == project_id
            and capability in agent.role.capabilities
            and agent.config.agent_id not in excluded
            and (agent_id is None or agent.config.agent_id == agent_id)
        ]
        if len(candidates) != 1:
            raise LookupError(
                f"Expected one agent for {capability!r}; found {len(candidates)}. "
                "Register an eligible agent or specify agent_id."
            )
        return candidates[0]


@dataclass(frozen=True)
class Step:
    step_id: str
    capability: str
    dependencies: tuple[str, ...] = ()
    agent_id: str | None = None
    distinct_from: tuple[str, ...] = ()


@dataclass(frozen=True)
class RunReport:
    status: str
    results: Mapping[str, AgentResult]
    assignments: Mapping[str, str]
    events: tuple[str, ...]


class Workflow:
    """A configurable DAG. Modify it between runs, not while a run is active.

    Failures raise; needs_input/rejected stop downstream work. Rework is explicit.
    This reference has no persistence, concurrency, retry, or side-effect recovery.
    """

    def __init__(self, steps: tuple[Step, ...] = ()) -> None:
        self._steps: dict[str, Step] = {}
        for step in steps:
            if step.step_id in self._steps:
                raise ValueError("Duplicate step ID.")
            self._steps[step.step_id] = step
        self._order(self._steps)

    @staticmethod
    def _order(steps: Mapping[str, Step]) -> list[str]:
        for step in steps.values():
            if not set(step.dependencies) <= steps.keys():
                raise ValueError("A step has an unknown dependency.")
            if not set(step.distinct_from) <= set(step.dependencies):
                raise ValueError("distinct_from must reference direct dependencies.")
        pending = dict(steps)
        ordered: list[str] = []
        while pending:
            ready = [key for key, value in pending.items()
                     if set(value.dependencies) <= set(ordered)]
            if not ready:
                raise ValueError("Workflow contains a cycle.")
            for key in ready:
                ordered.append(key)
                del pending[key]
        return ordered

    def add_step(self, step: Step) -> None:
        if step.step_id in self._steps:
            raise ValueError("Duplicate step ID.")
        proposed = {**self._steps, step.step_id: step}
        self._order(proposed)
        self._steps = proposed

    def insert_between(self, before: str, after: str, step: Step) -> None:
        """Insert a specialist on an existing dependency edge atomically."""
        from dataclasses import replace

        if before not in self._steps or after not in self._steps:
            raise ValueError("Both endpoints must exist.")
        target = self._steps[after]
        if before not in target.dependencies:
            raise ValueError("No dependency edge exists between those steps.")
        if step.step_id in self._steps:
            raise ValueError("Duplicate step ID.")
        dependencies = tuple(dict.fromkeys((*step.dependencies, before)))
        injected = replace(step, dependencies=dependencies)
        # Preserve other dependencies and any reviewer separation constraint.
        target_dependencies = tuple(
            step.step_id if key == before else key for key in target.dependencies
        )
        target_distinct = tuple(dict.fromkeys(
            (*target.distinct_from, step.step_id)
            if before in target.distinct_from else target.distinct_from
        ))
        if before in target.distinct_from:
            target_dependencies = tuple(dict.fromkeys((*target_dependencies, before)))
        proposed = {
            **self._steps,
            step.step_id: injected,
            after: replace(target, dependencies=target_dependencies,
                           distinct_from=target_distinct),
        }
        self._order(proposed)
        self._steps = proposed

    def run(
        self,
        task: Task,
        registry: AgentRegistry,
        project_grants: frozenset[str] = frozenset(),
        tool_handlers: Mapping[str, Callable[..., Any]] | None = None,
        on_event: Callable[[str, str, str, AgentResult | None], None] | None = None,
    ) -> RunReport:
        results: dict[str, AgentResult] = {}
        assignments: dict[str, str] = {}
        events: list[str] = []
        order = self._order(self._steps)
        for key in order:
            step = self._steps[key]
            excluded = frozenset(assignments[item] for item in step.distinct_from)
            agent = registry.resolve(task.project_id, step.capability,
                                     step.agent_id, excluded)
            assignments[key] = agent.config.agent_id
            events.append(f"assigned:{key}:{agent.config.agent_id}")
            if on_event:
                on_event("assigned", key, agent.config.agent_id, None)
            result = agent.run(
                task, {item: results[item] for item in step.dependencies},
                project_grants, tool_handlers or {},
            )
            if result.outcome is Outcome.ACCEPTED and step.capability != "review.verify":
                raise ValueError("Only a review.verify step may accept a result.")
            if (result.outcome is Outcome.ACCEPTED
                    and (not step.distinct_from or not result.evidence_ids)):
                raise ValueError("Acceptance requires separated review and evidence.")
            if step.capability == "review.verify" and result.outcome is Outcome.PROPOSED:
                raise ValueError("A review must accept, reject, or request input.")
            results[key] = result
            if on_event:
                on_event("result", key, agent.config.agent_id, result)
            events.append(f"result:{key}:{result.outcome.value}")
            if result.outcome in {Outcome.REJECTED, Outcome.NEEDS_INPUT}:
                return RunReport(result.outcome.value, dict(results),
                                 dict(assignments), tuple(events))
        # 'finished' means configured steps ran; acceptance is a separate result.
        return RunReport("finished", dict(results), dict(assignments), tuple(events))


def load_roles(path: str) -> dict[str, RoleSpec]:
    import json

    with open(path, encoding="utf-8") as handle:
        records = json.load(handle)
    roles: dict[str, RoleSpec] = {}
    for record in records:
        if record["role_id"] in roles:
            raise ValueError("Duplicate role ID.")
        roles[record["role_id"]] = RoleSpec(
            role_id=record["role_id"], purpose=record["purpose"],
            capabilities=frozenset(record["capabilities"]),
            allowed_tools=frozenset(record["allowed_tools"]),
            instructions=record["instructions"],
            display_name=record.get("display_name", record["role_id"].replace("_", " ").title()),
        )
    return roles
