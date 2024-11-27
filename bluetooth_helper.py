# sudo apt install bluez bluez-tools

import subprocess  
import time
class BluetoothHelper:
    def __init__(self):
        self.devices_seen = set()
        self.bluetooth_devices = []  

    def start_continuous_scan(self):
        try:
            process = subprocess.Popen(
                ["bluetoothctl"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Start scanning
            process.stdin.write("scan on\n")
            process.stdin.flush()

            print("Scanning for Bluetooth devices. Press Ctrl+C to stop.")
            while True:
                output = process.stdout.readline().strip()
                if "Device" in output:
                    self.process_device_line(output)

        except KeyboardInterrupt:
            print("\nStopping scan...")
            process.stdin.write("scan off\n")
            process.stdin.flush()
            process.terminate()

    def process_device_line(self, line):
        """Processes a single line of Bluetoothctl output to extract device info."""
        parts = line.split("Device")[1].strip().split(" ", 1)
        address = parts[0]
        name = parts[1] if len(parts) > 1 else "Unknown Device"

        if address not in self.devices_seen:
            self.devices_seen.add(address)
            self.bluetooth_devices.append({'name': name, 'address': address})  
            print(f"Discovered: Name: {name}, Address: {address}")

    def get_bluetooth_devices(self):
        """Returns the list of discovered Bluetooth devices."""
        return self.bluetooth_devices
