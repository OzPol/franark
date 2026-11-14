# ADR-0002: Configure roles on a common agent interface

Status: accepted. Template version: 0.1.0.

## Context

The team needs a PM, Coordinator, general Worker, and several specialists, with
more domains added over time.

## Decision

Use Agent, RoleSpec, AgentConfig, RuntimeAdapter, AgentRegistry, and Workflow.
Route by capabilities and project. Store instructions and role limits in one
canonical JSON catalog. Keep display labels independent from stable role IDs.

## Consequences

A new specialist requires registration and workflow composition. A new model
backend implements RuntimeAdapter. Distinct review constraints remain engine
rules rather than prose preferences.
