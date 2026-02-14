"""
System tray icon and menu. Blocking run until quit.
"""
import webbrowser
from typing import Callable, Optional

from PIL import Image, ImageDraw
import pystray


def _create_icon_image() -> Image.Image:
    """Create a simple 64x64 icon (clipboard/report style)."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Simple document shape
    d.rectangle([8, 8, 56, 56], outline=(70, 130, 180), width=3, fill=(100, 149, 237, 180))
    d.line([16, 24, 48, 24], fill=(255, 255, 255), width=2)
    d.line([16, 34, 40, 34], fill=(255, 255, 255), width=2)
    d.line([16, 44, 44, 44], fill=(255, 255, 255), width=2)
    return img


def run_tray(
    web_ui_port: int,
    tracker_is_running: Callable[[], bool],
    toggle_tracking: Callable[[], None],
    send_report_now: Optional[Callable[[], None]] = None,
    on_quit: Optional[Callable[[], None]] = None,
) -> None:
    """
    Run the system tray icon. Blocks until user chooses Quit.
    """
    url = f"http://127.0.0.1:{web_ui_port}"

    def open_dashboard(_icon: pystray.Icon, _item: pystray.MenuItem) -> None:
        webbrowser.open(url)

    def toggle_track(_icon: pystray.Icon, _item: pystray.MenuItem) -> None:
        toggle_tracking()

    def send_now(_icon: pystray.Icon, _item: pystray.MenuItem) -> None:
        if send_report_now:
            send_report_now()

    def quit_app(_icon: pystray.Icon, _item: pystray.MenuItem) -> None:
        if on_quit:
            on_quit()
        icon.stop()

    menu_items = [
        pystray.MenuItem("Open Dashboard", open_dashboard),
        pystray.MenuItem("Start / Stop tracking", toggle_track),
    ]
    if send_report_now:
        menu_items.append(pystray.MenuItem("Send report now", send_now))
    menu_items.append(pystray.MenuItem("Quit", quit_app))

    icon = pystray.Icon("work_report", _create_icon_image(), "Work Report", pystray.Menu(*menu_items))

    # Store ref so quit can stop the icon
    run_tray._icon = icon  # type: ignore
    icon.run()


def stop_tray() -> None:
    if getattr(run_tray, "_icon", None):
        run_tray._icon.stop()  # type: ignore
