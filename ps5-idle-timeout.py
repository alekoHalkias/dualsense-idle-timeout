#!/usr/bin/env python3

import os
import time
import subprocess
import threading
from evdev import InputDevice, list_devices, ecodes

IDLE_TIMEOUT = 5       # seconds
RESCAN_INTERVAL = 2    # seconds
STICK_DRIFT_THRESHOLD = 10  # analog drift filter

controller_threads = {}
lock = threading.Lock()

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

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

# Per-controller thread that watches for idle and disconnects
def monitor_controller(dev_path, name, mac, stop_event):
    try:
        dev = InputDevice(dev_path)
        log(f"🕹️ Monitoring {name} ({mac}) at {dev_path}")
    except Exception as e:
        log(f"❌ Could not open {dev_path}: {e}")
        return

    last_input = time.time()
    abs_state = {}
    disconnected = False

    try:
        for event in dev.read_loop():
            if stop_event.is_set():
                break

            if event.type == ecodes.EV_ABS:
                prev = abs_state.get(event.code, event.value)
                delta = abs(event.value - prev)
                abs_state[event.code] = event.value
                if delta > STICK_DRIFT_THRESHOLD:
                    last_input = time.time()
                    disconnected = False

            elif event.type == ecodes.EV_KEY:
                last_input = time.time()
                disconnected = False

            if not disconnected and time.time() - last_input > IDLE_TIMEOUT:
                if mac:
                    log(f"⚠️ {name} is idle, disconnecting {mac}")
                    subprocess.run(["bluetoothctl", "disconnect", mac])
                    disconnected = True
                else:
                    log(f"⚠️ {name} idle but no MAC found — can't disconnect")

    except OSError:
        log(f"🔌 Device {name} disconnected unexpectedly")

    log(f"🛑 Finished monitoring {name}")

# Thread to monitor and assign threads to new controllers
def scan_loop():
    while True:
        macs = get_dualsense_macs()
        devices = find_dualsense_event_devices()

        with lock:
            for path, name, mac in devices:
                if path not in controller_threads:
                    stop_event = threading.Event()
                    t = threading.Thread(target=monitor_controller, args=(path, name, mac, stop_event), daemon=True)
                    controller_threads[path] = {"thread": t, "stop": stop_event}
                    t.start()
                    log(f"✅ Started monitoring {name} ({mac})")

            # Cleanup dead threads
            to_remove = []
            for path, info in controller_threads.items():
                if not info["thread"].is_alive():
                    info["stop"].set()
                    to_remove.append(path)
            for path in to_remove:
                del controller_threads[path]

        time.sleep(RESCAN_INTERVAL)

if __name__ == "__main__":
    log("🔍 Starting DualSense idle monitor...")
    try:
        scan_loop()
    except KeyboardInterrupt:
        log("🧹 Shutting down...")
        with lock:
            for info in controller_threads.values():
                info["stop"].set()
    log("👋 Done.")
