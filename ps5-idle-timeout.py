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

def main():
    script_path = os.path.abspath(__file__)

    # ✅ Process CLI args first
    if handle_cli_args(script_path):
        return  # Exit if a flag handled the request

    log("🔍 Starting DualSense idle monitor...", notify=True, summary="Starting")
    try:
        scan_loop()
    except KeyboardInterrupt:
        log("🧹 Shutting down...")
        shutdown_all_threads()
    log("👋 Done.", notify=True, summary="Closing process")

if __name__ == "__main__":
    main()
