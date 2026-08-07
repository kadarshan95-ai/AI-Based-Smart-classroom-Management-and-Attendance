SnapClass — Flask classroom dashboard

Quick start (PowerShell)

1. Open PowerShell and activate your virtualenv (if you have one):

   .\.venv\Scripts\Activate.ps1

2. From the project folder run (explicit --app argument required):

   python -m flask --app app run --host 127.0.0.1 --port 5000

   OR run the app module directly:

   python app.py

Common error you saw:

  Error: Option '--app' requires an argument.

This happens when `--app` is provided with no value. Use `--app app` (the module or filename without .py).

Run scripts

- PowerShell: `run.ps1` (calls the same flask command safely for PowerShell)
- CMD: `run.bat`

If ports are in use, change `--port` to an available port.

Files of interest

- `app.py` — main Flask application and DB seeding
- `snapclass.db` — SQLite database (generated automatically)
- `templates/` — HTML templates
- `static/` — CSS

If you'd like, I can start the server for you or open the dashboard in your browser.