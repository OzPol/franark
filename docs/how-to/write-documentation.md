# Write consistent documentation

Choose the template matching the reader's goal:

| Need | Template |
|---|---|
| Complete a specific task | How-to |
| Explain a concept or assessment | Article |
| Record project progress | Blog post |
| Answer a repeated question | FAQ entry |
| Capture an architectural choice | ADR |
| Specify a user outcome | User story |
| Describe repeatable operations | Runbook |

Copy the template to the appropriate content directory. Fill in metadata,
prerequisites, steps or argument, evidence, and related content. Add the page to
that directory's toctree or linked index. Use source references for factual claims
and mark estimates and unresolved questions clearly.

Template revisions use SemVer in the metadata. Archive the previous template
under `templates/archive/vX.Y/` when changing its structure. Existing documents
retain their recorded template version until intentionally migrated.

Build before submitting a pull request:

```bash
python -m sphinx -W --keep-going -b html docs docs/_build/html
```

Role documentation is generated from the role catalog:

```bash
python tools/render_roles.py
```

Use Git history for content revisions and ADRs for design rationale. The blog is
a set of dated, version-controlled pages in this pilot; RSS and publishing
automation are backlog items.
