"""
APScheduler: run daily report at configured time in configured timezone.
"""
from datetime import date, datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from db.models import DailyReport
from report.generator import generate_daily_report_text
from report.slack_sender import send_report_to_slack


def run_daily_report_now(
    session_factory,
    slack_webhook_url: str,
    openai_api_key: str,
    timezone_str: str,
) -> tuple[bool, str]:
    """
    Generate report for today (in given timezone), send to Slack, save to daily_reports.
    Returns (success: bool, message: str).
    """
    tz = ZoneInfo(timezone_str)
    report_date = datetime.now(tz).date()

    try:
        report_text = generate_daily_report_text(
            report_date, session_factory, openai_api_key, timezone_str
        )
    except Exception as e:
        return False, f"Report generation failed: {e}"

    sent = send_report_to_slack(slack_webhook_url, report_text)
    sent_at = datetime.now(tz) if sent else None

    with session_factory() as session:
        # Upsert by report_date
        existing = session.query(DailyReport).filter(DailyReport.report_date == report_date).first()
        if existing:
            existing.report_text = report_text
            existing.sent_at = sent_at
        else:
            session.add(
                DailyReport(
                    report_date=report_date,
                    report_text=report_text,
                    sent_at=sent_at,
                )
            )
        session.commit()

    if sent:
        return True, "Report sent to Slack."
    return False, "Report generated but Slack send failed."


def setup_scheduler(
    session_factory,
    slack_webhook_url: str,
    openai_api_key: str,
    report_time: str,
    timezone_str: str,
) -> BackgroundScheduler:
    """Parse report_time (HH:MM), add daily job at that time in timezone_str. Call start() on returned scheduler."""
    hour, minute = 18, 0
    if ":" in report_time:
        parts = report_time.strip().split(":")
        try:
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
        except ValueError:
            pass

    tz = ZoneInfo(timezone_str)
    scheduler = BackgroundScheduler(timezone=tz)

    def job():
        run_daily_report_now(
            session_factory,
            slack_webhook_url,
            openai_api_key,
            timezone_str,
        )

    scheduler.add_job(
        job,
        CronTrigger(hour=hour, minute=minute),
        id="daily_report",
    )
    return scheduler
