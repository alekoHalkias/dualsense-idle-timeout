# monitor/cli.py

import os
import sys
import time
import subprocess
import argparse

from monitor.battery import get_battery_level
from monitor.notif import log
from monitor.monitor import scan_loop, shutdown_all_threads
from monitor.macs import find_dualsense_event_devices
from monitor.config import load_config

config = load_config()
PID_FILE = os.path.expanduser("~/.cache/ps5-idle-timeout.pid")

def handle_cli_args(script_path):
    parser = argparse.ArgumentParser(description="DualSense idle timeout monitor & battery checker")
    parser.add_argument("--status", action="store_true", help="Show connected controller battery + MACs")
    parser.add_argument("--version", action="store_true", help="Print version and exit")
    parser.add_argument("--daemon", action="store_true", help="Run monitor in background (detached)")
    parser.add_argument("--stop", action="store_true", help="Stop the background daemon")
    parser.add_argument("--restart", action="store_true", help="Restart the script to reload config")
    args = parser.parse_args()

    if args.version:
        print(f"ps5-idle-timeout version {config['app']['version']}")
        return True

    if args.status:
        print("🎮 Controller Status\n")
        idle_data = get_idle_times()
        for path, name, mac in find_dualsense_event_devices():
            battery = get_battery_level(mac) if mac else "Unknown"
            idle_str = ""
            if path in idle_data:
                idle = idle_data[path]["idle_for"]
                idle_str = f"— Idle: {idle:.1f}s"
            print(f"• {name} ({mac or 'no MAC'}) — Battery: {battery} {idle_str}")
        return True

    if args.daemon:
        log("🔧 Starting in daemon mode...", summary="Daemon")
        proc = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            close_fds=True,
            start_new_session=True
        )
        with open(PID_FILE, "w") as f:
            f.write(str(proc.pid))
        return True

    if args.stop:
        if os.path.exists(PID_FILE):
            with open(PID_FILE) as f:
                try:
                    pid = int(f.read().strip())
                    os.kill(pid, 15)  # SIGTERM
                    log(f"🛑 Sent SIGTERM to daemon (pid {pid})", notify=True, summary="Stopped")
                    os.remove(PID_FILE)
                except Exception as e:
                    log(f"⚠️ Failed to stop daemon: {e}")
        else:
            log("⚠️ No PID file found — is the daemon running?")
        return True

    if args.restart:
        log("🔁 Restarting script manually...", summary="Restart")
        shutdown_all_threads()
        time.sleep(0.5)
        subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            close_fds=True,
            start_new_session=True
        )
        return True

    return False  # no flags matched — run main loop
