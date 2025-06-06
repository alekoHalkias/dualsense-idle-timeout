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
        "stick_drift_threshold": "10",
        "ignore_idle_when_charging": "true"
    },
    "app": {
        "version": "1.2.0"
    }
}

def load_config():
    config = configparser.ConfigParser()
    config.read_dict(DEFAULTS)  # Load defaults first

    if os.path.exists(HOME_CONFIG):
        config.read(HOME_CONFIG)

    # Ensure all expected sections/keys are present
    for section in DEFAULTS:
        if not config.has_section(section):
            config.add_section(section)
        for key, value in DEFAULTS[section].items():
            if not config.has_option(section, key):
                config.set(section, key, value)

    return config