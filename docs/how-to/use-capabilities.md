# Use the capabilities lab

Prerequisite: the existing local Franark Python or Docker setup is running.

1. Open `http://127.0.0.1:8765/lab`, or select **Capabilities lab** in the workbench.
2. Select one of the six mechanisms. Its input, JSON Schema and source references
   appear together. Restore the synthetic example if needed.
3. Edit the JSON and select **Run method**. Inspect the returned representation,
   source references, limitations and measured timing/byte counts.
4. Download a reproduction bundle when you need exact replay inputs. It includes
   source content; keep operational bundles in an approved data environment.
5. Inspect local measurement history. It persists telemetry and hashes, not the
   source/result documents. Missing quality scores are intentionally null.

No model key is needed for these computations. `memory.summarize` extracts
sentences; it does not reason about an assessment or produce a finished case note.
The current app does not collect tablet forms or signatures.

For model-driven calls, configure the existing OpenAI adapter as documented in
[Connect a model](connect-model.md). A synthetic fake-client test covers function
calling, argument validation, permissions and request budgets. Live provider
behavior still needs an account-level synthetic test after credentials are set.

## Add a future mechanism

Define a validated input model and pure function, register a Method with its
reference IDs and limitations, add synthetic examples and invariant tests, then
grant it to the intended roles/instances/projects. Update the method and idea
records before comparing results. Functions can be reused in non-agent workflows.

A written skill can later guide selection and policy. Do not copy implementation
logic into prompts, and do not treat a skill instruction as permission to bypass
the application's tool or record access controls.
