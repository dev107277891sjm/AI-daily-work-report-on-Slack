"""
Build daily activity stats from DB and generate report text using OpenAI.
"""
from datetime import date
from typing import Any

from openai import OpenAI
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from db.models import WindowSession


def get_daily_stats(
    session: Session, report_date: date, timezone_str: str = "UTC"
) -> list[dict[str, Any]]:
    """Aggregate window sessions by process_name for the given date in the given timezone. Returns list of {process_name, total_minutes}."""
    # started_at is stored as UTC; filter by date in user's timezone
    rows = (
        session.query(
            WindowSession.process_name,
            func.coalesce(func.sum(WindowSession.duration_seconds), 0).label("total_seconds"),
        )
        .where(
            text(
                "(window_sessions.started_at AT TIME ZONE :tz)::date = :d"
            ).bindparams(tz=timezone_str, d=report_date)
        )
        .group_by(WindowSession.process_name)
        .order_by(func.sum(WindowSession.duration_seconds).desc())
        .all()
    )
    return [
        {"process_name": r.process_name, "total_minutes": round(r.total_seconds / 60.0, 1)}
        for r in rows
    ]


def generate_daily_report_text(
    report_date: date,
    session_factory: Any,
    openai_api_key: str,
    timezone_str: str = "UTC",
) -> str:
    """
    Load daily stats from DB, call ChatGPT to produce a short professional report, return the text.
    """
    with session_factory() as session:
        stats = get_daily_stats(session, report_date, timezone_str)

    if not stats:
        return (
            f"Daily work report for {report_date.isoformat()}: No window activity was recorded for this day."
        )

    # Build a simple table for the prompt
    lines = ["Application | Total minutes", "---|---"]
    for s in stats[:30]:  # cap at 30 apps
        lines.append(f"{s['process_name']} | {s['total_minutes']}")
    table = "\n".join(lines)

    client = OpenAI(api_key=openai_api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a concise assistant. Given daily application usage statistics (process name and minutes used), write a brief professional daily work report in 3–5 sentences. Focus on what kind of work was likely done (e.g. coding, browsing, meetings) without making up details. Use neutral, formal tone.",
            },
            {
                "role": "user",
                "content": f"Date: {report_date.isoformat()}\n\nUsage statistics (top applications by time):\n{table}\n\nWrite the daily work report:",
            },
        ],
        max_tokens=400,
    )
    text = (response.choices[0].message.content or "").strip()
    return text or "No report generated."
