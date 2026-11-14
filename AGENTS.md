# Working on Franark

- Preserve the common Agent, RoleSpec, AgentConfig, RuntimeAdapter, Task,
  AgentResult, AgentRegistry, and Workflow contracts unless a change needs them.
- Add roles through the catalog and capability registration. Avoid new role-specific
  subclasses where configuration is sufficient.
- PM prioritization uses an approved policy, cited facts, and explicit assumptions.
  Keep PM accountability separate from Coordinator dispatch and Reviewer acceptance.
- Keep secrets and operational records out of source files, examples, tests, and CI.
- Use synthetic examples in automated tests. Model tests use fake clients.
- Add focused tests for changed routing, state, permissions, or integration behavior.
- Update the relevant how-to, reference, and changelog when behavior changes.
- Generate role documentation with `python tools/render_roles.py` after catalog changes.
- Check `python -m unittest discover -s tests -v`,
  `python tools/render_roles.py --check`, and the strict Sphinx build.
- Record architectural decisions in `docs/decisions` using the ADR template.
- Use the user's current task and repository issue as the scope of work.
