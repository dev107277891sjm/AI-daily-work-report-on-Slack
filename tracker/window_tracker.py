"""
Real-time tracker of the active Windows foreground window.
Records process name and window title; computes exact duration per session.
"""
import threading
import time
from datetime import datetime, timezone
from typing import Callable, Optional

import psutil
from sqlalchemy.orm import Session

# Windows-only
try:
    import win32gui
    import win32process
except ImportError:
    win32gui = None
    win32process = None


def _get_foreground_window_info() -> Optional[tuple[str, str]]:
    """Returns (process_name, window_title) or None if not on Windows or no window."""
    if win32gui is None or win32process is None:
        return None
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None
        title = win32gui.GetWindowText(hwnd) or ""
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if not pid:
            return None
        proc = psutil.Process(pid)
        name = proc.name() or "Unknown"
        return (name, title)
    except Exception:
        return None


class WindowTracker:
    """
    Runs in a background thread; polls foreground window at interval.
    On change, closes previous session (sets ended_at, duration_seconds) and starts new one.
    """

    def __init__(
        self,
        session_factory: Callable[[], Session],
        poll_interval_seconds: float = 5.0,
    ):
        self._session_factory = session_factory
        self._poll_interval = poll_interval_seconds
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._current_process: Optional[str] = None
        self._current_title: Optional[str] = None
        self._current_started_at: Optional[datetime] = None
        self._running = False

    def _persist_session(
        self,
        process_name: str,
        window_title: str,
        started_at: datetime,
        ended_at: datetime,
    ) -> None:
        duration = (ended_at - started_at).total_seconds()
        from db.models import WindowSession

        with self._session_factory() as session:
            row = WindowSession(
                process_name=process_name,
                window_title=window_title,
                started_at=started_at,
                ended_at=ended_at,
                duration_seconds=duration,
            )
            session.add(row)
            session.commit()

    def _tick(self, now: datetime) -> None:
        info = _get_foreground_window_info()
        if info is None:
            return
        process_name, window_title = info

        if self._current_process is not None and (
            self._current_process != process_name or self._current_title != window_title
        ):
            # Window changed: end previous session
            self._persist_session(
                self._current_process,
                self._current_title or "",
                self._current_started_at,
                now,
            )

        # Start or continue current session
        if self._current_process != process_name or self._current_title != window_title:
            self._current_process = process_name
            self._current_title = window_title
            self._current_started_at = now

    def _run_loop(self) -> None:
        while not self._stop.wait(timeout=self._poll_interval):
            now = datetime.now(timezone.utc)
            try:
                self._tick(now)
            except Exception:
                # Log but keep running
                pass

        # On stop: close current session if any
        if self._current_process is not None and self._current_started_at is not None:
            try:
                self._persist_session(
                    self._current_process,
                    self._current_title or "",
                    self._current_started_at,
                    datetime.now(timezone.utc),
                )
            except Exception:
                pass

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._stop.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=self._poll_interval * 3)
            self._thread = None

    @property
    def is_running(self) -> bool:
        return self._running
