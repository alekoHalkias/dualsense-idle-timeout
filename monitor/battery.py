
import subprocess 
from .macs import get_mac_for_device, get_dualsense_macs

def normalize_mac(mac):
    return mac.strip().lower().replace("-", ":")


def get_battery_level(mac):
    try:
        mac = normalize_mac(mac)
        devices = subprocess.run(["upower", "-e"], capture_output=True, text=True).stdout.splitlines()

        for device in devices:
            if "ps_controller_battery" in device:
                info = subprocess.run(["upower", "-i", device.strip()], capture_output=True, text=True).stdout

                found_mac = False
                battery = "Unknown"

                for line in info.splitlines():
                    line = line.strip()
                    if line.startswith("serial:"):
                        serial_mac = normalize_mac(line.split(":", 1)[1])
                        if serial_mac == mac:
                            found_mac = True

                    if found_mac and line.startswith("percentage:"):
                        battery = line.split(":", 1)[1].strip()
                        return battery
        return "Unknown"
    except Exception as e:
        print(f"⚠️ Battery check failed: {e}")
        return "Unknown"

def is_charging(mac):
    try:
        mac = normalize_mac(mac)
        devices = subprocess.run(["upower", "-e"], capture_output=True, text=True).stdout.splitlines()

        for device in devices:
            if "ps_controller_battery" in device:
                info = subprocess.run(["upower", "-i", device.strip()], capture_output=True, text=True).stdout

                found_mac = False
                for line in info.splitlines():
                    line = line.strip()
                    if line.startswith("serial:"):
                        serial_mac = normalize_mac(line.split(":", 1)[1])
                        if serial_mac == mac:
                            found_mac = True
                    if found_mac:
                        if line.startswith("icon-name:"):
                            icon = line.split(":", 1)[1].strip().lower()
                            if "charging" in icon or "charged" in icon:
                                return True
                        elif "History (charge):" in line:
                            return "charging" in line.lower()

        return False
    except Exception as e:
        print(f"⚠️ Charging check failed: {e}")
        return False