"""Generate the role reference from the canonical catalog."""
from pathlib import Path
import argparse
import json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    roles = json.loads((root / "src/franark/resources/roles.json").read_text())
    output = ["# Role catalog", "", "Generated from the canonical role configuration.", "",
              "FRAN is the queen bee and Project Manager. Display names can change independently of role IDs.", "",
              "| Display name | Role ID | Responsibility |", "|---|---|---|"]
    for role in roles:
        output.append(f"| {role['display_name']} | `{role['role_id']}` | {role['purpose']} |")
    output.append("")
    for role in roles:
        output += [f"## {role['display_name']}", "", role["instructions"], "",
                   "Capabilities: " + ", ".join(f"`{item}`" for item in role["capabilities"]) + ".", ""]
    text = "\n".join(output)
    destination = root / "docs/reference/roles.md"
    if args.check:
        if not destination.exists() or destination.read_text() != text:
            raise SystemExit("Role documentation is stale. Run python tools/render_roles.py")
        print("Role documentation is current.")
    else:
        destination.write_text(text)
        print("Generated docs/reference/roles.md")


if __name__ == "__main__":
    main()
