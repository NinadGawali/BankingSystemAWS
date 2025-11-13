# BankingSystemAWS — Local Development Guide

This guide shows how to run the Flask API, execute tests, and use helper scripts locally on Windows (PowerShell). Linux/macOS equivalents are included where useful.

## Overview
- Stack: Python + Flask + SQLAlchemy + JWT + Flask-Migrate
- API root: `http://127.0.0.1:5000`
- Static UI: served from `static/` at `/`
- Default DB (local): SQLite at `src/banking.db`
- Optional DB: PostgreSQL via `DATABASE_URL`

## Prerequisites
- Python 3.10+ installed and available in PATH
- PowerShell (Windows). If scripts are blocked, see Troubleshooting.

## Quick Start (Windows PowerShell)
```powershell
# 1) Go to the project root
Set-Location "c:\Users\JCIN\OneDrive\Desktop\BankingSystemAWS"

# 2) Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3) Install dependencies
pip install -r requirements.txt

# 4) Run the Flask app (explicit app factory)
python -m flask --app src.app:create_app run --debug
```
- Open: http://127.0.0.1:5000
- Stop: Ctrl + C

### Alternative run locations
From inside `src/` you can also do:
```powershell
Set-Location .\src
python -m flask --app app:create_app run --debug
```

### Choose a custom port
```powershell
python -m flask --app src.app:create_app run --debug --port 5050
```

## Default Data and Logins
On first run, the app auto-initializes the database and seeds data if empty:
- Admin: `admin` / `admin123`
- User: `user` / `user123`

Health check:
- `GET /health` → verifies DB connectivity and basic status

## Configuration (Environment Variables)
- `SECRET_KEY`: Flask secret key (defaults to `dev-secret-key`)
- `JWT_SECRET_KEY`: JWT signing key (defaults to `dev-jwt-secret`)
- `DATABASE_URL`: SQLAlchemy URL; if not set, uses SQLite `src/banking.db`
  - Postgres `postgres://` is auto-rewritten to `postgresql://`

Examples (PowerShell):
```powershell
$env:SECRET_KEY = "your-strong-secret"
$env:JWT_SECRET_KEY = "your-jwt-secret"
$env:DATABASE_URL = "postgresql://user:password@localhost:5432/banking"
python -m flask --app src.app:create_app run --debug
```

## Using PostgreSQL (optional)
1. Ensure a local PostgreSQL instance is running and a database exists (e.g., `banking`).
2. Set `DATABASE_URL` before starting the server (see above). Example URL formats:
   - `postgresql://postgres:password@localhost:5432/banking`
   - `postgres://...` (will be rewritten to `postgresql://` automatically)

## Running Tests
From the project root:
```powershell
Set-Location "c:\Users\JCIN\OneDrive\Desktop\BankingSystemAWS"
.\.venv\Scripts\Activate.ps1  # if not already active
python -m pytest -q
```

## Running Helper Scripts
Example smoke test for transaction hash storage:
```powershell
Set-Location "c:\Users\JCIN\OneDrive\Desktop\BankingSystemAWS"
.\.venv\Scripts\Activate.ps1  # if not already active
python .\scripts\smoke_hash.py
```

## Project Structure (essentials)
```
requirements.txt
src/
  app.py            # Flask app factory (create_app)
  models.py         # SQLAlchemy models & db
  api/routes/       # Blueprints: users, accounts, loans
  utils/            # helpers: JWT, keepalive, json utils, tx hash store
static/             # Frontend served at '/'
  index.html
  css/, js/
tests/              # pytest tests for core, managers, routes, utils
scripts/
  smoke_hash.py     # small script exercising tx hash store
```

## Common Troubleshooting
- Activation policy error in PowerShell:
  - If running `Activate.ps1` is blocked, run once in the current session:
    ```powershell
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    .\.venv\Scripts\Activate.ps1
    ```
- Port already in use:
  - Add `--port 5050` (or another free port) to the run command.
- Import/path issues:
  - Run commands from the project root and use the explicit `--app src.app:create_app`.
- DB not initializing / empty:
  - First run should auto-create tables. You can also hit `GET /init-database` to trigger manual initialization.
- Switching to Postgres:
  - Ensure `DATABASE_URL` is set before starting; verify credentials and network access.

## Useful URLs
- UI: `http://127.0.0.1:5000/`
- API base: `http://127.0.0.1:5000/api/v1`
- Health: `http://127.0.0.1:5000/health`

## Notes
- For development only, default secrets are fine; change secrets for any non-local use.
- SQLite file is created at `src/banking.db` when `DATABASE_URL` is not set.
