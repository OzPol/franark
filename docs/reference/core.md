# Agent and workflow contracts

```{automodule} franark.core
:members:
```

`RuntimeAdapter` is the model integration seam. A runtime receives the configured
agent, its role, task evidence, dependency outputs, and mediated tools. It returns
an `AgentResult`. The current API adapter produces drafts and evaluations;
external work-tool execution is an integration milestone.
