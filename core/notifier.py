"""
core/notifier.py
Plattformübergreifende System-Notifications.
macOS: osascript (keine Abhängigkeit). Windows: plyer.
"""

import platform
import subprocess

_delegate = None   # hält den NSUserNotificationCenter-Delegate am Leben


def setup_notification_handler(on_show_cb) -> None:
    """
    Registriert einen Delegate für NSUserNotificationCenter.
    on_show_cb wird aufgerufen wenn der User auf 'Anzeigen' klickt.
    Muss vom Hauptthread aus aufgerufen werden.
    """
    if platform.system() != "Darwin":
        return
    global _delegate
    try:
        from Foundation import NSObject, NSUserNotificationCenter
        import objc

        class _Delegate(NSObject):
            def userNotificationCenter_didActivateNotification_(
                    self, center, notification):
                if on_show_cb:
                    on_show_cb()

            def userNotificationCenter_shouldPresentNotification_(
                    self, center, notification):
                return True

        _delegate = _Delegate.alloc().init()
        NSUserNotificationCenter.defaultUserNotificationCenter() \
            .setDelegate_(_delegate)
    except Exception:
        pass


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
