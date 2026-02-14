"""
Entry point: initialize DB, start tracker, scheduler, web UI, and tray.
Run: python main.py
"""
import threading

from config import settings
from db import get_engine, get_session_factory, init_db
from scheduler import run_daily_report_now, setup_scheduler
from tracker import WindowTracker
from ui import run_tray
from ui.web import create_app


def main() -> None:
    engine = get_engine(settings.database_url)
    init_db(engine)
    session_factory = get_session_factory(engine)

    tracker = WindowTracker(
        session_factory=session_factory,
        poll_interval_seconds=float(settings.tracker_poll_interval_seconds),
    )
    tracker.start()  # start tracking by default

    scheduler = setup_scheduler(
        session_factory=session_factory,
        slack_webhook_url=settings.slack_webhook_url,
        openai_api_key=settings.openai_api_key,
        report_time=settings.report_time,
        timezone_str=settings.timezone,
    )
    scheduler.start()

    def run_report_now():
        return run_daily_report_now(
            session_factory,
            settings.slack_webhook_url,
            settings.openai_api_key,
            settings.timezone,
        )

    app = create_app(
        settings=settings,
        session_factory=session_factory,
        tracker_is_running=lambda: tracker.is_running,
        toggle_tracking=lambda: (tracker.stop() if tracker.is_running else tracker.start()),
        run_report_now=run_report_now,
    )

    def run_flask():
        app.run(host="127.0.0.1", port=settings.web_ui_port, use_reloader=False, threaded=True)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    def on_quit():
        tracker.stop()
        scheduler.shutdown(wait=False)

    run_tray(
        web_ui_port=settings.web_ui_port,
        tracker_is_running=lambda: tracker.is_running,
        toggle_tracking=lambda: (tracker.stop() if tracker.is_running else tracker.start()),
        send_report_now=lambda: run_report_now(),
        on_quit=on_quit,
    )


if __name__ == "__main__":
    main()
