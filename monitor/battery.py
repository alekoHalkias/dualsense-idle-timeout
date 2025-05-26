
import subprocess 
from .macs import get_mac_for_device, get_dualsense_macs

def get_battery_level(mac):
    try:
        mac = mac.lower()
        devices = subprocess.run(["upower", "-e"], capture_output=True, text=True).stdout.splitlines()

        for device in devices:
            if "ps_controller_battery" in device:
                info = subprocess.run(["upower", "-i", device.strip()], capture_output=True, text=True).stdout

                found_mac = False
                battery = "Unknown"

                for line in info.splitlines():
                    line = line.strip()
                    if line.startswith("serial:"):
                        serial_mac = line.split(":", 1)[1].strip().lower()
                        if serial_mac == mac:
                            found_mac = True

                    if found_mac and line.startswith("percentage:"):
                        battery = line.split(":", 1)[1].strip()
                        return battery  # ✅ Done!

        return "Unknown"

    except Exception as e:
        print(f"⚠️ Battery check failed: {e}")
        return "Unknown"
