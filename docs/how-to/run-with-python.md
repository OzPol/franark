# Run without Docker

Install Python 3.12 on Windows. In PowerShell, from the repository:

```powershell
py -3.12 -m venv .venv
```

```powershell
.\.venv\Scripts\python.exe -m pip install -c requirements.lock -e ".[openai,dev,docs]"
```

```powershell
Copy-Item .env.example .env
```

```powershell
.\.venv\Scripts\franark.exe serve
```

Open <http://127.0.0.1:8765>. Keep that terminal open. This path avoids changing
PowerShell execution policy because it does not activate an environment script.

In a second PowerShell window, build the docs:

```powershell
.\.venv\Scripts\python.exe -m sphinx -W --keep-going -b html docs docs/_build/html
```

Serve the generated documentation:

```powershell
.\.venv\Scripts\python.exe -m http.server 8766 --bind 127.0.0.1 --directory docs/_build/html
```

For Linux/macOS, use `python3 -m venv .venv`, `.venv/bin/python`, and
`.venv/bin/franark` in the equivalent commands.
