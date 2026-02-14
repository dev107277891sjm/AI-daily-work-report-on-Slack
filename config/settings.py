"""
Application settings loaded from environment (.env).
All sensitive data should be in .env; this module validates on import.
"""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)


@dataclass(frozen=True)
class Settings:
    """Validated settings from environment."""

    database_url: str
    slack_webhook_url: str
    openai_api_key: str
    report_time: str  # "HH:MM" 24h
    timezone: str
    flask_secret_key: str
    tracker_poll_interval_seconds: int
    web_ui_port: int

    @classmethod
    def from_env(cls) -> "Settings":
        database_url = os.getenv("DATABASE_URL")
        slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL", "").strip()
        openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        report_time = os.getenv("REPORT_TIME", "18:00").strip()
        timezone = os.getenv("TIMEZONE", "UTC").strip()
        flask_secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-in-production").strip()
        tracker_poll = int(os.getenv("TRACKER_POLL_INTERVAL_SECONDS", "5"))
        web_port = int(os.getenv("WEB_UI_PORT", "5050"))

        if not database_url:
            raise SystemExit(
                "Missing DATABASE_URL in .env. Example: postgresql://user:password@localhost:5432/work_report_db"
            )
        if not slack_webhook_url:
            raise SystemExit("Missing SLACK_WEBHOOK_URL in .env. Add your Slack Incoming Webhook URL.")
        if not openai_api_key:
            raise SystemExit("Missing OPENAI_API_KEY in .env. Add your OpenAI API key.")

        if tracker_poll < 1:
            tracker_poll = 1
        if web_port < 1 or web_port > 65535:
            web_port = 5050

        return cls(
            database_url=database_url,
            slack_webhook_url=slack_webhook_url,
            openai_api_key=openai_api_key,
            report_time=report_time,
            timezone=timezone,
            flask_secret_key=flask_secret_key,
            tracker_poll_interval_seconds=tracker_poll,
            web_ui_port=web_port,
        )


settings = Settings.from_env()
