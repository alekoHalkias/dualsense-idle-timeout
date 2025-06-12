# monitor/battery.py

from dbus_next.aio import MessageBus
from dbus_next.constants import MessageType
from dbus_next import BusType
import asyncio
import threading
import time
import subprocess
from .macs import normalize_mac

upower_path = "/org/freedesktop/UPower"
upower_interface = "org.freedesktop.UPower"
device_interface = "org.freedesktop.UPower.Device"

# Shared event loop and background thread
_loop = asyncio.new_event_loop()
_thread = threading.Thread(target=_loop.run_forever, daemon=True)
_thread.start()

def run_async_task(coro):
    return asyncio.run_coroutine_threadsafe(coro, _loop).result()

async def get_device_info(mac):
    try:
        bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
        introspection = await bus.introspect("org.freedesktop.UPower", upower_path)
        upower = bus.get_proxy_object("org.freedesktop.UPower", upower_path, introspection)
        upower_iface = upower.get_interface(upower_interface)
        device_paths = await upower_iface.call_enumerate_devices()

        mac = normalize_mac(mac)
        for path in device_paths:
            try:
                device_obj = await bus.introspect("org.freedesktop.UPower", path)
                device = bus.get_proxy_object("org.freedesktop.UPower", path, device_obj)
                dev_iface = device.get_interface(device_interface)

                props = await dev_iface.get_all()
                serial = props.get("Serial", "")
                if normalize_mac(serial) == mac:
                    percentage = props.get("Percentage", 0.0)
                    state = props.get("State", 0)  # 1=charging, 2=discharging, 4=fully charged
                    charging = state in [1, 4]
                    return f"{percentage:.0f}%", charging
            except Exception:
                continue
    except Exception as e:
        print(f"⚠️ D-Bus UPower query failed: {e}")

    # Fallback to subprocess if D-Bus fails
    try:
        output = subprocess.run(["upower", "-e"], capture_output=True, text=True).stdout
        devices = [d for d in output.splitlines() if "ps_controller_battery" in d]

        for device in devices:
            info = subprocess.run(["upower", "-i", device], capture_output=True, text=True).stdout
            found_mac = False
            battery = "Unknown"
            charging = False

            for line in info.splitlines():
                line = line.strip()
                if line.startswith("serial:"):
                    serial_mac = normalize_mac(line.split(":", 1)[1])
                    if serial_mac == normalize_mac(mac):
                        found_mac = True
                if found_mac and line.startswith("percentage:"):
                    battery = line.split(":", 1)[1].strip()
                if found_mac and line.startswith("icon-name:"):
                    charging = "charging" in line.lower() or "charged" in line.lower()

            if found_mac:
                return battery, charging
    except Exception as e:
        print(f"⚠️ Fallback battery check failed: {e}")

    return "Unknown", False

def get_battery_level(mac):
    return run_async_task(get_device_info(mac))[0]

def is_charging(mac):
    return run_async_task(get_device_info(mac))[1]
