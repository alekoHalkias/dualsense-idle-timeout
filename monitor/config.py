# monitor/config.py

import os
import configparser

CONFIG_PATH = os.path.expanduser("~/.config/ps5-idle-timeout/config.ini")

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
    if os.path.exists(CONFIG_PATH):
        config.read(CONFIG_PATH)
    return config
