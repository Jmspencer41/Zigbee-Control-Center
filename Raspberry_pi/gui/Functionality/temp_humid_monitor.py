# from Raspberry_pi.temp_humid import TempHumidSensor

# class tempHumidMonitor:
#     def __init__(self):
#         self.temperature = None
#         self.humidity = None
#         self.sensor_thread = TempHumidSensor(interval=30) # Read every 30 seconds
#         self.sensor_thread.daemon = True
#         self.sensor_thread.start()

#     def get_temperature(self):
#         return self.sensor_thread.temperature
#     def get_humidity(self):
#         return self.sensor_thread.humidity

#     def stop(self):
#         self.sensor_thread.stop()

import random
import time
import threading

# Mock sensor for testing on laptop
class MockTempHumidSensor(threading.Thread):
    def __init__(self, interval=30):
        super().__init__()
        self.interval = interval
        self.temperature = 22.0  # Start with reasonable values
        self.humidity = 45.0
        self.running = False
        self.daemon = True
        
    def run(self):
        self.running = True
        while self.running:
            # Simulate sensor readings with small random changes
            self.temperature = round(20 + random.uniform(-2, 5), 1)
            self.humidity = round(40 + random.uniform(-5, 15), 1)
            print(f"Mock Sensor - Temperature: {self.temperature:.1f}°C, Humidity: {self.humidity:.1f}%")
            time.sleep(self.interval)
    
    def stop(self):
        self.running = False

# Try to import real sensor, fall back to mock
try:
    from Raspberry_pi.temp_humid import TempHumidSensor
    USING_REAL_SENSOR = True
    print("Using real DHT22 sensor")
except ImportError:
    TempHumidSensor = MockTempHumidSensor
    USING_REAL_SENSOR = False
    print("Using mock sensor for testing")

class tempHumidMonitor:
    def __init__(self):
        self.temperature = None
        self.humidity = None
        self.sensor_thread = TempHumidSensor(interval=5)  # 5 seconds for testing (change back to 30 for real use)
        self.sensor_thread.daemon = True
        self.sensor_thread.start()

    def get_temperature(self):
        return self.sensor_thread.temperature
    
    def get_humidity(self):
        return self.sensor_thread.humidity

    def stop(self):
        self.sensor_thread.stop()