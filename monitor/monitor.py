import os
import time
import subprocess
import threading
from evdev import InputDevice, list_devices, ecodes
from .battery import get_battery_level
from .notif import log
from .macs import get_dualsense_macs,get_mac_for_device,find_dualsense_event_devices

IDLE_TIMEOUT =  10     # seconds
RESCAN_INTERVAL = 2    # seconds
STICK_DRIFT_THRESHOLD = 10  # analog drift filter

controller_threads = {}
lock = threading.Lock()

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

    log(f"🛑 Finished monitoring {name}", notify=True,summary="Disconnected")


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
                    battery = get_battery_level(mac) if mac else "Unknown"
                    log(f"✅ Started monitoring {name} ({mac}) — Battery: {battery}", notify=True, summary="Controller Connected")

            # Cleanup dead threads
            to_remove = []
            for path, info in controller_threads.items():
                if not info["thread"].is_alive():
                    info["stop"].set()
                    to_remove.append(path)
            for path in to_remove:
                del controller_threads[path]

        time.sleep(RESCAN_INTERVAL)

def shutdown_all_threads():
    with lock:
        for info in controller_threads.values():
            info["stop"].set()