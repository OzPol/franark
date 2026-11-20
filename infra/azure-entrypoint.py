"""Prepare the mounted application directory before dropping root privileges."""
import os
from pathlib import Path
import pwd

directory = Path(os.environ.get("FRANARK_DATA_DIR", "/home/franark-data")).resolve()
if not directory.is_relative_to(Path("/home")):
    raise RuntimeError("Azure application data must be stored beneath /home.")
account = pwd.getpwnam("franark")
directory.mkdir(parents=True, exist_ok=True)
os.chown(directory, account.pw_uid, account.pw_gid)
os.setgroups([])
os.setgid(account.pw_gid)
os.setuid(account.pw_uid)
os.execvp("uvicorn", ["uvicorn", "franark.app:app", "--host", "0.0.0.0", "--port", "8765", "--workers", "1", "--proxy-headers"])
