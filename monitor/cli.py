# monitor/cli.py

import os
import sys
import time
import subprocess
import argparse
import socket
import json

from monitor.battery import get_battery_level
from monitor.notif import log
from monitor.monitor import scan_loop, shutdown_all_threads
from monitor.macs import find_dualsense_event_devices
from monitor.config import load_config
from configparser import ConfigParser
from monitor.config import HOME_CONFIG

config = load_config()
PID_FILE = os.path.expanduser("~/.cache/ps5-idle-timeout.pid")

def handle_cli_args(script_path):
    parser = argparse.ArgumentParser(description="DualSense idle timeout monitor & battery checker")
    parser.add_argument("-s","--status", action="store_true", help="Show connected controller battery + MACs")
    parser.add_argument("-v","--version", action="store_true", help="Print version and exit")
    parser.add_argument("-d","--daemon", action="store_true", help="Run monitor in background (detached)")
    parser.add_argument("-x","--stop", action="store_true", help="Stop the background daemon")
    parser.add_argument("-r","--restart", action="store_true", help="Restart the script to reload config")
    parser.add_argument("-t","--set-timeout", type=int, help="Set new idle timeout value (in seconds)")
    parser.add_argument("-n","--notify-now", action="store_true", help="Send a desktop notification with current controller status")

    args = parser.parse_args()

    if args.version:
        print(f"ps5-idle-timeout version {config['app']['version']}")
        return True

    if args.status:
        try:
            import dbus
            bus = dbus.SessionBus()
            remote = bus.get_object("org.dualsense.Monitor", "/org/dualsense/Monitor")
            iface = dbus.Interface(remote, "org.dualsense.Monitor")
            data = json.loads(iface.GetStatus())
        except Exception as e:
            log(f"⚠️ Could not query D-Bus status: {e}")
            data = {}

        print("🎮 Controller Status\n")
        monitor_cfg = config["monitor"]
        print(
            f"🛠️  Config — idle_timeout: {monitor_cfg['idle_timeout']}s, "
            f"rescan_interval: {monitor_cfg['rescan_interval']}s, "
            f"drift_threshold: {monitor_cfg['stick_drift_threshold']}\n"
        )

        for path, info in data.items():
            battery = info.get("battery", "Unknown")
            charging = info.get("charging", False)
            idle = info.get("idle_for", 0)
            timeout = int(config["monitor"]["idle_timeout"])

            if charging:
                status_line = f"⚡ Charging — idle timer paused"
            else:
                remaining = max(0, timeout - idle)
                status_line = f"Idle timeout in: {remaining:.1f}s"

            print(f"• {info['name']} ({info['mac']}) — Battery: {battery} — {status_line}")

        return True

    if args.daemon:
        if os.path.exists(PID_FILE):
            try:
                with open(PID_FILE) as f:
                    existing_pid = int(f.read().strip())
                # Check if process is still running
                os.kill(existing_pid, 0)
                log(f"⚠️ Daemon already running (PID {existing_pid})", notify=True, summary="Already Running")
                return True
            except (ValueError, ProcessLookupError, PermissionError):
                # PID file exists but process is not alive — continue to spawn new one
                os.remove(PID_FILE)

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

    if args.set_timeout is not None:
        new_config = ConfigParser()
        if os.path.exists(HOME_CONFIG):
                config.read(HOME_CONFIG)
        else:
                os.makedirs(os.path.dirname(HOME_CONFIG), exist_ok=True)

        if not config.has_section("monitor"):
                config.add_section("monitor")
        config.set("monitor", "idle_timeout", str(args.set_timeout))
        with open(HOME_CONFIG, "w") as f:
                config.write(f)

        log(f"✅ idle_timeout set to {args.set_timeout}s", notify=True, summary="Config Updated")
        return True
    
    if args.notify_now:
        try:
            import dbus
            bus = dbus.SessionBus()
            remote = bus.get_object("org.dualsense.Monitor", "/org/dualsense/Monitor")
            iface = dbus.Interface(remote, "org.dualsense.Monitor")
            iface.SendStatusToast()
        except Exception as e:
            log(f"⚠️ Could not send status toast: {e}")
        return True

    return False  # no flags matched — run main loop
