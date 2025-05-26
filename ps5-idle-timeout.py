#!/usr/bin/env python3

import os
import sys
import time
import argparse
import subprocess

from monitor.battery import get_battery_level
from monitor.notif import log
from monitor.monitor import scan_loop, shutdown_all_threads
from monitor.macs import find_dualsense_event_devices
from monitor.config import load_config
from monitor.cli import handle_cli_args

config = load_config()

def running_under_systemd():
    return os.environ.get("INVOCATION_ID") is not None

def main():
    # parser = argparse.ArgumentParser(description="DualSense idle timeout monitor & battery checker")
    # parser.add_argument("--status", action="store_true", help="Show connected controller battery + MACs")
    # parser.add_argument("--version", action="store_true", help="Print version and exit")
    # parser.add_argument("--daemon", action="store_true", help="Run monitor in background (detached)")

    # args = parser.parse_args()

    # if args.version:
    #     print(f"ps5-idle-timeout version {config['app']['version']}")
    #     return

    # if args.status:
    #     print("🎮 Controller Status\n")
    #     for path, name, mac in find_dualsense_event_devices():
    #         battery = get_battery_level(mac) if mac else "Unknown"
    #         print(f"• {name} ({mac or 'no MAC'}) — Battery: {battery}")
    #     return

    # if args.daemon:
    #     if running_under_systemd():
    #         print("⚠️  Refusing to daemonize: already running under systemd.")
    #         return

    #     log("🔧 Starting in daemon mode...", summary="Daemon")
    #     subprocess.Popen(
    #         [sys.executable, os.path.abspath(__file__)],
    #         stdout=subprocess.DEVNULL,
    #         stderr=subprocess.DEVNULL,
    #         stdin=subprocess.DEVNULL,
    #         close_fds=True,
    #         start_new_session=True
    #     )
    #     return

    # Default: foreground daemon
    log("🔍 Starting DualSense idle monitor...", notify=True, summary="Starting")
    try:
        scan_loop()
    except KeyboardInterrupt:
        log("🧹 Shutting down...")
        shutdown_all_threads()
    log("👋 Done.", notify=True, summary="Closing process")

if __name__ == "__main__":
    main()
