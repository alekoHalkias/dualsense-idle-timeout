# PS5 DualSense Idle Timeout Monitor

A Linux utility that monitors connected DualSense controllers for idle input and disconnects them automatically when inactive.
Also reports battery levels using UPower.

## Features

- Disconnects controllers after configurable idle timeout
- Filters out stick drift and analog noise
- Reports battery percentage and charging status
- Sends desktop notifications via D-Bus (KDE/GNOME compatible)
- Can be run as a foreground process, background daemon, or systemd user service
- CLI tool with `--status`, `--daemon`, and `--version` options
- Configurable via `~/.config/ps5-idle-timeout/config.ini`

---

## Installation

Clone the repository and run the install script:

```bash
git clone https://github.com/alekohalkias/dualsense-idle-timeout.git
cd dualsense-idle-timeout
./install.sh


ps5-idle-timeout                # Run monitor in foreground
ps5-idle-timeout --daemon       # Launch in background (detached process)
ps5-idle-timeout --status       # List connected controllers and battery levels
ps5-idle-timeout --version      # Show installed version


requirements

evdev>=1.6.1
dbus-python>=1.2.18
