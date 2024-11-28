import random
class DHT:
    def __init__(self, pin):
        print(f"Mock: DHT sensor initialized on pin {pin}")

    def readDHT11(self):
        return 0  # Simulate successful read

    def getTemperature(self):
        # Generate random temperature under 24 (fan not activated) | Still including random numbers helps visualize updates
        return round(random.uniform(20.0, 23.0), 1)
        
        # Generate random temperature
        # return round(random.uniform(20.0, 26.0), 1)

        # # Generate random temperature above 24 (fan always activated)
        # return round(random.uniform(25.0, 27.0), 1)

    def getHumidity(self):
        return round(random.uniform(30.0, 70.0), 1)  # Generate random humidity