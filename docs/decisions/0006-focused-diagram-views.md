# ADR-0006: Separate concepts and architectural viewpoints

- Status: Accepted
- Date: 2026-11-20

## Context

Composite boxes mixed devices, software, lifecycle actions and algorithm names.
Those labels obscured responsibilities and made options hard to rearrange.
The business service hierarchy also needs a future link to an organizational
model without inventing reporting relationships.

## Decision

I use one concept per node, with labeled groups for categories. A device, capture
channel, input method and client are independent dimensions. Separate views use
hierarchy, option maps, cross-functional flow, state and entity relationships as
appropriate. Optional components and unverified connections are dashed, with
readiness recorded independently from category membership.

I maintain stable concept IDs and positions in one versioned model. Generated
outputs include scalable SVG, native Excalidraw nodes with bound connectors,
Mermaid source, a vector PDF and a source bundle. Each view has one purpose;
a single overview does not need to contain every integration or function.

Existing paper processes remain explicit. Offline device drafts, synchronization
and conflict handling remain proposed. The service hierarchy preserves only the
supplied relationships. Form-definition tooling remains separate from the
already implemented assessment correction workflow.

## Consequences

More focused views replace one crowded overview. Shared IDs make related
concepts traceable across views. Editor changes require reconciliation into the
maintained model. Generated-source checks detect stale packaged output.
Diagram export requires ReportLab but no Graphviz or external editor service.
