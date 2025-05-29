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

def run_dbus_loop(get_status_fn):
    print("📡 D-Bus service starting...")
    service = StatusService(get_status_fn)
    print("✅ D-Bus service registered")
    loop = GLib.MainLoop()
    loop.run()
