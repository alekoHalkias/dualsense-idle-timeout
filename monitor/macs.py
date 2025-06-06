import os
import subprocess
import threading
import time
from evdev import InputDevice, list_devices, ecodes
# from monitor.notif import send_dbus_notification, log

IDLE_TIMEOUT =  10     # seconds
RESCAN_INTERVAL = 2    # seconds
STICK_DRIFT_THRESHOLD = 10  # analog drift filter

controller_threads = {}
lock = threading.Lock()

# Find all known DualSense MACs from bluetoothctl
def get_dualsense_macs():
    output = subprocess.run(["bluetoothctl", "devices"], capture_output=True, text=True).stdout
    return {
        line.split()[1]: " ".join(line.split()[2:])
        for line in output.splitlines()
        if "DualSense" in line or "Wireless Controller" in line
    }

# For a given /dev/input/eventX, get its MAC from sysfs (uniq)
def get_mac_for_device(dev_path):
    try:
        event_name = os.path.basename(dev_path)
        uniq_path = f"/sys/class/input/{event_name}/device/uniq"
        if os.path.exists(uniq_path):
            with open(uniq_path) as f:
                mac = f.read().strip()
                return mac if mac else None
    except Exception:
        pass
    return None

# Find all DualSense input devices + MACs
def find_dualsense_event_devices():
    devices = []
    for path in list_devices():
        try:
            dev = InputDevice(path)
            if "dualsense" in dev.name.lower() or "wireless controller" in dev.name.lower():
                mac = get_mac_for_device(path)
                devices.append((path, dev.name, mac))
        except Exception:
            continue
    return devices
