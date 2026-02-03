from Raspberry_pi.temp_humid import TempHumidSensor

class tempHumidMonitor:
    def __init__(self):
        self.temperature = None
        self.humidity = None
        self.sensor_thread = TempHumidSensor(interval=30) # Read every 30 seconds
        self.sensor_thread.daemon = True
        self.sensor_thread.start()

    def get_temperature(self):
        return self.sensor_thread.temperature
    def get_humidity(self):
        return self.sensor_thread.humidity

    def stop(self):
        self.sensor_thread.stop()