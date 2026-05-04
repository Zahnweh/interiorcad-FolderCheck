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
    # NSUserNotificationCenter schickt die Notification vom laufenden Prozess –
    # Klick auf "Anzeigen" öffnet unsere App, nicht den Script Editor.
    try:
        from Foundation import NSUserNotification, NSUserNotificationCenter
        notif = NSUserNotification.alloc().init()
        notif.setTitle_(title)
        notif.setInformativeText_(message)
        NSUserNotificationCenter.defaultUserNotificationCenter() \
            .deliverNotification_(notif)
    except Exception:
        # Fallback für den Fall dass PyObjC nicht verfügbar ist
        safe_msg   = message.replace('"', '\\"')
        safe_title = title.replace('"', '\\"')
        subprocess.Popen(
            ["osascript", "-e",
             f'display notification "{safe_msg}" with title "{safe_title}"'],
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
