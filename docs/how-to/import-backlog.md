# Create GitHub issues from the backlog

The canonical portable backlog is `backlog/issues.json`. `PROJECT.md` is its
human-readable project view. IDs such as `FW-001` remain stable even if GitHub
assigns different issue numbers.

After the repository is available, the connected development assistant can create
the issues from this file. The optional script also supports import with a
signed-in GitHub CLI.

Preview first:

```bash
python tools/seed_issues.py --repo OzPol/franark
```

Create the missing issues:

```bash
python tools/seed_issues.py --repo OzPol/franark --apply
```

The script identifies previously imported issues by a stable marker in their
bodies and processes creation sequentially. It does not delete or rewrite
existing issues. Its existing-issue scan covers the first 1,000 issues returned
by GitHub CLI, which is adequate for this starter backlog. Review import output
before rerunning after a failure.

The backlog file defines milestone names and dependencies. The starter importer
records those in issue bodies; setting GitHub milestone objects and a GitHub
Projects board is a separate repository setup task.
