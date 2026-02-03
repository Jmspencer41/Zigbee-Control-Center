import Adafruit_DHT # TODO: sudo pip3 install Adafruit_DHT (on raspberry pi)
import time
import threading

DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4  

class TempHumidSensor(threading.Thread):
    def __init__(self, sensor=DHT_SENSOR, pin=DHT_PIN, interval=30):
        super().__init__()
        self.sensor = sensor
        self.pin = pin
        self.interval = interval
        self.temperature = None
        self.humidity = None
        self.running = False
        
    def read_temp_humid(self):
        humidity, temperature = Adafruit_DHT.read_retry(self.sensor, self.pin)
        if humidity is not None and temperature is not None:
            return temperature, humidity
        else:
            raise RuntimeError("Failed to retrieve data from DHT22")


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