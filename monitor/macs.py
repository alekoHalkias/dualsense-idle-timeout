import os
import subprocess
import threading
import time
from evdev import InputDevice, list_devices, ecodes

IDLE_TIMEOUT = 10  # seconds
RESCAN_INTERVAL = 2  # seconds
STICK_DRIFT_THRESHOLD = 10  # analog drift filter

controller_threads = {}
lock = threading.Lock()

# Bluetooth MAC cache
_last_bt_query = 0
_bt_cache_ttl = 10  # seconds
_bt_device_cache = {}

def get_dualsense_macs():
    """Return a dictionary of MAC -> device name for DualSense devices, with caching."""
    global _last_bt_query, _bt_device_cache
    now = time.time()
    if now - _last_bt_query < _bt_cache_ttl:
        return _bt_device_cache

    try:
        output = subprocess.run(["bluetoothctl", "devices"], capture_output=True, text=True, check=True).stdout
        _bt_device_cache = {
            line.split()[1]: " ".join(line.split()[2:])
            for line in output.splitlines()
            if "DualSense" in line or "Wireless Controller" in line
        }
        _last_bt_query = now
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Failed to query bluetoothctl: {e}")
        # fallback: keep last cache
    return _bt_device_cache

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

def normalize_mac(mac):
    return mac.strip().lower().replace("-", ":")
