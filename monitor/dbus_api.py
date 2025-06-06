# monitor/dbus_api.py

import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib
import json
import os

# ✅ Set the main loop globally BEFORE any connections are made
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

BUS_NAME = "org.dualsense.Monitor"
OBJ_PATH = "/org/dualsense/Monitor"

class StatusService(dbus.service.Object):
    def __init__(self, get_status_fn):
        self.get_status_fn = get_status_fn
        self.bus = dbus.SessionBus()
        name = dbus.service.BusName(BUS_NAME, self.bus)
        super().__init__(name, OBJ_PATH)

    @dbus.service.method(BUS_NAME, in_signature="", out_signature="s")
    def GetStatus(self):
        data = self.get_status_fn()
        return json.dumps(data)
    @dbus.service.method(BUS_NAME, in_signature="", out_signature="s")
    def SendStatusToast(self):
        data = self.get_status_fn()
        lines = []

        for info in data.values():
            name = info.get("name", "Controller")
            battery = info.get("battery", "Unknown")
            charging = info.get("charging", False)
            idle = info.get("idle_for", 0)
            mac = info.get("mac", "??")
            timeout = int(os.environ.get("DUALSENSE_TIMEOUT", 60))

            if charging:
                status = "⚡ Charging"
            else:
                remaining = max(0, timeout - idle)
                status = f"Idle in {remaining:.0f}s"

            lines.append(f"{name} ({mac}) — {battery} — {status}")

        from monitor.notif import send_dbus_notification
        send_dbus_notification("🎮 DualSense Status", "\n".join(lines))
        return "ok"

def run_dbus_loop(get_status_fn):
    print("📡 D-Bus service starting...")
    service = StatusService(get_status_fn)
    print("✅ D-Bus service registered")
    loop = GLib.MainLoop()
    loop.run()
