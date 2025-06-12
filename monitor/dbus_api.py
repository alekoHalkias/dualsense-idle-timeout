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
            idle = info.get("idle_remaining", 0)
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
    
    @dbus.service.method(BUS_NAME, in_signature="i", out_signature="s")
    def SetTimeout(self, seconds):
        from monitor.config import HOME_CONFIG, load_config
        from configparser import ConfigParser
        from monitor.notif import log

        if not isinstance(seconds, int) or seconds < 5:
            return "Invalid timeout value"

        config = ConfigParser()
        config.read(HOME_CONFIG)
        if not config.has_section("monitor"):
            config.add_section("monitor")
        config.set("monitor", "idle_timeout", str(seconds))
        with open(HOME_CONFIG, "w") as f:
            config.write(f)

        log(f"⏱️ Idle timeout updated to {seconds}s", notify=True, summary="Idle Timeout Changed")
        return f"Idle timeout set to {seconds}s"

    @dbus.service.method(BUS_NAME, in_signature="i", out_signature="s")
    def DisconnectByIndex(self, index):
        from monitor.monitor import controller_threads, lock
        import subprocess
        from monitor.notif import log

        with lock:
            for info in controller_threads.values():
                if info.get("player") == index:
                    mac = info.get("mac")
                    name = info.get("name", "Unknown")
                    if not mac:
                        return f"{name} has no MAC — cannot disconnect"

                    try:
                        subprocess.run(["bluetoothctl", "disconnect", mac], check=True)
                        log(f"🔌 Disconnected {name} (Player {index})", notify=True, summary="Disconnected")
                        return f"Disconnected {name} (Player {index})"
                    except subprocess.CalledProcessError as e:
                        return f"Failed to disconnect Player {index}: {e}"

        return f"No controller found at index {index}"

def run_dbus_loop(get_status_fn):
    print("📡 D-Bus service starting...")
    service = StatusService(get_status_fn)
    print("✅ D-Bus service registered")
    loop = GLib.MainLoop()
    loop.run()
