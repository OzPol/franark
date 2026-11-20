# ADR-0004: callable information services with measurable baselines

Document ID: ADR-0004. Template version: 0.1.0.
Owner: Oz. Status: implemented foundation; portal recommendations remain proposed.
Updated: 2026-11-19. Applies to: local Franark development. Scope: CAP-001.

## Context

Oz requested real callable mechanisms, established methods, performance measures
and an academic history before optimizing or pursuing novelty. Existing Franark
uses Python, FastAPI, configurable agents, a DAG workflow, SQLite and an OpenAI
adapter. The six-tab simulator demonstrates concepts but not an integrated system.

## Options

- Six new autonomous agent subclasses: more orchestration cost and duplicated
  role/runtime behavior without a demonstrated need.
- Prompt/skill instructions only: useful guidance but no enforceable algorithm,
  metric contract or permission boundary.
- Pure functions behind the existing Toolbox, with classes for stateful adapters:
  testable and usable from agents, APIs, experiments and future workflows.

## Decision

Use the third option. Preserve Agent, RoleSpec, AgentConfig, Task, AgentResult,
AgentRegistry, RuntimeAdapter and Workflow. Add information tool handlers and
schemas. Effective permission remains role ceiling intersected with instance and
project grants. Source processing tools have no network or business-system writes.

OpenAI function calling advertises only those granted tools. Every call validates
arguments; follow-up requests count against the API request limit. Method telemetry
stores hashes, code identity and observations, never invented quality or power data.
Skills may later document selection policies; application code remains the
implementation. No ChatGPT/Codex skill is installed or modified here.

## Consequences

The suite is usable now without model credentials and can be called by the model
when configured. A03 is a storage codec; A04 and A06 are conservative engineering
baselines. They do not implement all mathematical objectives in the original
simulator. Semantic adequacy and task quality require separate experiments.

Azure hosting, Entra authorization, operational form state machines, durable
business-action queues and supported vendor exports require their own decisions
and acceptance tests. The current loopback application must not be exposed to
employees by widening its allowed hosts before those controls exist.

## Sources and related records

- [Method equations and bibliography](../research/methods.md)
- [Research idea history](../research/idea-log.md)
- [Proposed SFC portal architecture](../explanations/sfc-portal-plan.md)
