"""Preview issue import, or create missing issues through an authenticated gh CLI."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import tempfile


def issue_body(issue):
    lines = [f"<!-- franark:{issue['id']} -->", "", issue["story"], "",
             f"Milestone: {issue['milestone']}", f"Priority: {issue['priority']}",
             "Dependencies: " + (", ".join(issue["depends_on"]) or "None"), "",
             "## Acceptance criteria", ""]
    lines += ["- [ ] " + item for item in issue["acceptance_criteria"]]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repo):
        parser.error("Repository must use OWNER/REPOSITORY format.")
    root = Path(__file__).resolve().parents[1]
    issues = json.loads((root / "backlog/issues.json").read_text())
    if not args.apply:
        for issue in issues:
            print(f"{issue['id']}: {issue['title']} [{issue['milestone']}]")
        print(f"Preview only: {len(issues)} issues for {args.repo}. Add --apply to create missing issues.")
        return
    existing = subprocess.run(
        ["gh", "issue", "list", "--repo", args.repo, "--state", "all",
         "--limit", "1000", "--json", "number,body"],
        check=True, capture_output=True, text=True,
    )
    bodies = [item.get("body") or "" for item in json.loads(existing.stdout)]
    for issue in issues:
        marker = f"<!-- franark:{issue['id']} -->"
        if any(marker in body for body in bodies):
            print(f"Skip existing {issue['id']}")
            continue
        with tempfile.TemporaryDirectory() as folder:
            body_path = Path(folder) / "issue.md"
            body_path.write_text(issue_body(issue), encoding="utf-8")
            result = subprocess.run(
                ["gh", "issue", "create", "--repo", args.repo,
                 "--title", f"[{issue['id']}] {issue['title']}",
                 "--body-file", str(body_path)],
                check=True, capture_output=True, text=True,
            )
        print(result.stdout.strip())
        bodies.append(marker)


if __name__ == "__main__":
    main()
