import dbus
import os 
import time
import subprocess


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(SCRIPT_DIR, "dualsensewhite.svg")


def send_dbus_notification(summary, body="", icon=ICON_PATH):
    try:
        session_bus = dbus.SessionBus()
        notify_obj = session_bus.get_object("org.freedesktop.Notifications", "/org/freedesktop/Notifications")
        notify = dbus.Interface(notify_obj, "org.freedesktop.Notifications")

        if not os.path.exists(icon):
            icon = ""

        # Plasma doesn't show summary separately — emulate bold manually
        full_body = f"<b>{summary}</b>\n{body}" if body else f"<b>{summary}</b>"

        hints = dbus.Dictionary({
            "urgency": dbus.Byte(1),
            "category": "device",
            "desktop-entry": "dualsense-idle-monitor"  # improves KDE integration
        }, signature="sv")

        notify.Notify(
            "DualSense Idle Monitor",  # app name
            0,
            icon,
            "",                         # KDE ignores summary; send empty
            full_body,                 # manually constructed message
            [],
            hints,
            -1
        )
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] ⚠️ D-Bus notification failed: {e}")

def log(msg, notify=False,summary=""):
    timestamp= f"[{time.strftime('%H:%M:%S')}]"
    print(f"{timestamp} {msg}")
    if notify:
        send_dbus_notification(summary, msg)
