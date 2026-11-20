"""Render the maintained architecture views from Graphviz source."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
COMMON = '''
graph [rankdir=TB, bgcolor="white", pad="0.3", nodesep="0.45", ranksep="0.55", fontname="DejaVu Sans", fontsize=17, color="#cbd5e1"];
node [shape=box, style="rounded,filled", fillcolor="#edf5fc", color="#6b8aa5", fontcolor="#111111", fontname="DejaVu Sans", fontsize=16, margin="0.20,0.14", penwidth=1.3];
edge [color="#52677a", fontname="DejaVu Sans", fontsize=12, fontcolor="#111111", arrowsize=0.75];
'''
DIAGRAMS = {
    "context": ("System context", "Solid: working pilot. Dashed: account connection or destination contract still required.", '''
staff [label="SFC employees\nCase work and nutrition"];
reviewer [label="Assigned reviewer"];
app [label="Franark\nForms · review · agents · research", fillcolor="#dcebf8", penwidth=2];
records [label="Application records\nSQLite pilot / Azure SQL adapter"];
model [label="OpenAI API\nConfigured adapter; live test pending", style="rounded,filled,dashed", fillcolor="#f5f5f5"];
identity [label="SFC Microsoft Entra\nSign-in and app assignments", style="rounded,filled,dashed", fillcolor="#f5f5f5"];
mail [label="Outlook / signature providers\nConnections pending", style="rounded,filled,dashed", fillcolor="#f5f5f5"];
vendors [label="eCIRTS / WellSky / SAMS\nImport contracts pending", style="rounded,filled,dashed", fillcolor="#f5f5f5"];
staff -> app; reviewer -> app; identity -> app [style=dashed, label="validated identity"];
app -> records [label="versioned records"];
app -> model [style=dashed, label="bounded requests"];
app -> mail [style=dashed]; app -> vendors [style=dashed];
{rank=same; staff; reviewer; identity;}
{rank=same; records; model;}
{rank=same; mail; vendors;}
records -> mail [style=invis]; model -> vendors [style=invis];
'''),
    "stack": ("Software stack", "The same Python services support the portal, agents and measurement harness.", '''
browser [label="Browser / tablet\nHTML, forms and pen input"];
api [label="FastAPI boundary\nJWT verification · roles · record scope", fillcolor="#dcebf8", penwidth=2];
forms [label="Form lifecycle\nValidation · review · PDF / exports"];
agents [label="Agent registry and workflows\nFRAN · specialists · reviewer"];
methods [label="Information tools\nSelect · delta · pack\nProject · summarize · timeline"];
store [label="SQLAlchemy repository\nTransactions · concurrency · audit"];
sqlite [label="SQLite\nWorking synthetic pilot", fillcolor="#eef6ee"];
sql [label="Azure SQL\nManaged-identity adapter\nTenant connection pending", style="rounded,filled,dashed", fillcolor="#f5f5f5"];
llm [label="Model adapter\nBounded OpenAI calls"];
browser -> api; api -> forms; api -> agents; api -> methods;
agents -> methods [label="granted tools"];
agents -> llm; forms -> llm [label="optional QA"];
forms -> store; methods -> store [label="telemetry"];
agents -> store [label="run history"];
store -> sqlite; store -> sql [style=dashed];
{rank=same; forms; agents; methods;}
{rank=same; sqlite; sql;}
'''),
    "workflow": ("Assessment and review flow", "AI can draft findings. Only an authorized human review releases exports.", '''
draft [label="Editable draft"];
submit [label="Submit revision\nFreeze answers + signature hash"];
validate [label="Rule validation\nCompare authorized prior record"];
findings [label="Validation outcome", shape=diamond, fillcolor="#fff7e8"];
fix [label="Correction draft\nNew acknowledgement required", fillcolor="#fff7e8"];
review [label="Human review\nEvidence + written resolution", fillcolor="#dcebf8", penwidth=2];
approve [label="Approved record", fillcolor="#eef6ee"];
export [label="PDF · note · JSON · CSV\nNo destination transfer implied"];
ai [label="Optional AI quality draft\nState remains unapproved", style="rounded,filled,dashed", fillcolor="#f5f5f5"];
draft -> submit; submit -> validate; validate -> findings;
findings -> fix [label="errors"];
findings -> review [label="no errors"];
fix -> draft [label="preserve old revision"];
review -> fix [label="changes requested"];
review -> approve [label="human approval"];
approve -> export;
validate -> ai [style=dashed]; ai -> review [style=dashed, label="suggestions only"];
'''),
    "records": ("Record links and provenance", "Submitted answers stay fixed. Corrections create linked drafts; exports require approval.", '''
definition [label="Form definition + version\nFields · rules · note template"];
submission [label="Submission revision\nClient reference · owner · state\nPayload SHA-256", fillcolor="#dcebf8", penwidth=2];
answers [label="Structured answers"];
signature [label="Signature acknowledgement\nSame payload hash"];
findings [label="Validation findings\nPrior source ID + current value"];
note [label="Template note draft\nOptional model QA draft"];
audit [label="Append-only application events\nActor · time · review resolution"];
correction [label="Correction draft\nSupersedes prior submission"];
output [label="Approved outputs\nPDF · JSON · CSV · note"];
prior [label="Prior approved submission"];
review [label="Human review decision", fillcolor="#eef6ee"];
definition -> submission; submission -> answers;
submission -> correction [label="linked new record"];
answers -> signature [label="payload hash"];
answers -> findings [label="validation"];
answers -> note [label="template"];
prior -> findings [label="comparison"];
signature -> review; findings -> review; note -> review;
review -> audit [label="decision history"];
review -> output [label="approval gate"];
{rank=same; signature; findings; note;}
{rank=same; audit; output;}
''')
}


def main():
    source = ROOT / "docs/diagrams"
    target = ROOT / "src/franark/resources/diagrams"
    source.mkdir(parents=True, exist_ok=True)
    target.mkdir(parents=True, exist_ok=True)
    for name, (title, caption, body) in DIAGRAMS.items():
        path = source / (name + ".dot")
        path.write_text("digraph " + name + " {\n" + COMMON + body + "\n}\n")
        subprocess.run(["dot", "-Tsvg", str(path), "-o", str(target / (name + ".svg"))], check=True)
        print(name + ": rendered")


if __name__ == "__main__":
    main()
