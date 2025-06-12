import os
import time
import subprocess
import threading
from evdev import InputDevice, list_devices, ecodes
from .notif import log
from .macs import get_dualsense_macs, get_mac_for_device, find_dualsense_event_devices
from .config import load_config
from monitor.dbus_api import run_dbus_loop
from .battery import get_battery_level, is_charging

_config = load_config()
RESCAN_INTERVAL = int(_config["monitor"]["rescan_interval"])
STICK_DRIFT_THRESHOLD = int(_config["monitor"]["stick_drift_threshold"])

controller_threads = {}
lock = threading.Lock()
last_input_times = {}
last_charging_log = {}

# Battery info cache to avoid repeated D-Bus calls
_battery_cache = {}

def get_idle_timeout():
    return int(load_config()["monitor"]["idle_timeout"])

def get_cached_battery_info(mac, ttl=10):
    now = time.time()
    entry = _battery_cache.get(mac)
    if entry and now - entry['time'] < ttl:
        return entry['battery'], entry['charging']

    battery = get_battery_level(mac)
    charging = is_charging(mac)
    _battery_cache[mac] = {"time": now, "battery": battery, "charging": charging}
    return battery, charging

def monitor_controller(dev_path, name, mac, stop_event):
    try:
        dev = InputDevice(dev_path)
        log(f"🔹 Monitoring {name} ({mac}) at {dev_path}")
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

                if event.code in (ecodes.ABS_HAT0X, ecodes.ABS_HAT0Y) and event.value != 0:
                    last_input = time.time()
                    last_input_times[dev_path] = last_input
                    disconnected = False

                if delta > STICK_DRIFT_THRESHOLD:
                    last_input = time.time()
                    last_input_times[dev_path] = last_input
                    disconnected = False

            elif event.type == ecodes.EV_KEY:
                last_input = time.time()
                last_input_times[dev_path] = last_input
                disconnected = False

            if not disconnected and time.time() - last_input > get_idle_timeout():
                if mac:
                    battery, charging = get_cached_battery_info(mac)
                    prev_charging = last_charging_log.get(dev_path)

                    if prev_charging is not None and charging != prev_charging:
                        if charging:
                            log(f"⚡ {name} is now charging — skipping idle disconnect")
                        else:
                            log(f"🔋 {name} is no longer charging — resetting idle timer")
                            last_input = time.time()
                            last_input_times[dev_path] = last_input

                    last_charging_log[dev_path] = charging

                    if charging and _config["monitor"].getboolean("ignore_idle_when_charging"):
                        continue

                    log(f"⚠️ {name} is idle, disconnecting {mac}")
                    result = subprocess.run(
                        ["bluetoothctl", "disconnect", mac],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )

                    if result.returncode == 0:
                        log(f"🔌 Disconnected {name} ({mac})", notify=True, summary="Disconnected")
                    else:
                        log(f"⚠️ Failed to disconnect {name} ({mac}) (exit code {result.returncode})", notify=True, summary="Disconnect Failed")

                    disconnected = True
                    return
                else:
                    log(f"⚠️ {name} idle but no MAC found — can't disconnect")

    except OSError:
        if not disconnected:
            log(f"🔌 Device {name} disconnected unexpectedly")

    log(f"🚑 Finished monitoring {name}", notify=True, summary="Disconnected")

def scan_loop():
    threading.Thread(target=run_dbus_loop, args=(collect_status,), daemon=True).start()
    while True:
        macs = get_dualsense_macs()
        devices = find_dualsense_event_devices()

        with lock:
            for path, name, mac in devices:
                if path not in controller_threads:
                    existing_players = {info["player"] for info in controller_threads.values()}
                    player_number = 1
                    while player_number in existing_players:
                        player_number += 1

                    stop_event = threading.Event()
                    t = threading.Thread(target=monitor_controller, args=(path, name, mac, stop_event), daemon=True)
                    controller_threads[path] = {
                        "thread": t,
                        "stop": stop_event,
                        "mac": mac,
                        "name": name,
                        "player": player_number
                    }
                    t.start()
                    if mac:
                        subprocess.run(["bluetoothctl", "trust", mac], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    battery, _ = get_cached_battery_info(mac) if mac else ("Unknown", False)
                    log(f"✅ Player {player_number}: Monitoring {name} ({mac}) — Battery: {battery}", notify=True, summary="Controller Connected")

            to_remove = []
            for path, info in controller_threads.items():
                if not info["thread"].is_alive():
                    to_remove.append(path)

            for path in to_remove:
                del controller_threads[path]

            for i, (path, info) in enumerate(sorted(controller_threads.items()), start=1):
                info["player"] = i

        time.sleep(RESCAN_INTERVAL)

def collect_status():
    now = time.time()
    status = {}
    timeout = get_idle_timeout()
    for path, info in controller_threads.items():
        mac = info.get("mac", "unknown")
        name = info.get("name", "Unknown Controller")
        battery, charging = get_cached_battery_info(mac) if mac else ("Unknown", False)
        last = last_input_times.get(path, now)
        idle = max(0, timeout - (now - last))
        idle = min(timeout, idle)  # Clamp to valid range
        status[path] = {
            "mac": mac,
            "name": name,
            "player": info.get("player", "?"),
            "battery": battery,
            "charging": charging,
            "idle_remaining": round(idle, 1)
        }
    return status

def shutdown_all_threads():
    with lock:
        for info in controller_threads.values():
            info["stop"].set()
