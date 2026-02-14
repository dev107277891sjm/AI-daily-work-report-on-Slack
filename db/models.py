"""
SQLAlchemy models for PostgreSQL.
"""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Float, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class WindowSession(Base):
    """One continuous period of a window being in foreground."""

    __tablename__ = "window_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    process_name: Mapped[str] = mapped_column(String(512), index=True)
    window_title: Mapped[str] = mapped_column(String(1024), default="")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"WindowSession(process={self.process_name!r}, started={self.started_at})"


class DailyReport(Base):
    """Generated daily report text and send metadata."""

    __tablename__ = "daily_reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    report_date: Mapped[date] = mapped_column(Date, unique=True, index=True)
    report_text: Mapped[str] = mapped_column(Text)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    slack_channel: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"DailyReport(date={self.report_date}, sent={self.sent_at})"


class AppSettings(Base):
    """Key-value store for UI-managed non-secret settings (report time, timezone display, etc.)."""

    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    value: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"AppSettings(key={self.key!r})"
