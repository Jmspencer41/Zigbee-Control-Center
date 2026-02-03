import adafruit_dht
import board
import time
import threading

class TempHumidSensor(threading.Thread):
    def __init__(self, pin=board.D4, interval=30):
        super().__init__()
        self.sensor = adafruit_dht.DHT22(pin)
        self.pin = pin
        self.interval = interval
        self.temperature = None
        self.humidity = None
        self.running = False
        
    def read_temp_humid(self):
        try:
            temperature = self.sensor.temperature
            humidity = self.sensor.humidity
            if humidity is not None and temperature is not None:
                return temperature, humidity
            else:
                raise RuntimeError("Failed to retrieve data from DHT22")
        except RuntimeError as e:
            # DHT sensors can occasionally fail to read, this is normal
            raise e


    def run(self):
        self.running = True
        while self.running:
            try:
                self.temperature, self.humidity = self.read_temp_humid()
                print(f"Temperature: {self.temperature:.1f}°C, Humidity: {self.humidity:.1f}%")
            except RuntimeError as e:
                print(f"Error reading sensor: {e}")
            time.sleep(self.interval)

    def stop(self):
        self.running = False