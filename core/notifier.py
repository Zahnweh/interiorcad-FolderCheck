"""
core/notifier.py
Plattformübergreifende System-Notifications.
macOS: osascript (keine Abhängigkeit). Windows: plyer.
"""

import platform
import subprocess


def notify(title: str, message: str) -> None:
    """Zeigt eine System-Notification. Schlägt lautlos fehl."""
    try:
        if platform.system() == "Darwin":
            _notify_mac(title, message)
        elif platform.system() == "Windows":
            _notify_windows(title, message)
    except Exception:
        pass


def _notify_mac(title: str, message: str) -> None:
    safe_msg   = message.replace('"', '\\"')
    safe_title = title.replace('"', '\\"')
    script = (
        f'display notification "{safe_msg}" '
        f'with title "{safe_title}" '
        f'sound name "default"'
    )
    subprocess.Popen(
        ["osascript", "-e", script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _notify_windows(title: str, message: str) -> None:
    from plyer import notification
    notification.notify(
        title=title,
        message=message,
        app_name="interiorcad FolderCheck",
        timeout=8,
    )
