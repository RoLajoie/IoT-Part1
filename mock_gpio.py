BCM = "BCM"
OUT = "OUT"
LOW = 0
HIGH = 1

def setwarnings(flag):
    pass

def setmode(mode):
    print(f"Mock: GPIO mode set to {mode}")

def setup(pin, mode):
    print(f"Mock: Setup GPIO pin {pin} as {mode}")

def output(pin, state):
    print(f"Mock: Set GPIO pin {pin} to {'HIGH' if state else 'LOW'}")

def cleanup():
    print("Mock: Cleanup GPIO resources")