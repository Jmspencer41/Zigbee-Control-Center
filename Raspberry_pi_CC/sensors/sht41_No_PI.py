import time
import random
from PyQt6.QtCore import QThread, pyqtSignal

class TempHumidSensor(QThread):


    # Signal that broadcasts temperature and humidity data
    # Any object can connect to this signal to receive updates
    data_updated = pyqtSignal(float, float)  # (temperature, humidity)

    def __init__(self, interval):
        super().__init__()
        self.interval = interval
        self.running = True
        self.temperature = None
        self.humidity = None

    def run(self):

        while self.running:
            self.temperature = random.uniform(20, 50)  # Placeholder for actual sensor reading
            self.humidity = random.uniform(10, 50)     # Placeholder for actual sensor reading
            self.data_updated.emit(self.temperature, self.humidity)
            print(f"SHT41 Reading - Temp: {self.temperature:.1f}°C, Humidity: {self.humidity:.1f}%")
            time.sleep(self.interval)

    def stop(self):

        print("Stopping SHT41 sensor...")
        self.running = False
        
        # Wait for thread to finish
        self.wait()
