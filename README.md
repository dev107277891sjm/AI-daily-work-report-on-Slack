# Daily Work Report to Slack

A Windows desktop app that tracks active window usage in real time, stores data in PostgreSQL, generates daily reports with ChatGPT, and sends them to a Slack channel at a scheduled time. It includes a system tray icon and a simple web UI for settings and past reports.

## Features

- **Real-time window tracking**: Records the foreground window and process name at a configurable interval (default 5 seconds).
- **Exact duration**: Each window session is stored with start, end, and duration in seconds.
- **PostgreSQL**: All sessions and reports are stored in the database.
- **Daily report**: At a configured time (and timezone), the app aggregates the day’s activity, generates a short report with OpenAI (ChatGPT), and sends it to Slack.
- **Tray icon**: Start/stop tracking, open dashboard, send report now, quit.
- **Web UI**: Dashboard, past reports, activity by date, and settings (secrets live in `.env`).

## Prerequisites

- **Windows** (uses `pywin32` and window APIs).
- **Python 3.10+** (for `zoneinfo`).
- **PostgreSQL** (running and reachable).
- **Slack**: Incoming Webhook URL for the target channel.
- **OpenAI**: API key for report generation.

## Setup

1. **Clone or copy the project** and open a terminal in the project root.

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   - Copy `.env.example` to `.env`.
   - Edit `.env` and set:
     - `DATABASE_URL` — PostgreSQL connection string, e.g. `postgresql://user:password@localhost:5432/work_report_db`
     - `SLACK_WEBHOOK_URL` — Slack Incoming Webhook URL.
     - `OPENAI_API_KEY` — Your OpenAI API key.
     - Optionally: `REPORT_TIME` (e.g. `18:00`), `TIMEZONE` (e.g. `Europe/Kyiv`), `FLASK_SECRET_KEY`, `TRACKER_POLL_INTERVAL_SECONDS`, `WEB_UI_PORT`.

5. **Create the database and tables** (once):
   ```bash
   python -m scripts.init_db
   ```

6. **Run the application**:
   ```bash
   python main.py
   ```

   - A tray icon appears; use it to open the dashboard, start/stop tracking, send a report now, or quit.
   - Open **http://127.0.0.1:5050** (or your `WEB_UI_PORT`) for the web UI.

### Windows: "Running scripts is disabled" (PowerShell)

If `.venv\Scripts\activate` fails in PowerShell, use one of these:

- **Option A — Use the venv without activating** (any shell):
  ```bash
  .venv\Scripts\python.exe -m scripts.init_db
  .venv\Scripts\python.exe main.py
  ```
- **Option B — Use Command Prompt (cmd)** and run:
  ```bash
  .venv\Scripts\activate.bat
  pip install -r requirements.txt
  python -m scripts.init_db
  python main.py
  ```
- **Option C — Allow scripts for your user** (PowerShell once):
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```
  Then `.venv\Scripts\activate` will work in PowerShell.

## Project structure

- `config/settings.py` — Loads and validates settings from `.env`.
- `db/` — SQLAlchemy models and session; tables: `window_sessions`, `daily_reports`, `app_settings`.
- `tracker/window_tracker.py` — Background thread that polls the foreground window and writes sessions to the DB.
- `report/generator.py` — Builds daily stats and calls OpenAI for report text.
- `report/slack_sender.py` — Sends the report to Slack via webhook.
- `scheduler/job.py` — APScheduler job that runs the daily report at the configured time.
- `ui/tray.py` — System tray icon and menu.
- `ui/web/` — Flask app: dashboard, settings, reports list, report detail, activity by date.
- `main.py` — Entry point: init DB, start tracker, scheduler, Flask (in a thread), and tray.

## Security

- **Secrets** (database URL, Slack webhook, OpenAI API key) are read only from `.env`. Do not commit `.env`; it is in `.gitignore`.
- The web UI does not display or log raw secrets; it only shows whether they are configured.

## Customization

- **Report time and timezone**: Set `REPORT_TIME` and `TIMEZONE` in `.env`, then restart.
- **Poll interval**: `TRACKER_POLL_INTERVAL_SECONDS` (default 5).
- **Web UI port**: `WEB_UI_PORT` (default 5050).

## Scaling and maintenance

- The design is modular: tracker, report, scheduler, and UI can be extended or replaced independently.
- All persistent data is in PostgreSQL; you can add backups and indexing as needed.
- For high load, consider moving report generation to a queue (e.g. Celery) and keeping the tracker and UI as-is.

## Report

A detailed **project plan** is in `PROJECT_PLAN.md`, including architecture, module breakdown, and build order.
