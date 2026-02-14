"""
Flask web UI: dashboard, settings, past reports, activity.
"""
from datetime import date, datetime
from typing import Any, Callable, Optional

from flask import Flask, redirect, render_template, request, url_for

from db.models import DailyReport, WindowSession


def create_app(
    settings: Any,
    session_factory: Any,
    tracker_is_running: Callable[[], bool],
    toggle_tracking: Callable[[], None],
    run_report_now: Optional[Callable[[], tuple[bool, str]]] = None,
) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = settings.flask_secret_key
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    def get_session():
        return session_factory()

    # --- Dashboard ---
    @app.route("/")
    def index():
        with get_session() as session:
            last_report = (
                session.query(DailyReport)
                .order_by(DailyReport.report_date.desc())
                .first()
            )
        return render_template(
            "index.html",
            tracking=tracker_is_running(),
            last_report=last_report,
        )

    # --- Settings (display only; secrets in .env) ---
    @app.route("/settings", methods=["GET", "POST"])
    def settings_page():
        if request.method == "POST":
            # Non-secret settings could be saved to AppSettings here
            return redirect(url_for("index"))
        return render_template(
            "settings.html",
            report_time=settings.report_time,
            timezone=settings.timezone,
            webhook_configured=bool(settings.slack_webhook_url),
            openai_configured=bool(settings.openai_api_key),
        )

    # --- Past reports ---
    @app.route("/reports")
    def reports_list():
        with get_session() as session:
            reports = (
                session.query(DailyReport)
                .order_by(DailyReport.report_date.desc())
                .limit(100)
                .all()
            )
        return render_template("reports.html", reports=reports)

    @app.route("/reports/<int:report_id>")
    def report_detail(report_id: int):
        with get_session() as session:
            report = session.get(DailyReport, report_id)
        if not report:
            return "Report not found", 404
        return render_template("report_detail.html", report=report)

    # --- Activity (sessions for a date) ---
    @app.route("/activity")
    def activity():
        date_str = request.args.get("date")
        if date_str:
            try:
                target_date = date.fromisoformat(date_str)
            except ValueError:
                target_date = date.today()
        else:
            target_date = date.today()

        with get_session() as session:
            from sqlalchemy import cast, Date

            sessions = (
                session.query(WindowSession)
                .where(cast(WindowSession.started_at, Date) == target_date)
                .order_by(WindowSession.started_at.desc())
                .limit(500)
                .all()
            )
        return render_template(
            "activity.html",
            sessions=sessions,
            selected_date=target_date,
        )

    # --- API ---
    @app.route("/api/status")
    def api_status():
        with get_session() as session:
            last = (
                session.query(DailyReport)
                .order_by(DailyReport.report_date.desc())
                .first()
            )
        return {
            "tracking": tracker_is_running(),
            "last_report_date": last.report_date.isoformat() if last else None,
            "last_sent_at": last.sent_at.isoformat() if last and last.sent_at else None,
        }

    @app.route("/api/tracking", methods=["POST"])
    def api_tracking():
        toggle_tracking()
        return {"ok": True, "tracking": tracker_is_running()}

    @app.route("/api/send-report", methods=["POST"])
    def api_send_report():
        if not run_report_now:
            return {"ok": False, "message": "Not configured"}, 400
        ok, message = run_report_now()
        return {"ok": ok, "message": message}

    return app
