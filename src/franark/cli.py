import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

from dotenv import load_dotenv


def main():
    parser = argparse.ArgumentParser(prog="franark")
    parser.add_argument("command", choices=["serve", "demo"])
    args = parser.parse_args()
    load_dotenv()
    if args.command == "serve":
        import uvicorn
        uvicorn.run("franark.app:app", host="127.0.0.1", port=8765, workers=1)
    else:
        from .pipeline import SAMPLE_NOTES, markdown_report, run_saved
        from .settings import Settings
        from .store import Store
        with TemporaryDirectory() as folder:
            store = Store(Path(folder) / "demo.sqlite3")
            run_id, _ = store.create("Synthetic meeting", SAMPLE_NOTES, "it", "demo", "cli-demo")
            run_saved(store, run_id, Settings())
            print(markdown_report(store.get(run_id)))


if __name__ == "__main__":
    main()
