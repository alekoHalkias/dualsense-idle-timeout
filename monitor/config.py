# monitor/config.py

import os
import configparser


HOME_CONFIG = os.path.expanduser("~/.config/ps5-idle-timeout/config.ini")
SCRIPT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FALLBACK_CONFIG = os.path.join(SCRIPT_DIR, "config.ini")
# Defaults if config file is missing or incomplete
DEFAULTS = {
    "monitor": {
        "idle_timeout": "60",
        "rescan_interval": "2",
        "stick_drift_threshold": "10"
    },
    "app": {
        "version": "1.0.0"
    }
}

def load_config():
    config = configparser.ConfigParser()
    config.read_dict(DEFAULTS)

    if os.path.exists(HOME_CONFIG):
        config.read(HOME_CONFIG)
    elif os.path.exists(FALLBACK_CONFIG):
        config.read(FALLBACK_CONFIG)

    return config