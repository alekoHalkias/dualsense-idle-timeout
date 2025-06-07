import os
import time
import subprocess
import threading
from evdev import InputDevice, list_devices, ecodes
from .battery import get_battery_level,is_charging
from .notif import log
from .macs import get_dualsense_macs,get_mac_for_device,find_dualsense_event_devices
from .config import load_config
from monitor.dbus_api import run_dbus_loop

_config = load_config()
IDLE_TIMEOUT = int(_config["monitor"]["idle_timeout"])
RESCAN_INTERVAL = int(_config["monitor"]["rescan_interval"])
STICK_DRIFT_THRESHOLD = int(_config["monitor"]["stick_drift_threshold"])

controller_threads = {}
lock = threading.Lock()
last_input_times = {}
last_charging_log = {}

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

    last_input_times[dev_path] = last_input

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
                    last_input_times[dev_path] = last_input  # ✅ critical for status
                    disconnected = False

            elif event.type == ecodes.EV_KEY:
                last_input = time.time()
                last_input_times[dev_path] = last_input  # ✅ update on keypress
                disconnected = False

            if not disconnected and time.time() - last_input > IDLE_TIMEOUT:
                if mac:
                    charging = is_charging(mac)
                    prev_charging = last_charging_log.get(dev_path)

                    if charging != prev_charging:
                        if charging:
                            log(f"⚡ {name} is now charging — skipping idle disconnect")
                        else:
                            log(f"🔋 {name} is no longer charging — idle timer active")
                        last_charging_log[dev_path] = charging

                    if charging and _config["monitor"].getboolean("ignore_idle_when_charging"):
                        continue
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
    # start_socket_server()
    threading.Thread(target=run_dbus_loop, args=(collect_status,), daemon=True).start()
    while True:
        macs = get_dualsense_macs()
        devices = find_dualsense_event_devices()

        with lock:
            for path, name, mac in devices:
                if path not in controller_threads:
                    player_number = len(controller_threads) + 1 
                    stop_event = threading.Event()
                    t = threading.Thread(target=monitor_controller, args=(path, name, mac, stop_event), daemon=True)
                    controller_threads[path] = {
                        "thread": t,
                        "stop": stop_event,
                        "mac": mac,
                        "name": name,
                        "player":player_number
                    }
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

def collect_status():
    now = time.time()
    status = {}
    for path, info in controller_threads.items():
        mac = info.get("mac", "unknown")
        name = info.get("name", "Unknown Controller")
        battery = get_battery_level(mac) if mac else "Unknown"
        charging = is_charging(mac) if mac else False
        last = last_input_times.get(path, now)
        idle = now - last
        status[path] = {
            "mac": mac,
            "name": name,
            "player": info.get("player", "?"),
            "battery": battery,
            "charging": charging,
            "idle_for": round(idle, 1)
        }
    return status

def shutdown_all_threads():
    with lock:
        for info in controller_threads.values():
            info["stop"].set()