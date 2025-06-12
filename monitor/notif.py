import dbus
import os 
import time
import subprocess
import hashlib

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(SCRIPT_DIR, "dualsensewhite.svg")

_last_notify_time = 0
_last_notify_id = 0
_last_notify_hash = None
_NOTIFY_COOLDOWN = 3  # seconds

def send_dbus_notification(summary, body="", icon=ICON_PATH):
    global _last_notify_time, _last_notify_id, _last_notify_hash

    now = time.time()
    full_body = f"<b>{summary}</b>\n{body}" if body else f"<b>{summary}</b>"
    body_hash = hashlib.sha256(full_body.encode()).hexdigest()

    # Throttle if message is too soon or identical
    if now - _last_notify_time < _NOTIFY_COOLDOWN and body_hash == _last_notify_hash:
        return

    try:
        session_bus = dbus.SessionBus()
        notify_obj = session_bus.get_object("org.freedesktop.Notifications", "/org/freedesktop/Notifications")
        notify = dbus.Interface(notify_obj, "org.freedesktop.Notifications")

        if not os.path.exists(icon):
            icon = ""

        hints = dbus.Dictionary({
            "urgency": dbus.Byte(1),
            "category": "device",
            "desktop-entry": "dualsense-idle-monitor"
        }, signature="sv")

        _last_notify_id = notify.Notify(
            "DualSense Idle Monitor",
            _last_notify_id,
            icon,
            "",  # Empty summary for KDE/Plasma workaround
            full_body,
            [],
            hints,
            -1
        )
        _last_notify_time = now
        _last_notify_hash = body_hash

    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] ⚠️ D-Bus notification failed: {e}")

def log(msg, notify=False, summary=""):
    timestamp = f"[{time.strftime('%H:%M:%S')}]"
    print(f"{timestamp} {msg}")
    if notify:
        send_dbus_notification(summary, msg)
