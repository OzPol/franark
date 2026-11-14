# Add an agent or specialist

1. Add a role to `src/franark/resources/roles.json` if the role is new.
2. Define a stable capability such as `facilities.assess`.
3. Register an Agent instance with the role, project, and runtime.
4. Add a step or insert it into an existing dependency edge.
5. Give its outputs a separate review step.
6. Regenerate role documentation and run the focused workflow tests.

```python
from franark.core import Agent, AgentConfig, Step

registry.register(Agent(
    AgentConfig("facilities-1", "facilities_analyst", "local"),
    roles["facilities_analyst"],
    runtime,
))
workflow.insert_between(
    "work", "review", Step("facilities", "facilities.assess")
)
```

The example assumes that `roles`, `runtime`, `registry`, and `workflow` already
exist and that the new role has been added to the catalog. The workflow preserves
reviewer separation when a step is inserted before a separated review.

The local pilot constructs workflows in `pipeline.py`. A future configuration
loader can move those definitions to versioned files without replacing the core
contracts. The `tests/reference_demo.py` fixture exercises insertion.
