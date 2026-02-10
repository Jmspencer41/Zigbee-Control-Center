import time
import random
# TODO: import pigpio  # Uncomment when running on Raspberry Pi
from PyQt6.QtCore import QThread, pyqtSignal

class TempHumidSensor(QThread):


    # Signal that broadcasts temperature and humidity data
    # Any object can connect to this signal to receive updates
    data_updated = pyqtSignal(float, float)  # (temperature, humidity)

    # SHT41 I2C configuration
    ADDRESS = 0x44
    MEASURE_CMD = 0xFD
    I2C_BUS = 1  # Raspberry Pi I2C bus number

    def __init__(self, interval):
        super().__init__()
        self.interval = interval
        self.running = True
        self.temperature = None
        self.humidity = None

        #TODO: self.pi = pigpio.pi()  # Initialize pigpio on Raspberry Pi
        # if not self.pi.connected:
        #     raise Exception("Failed to connect to pigpio daemon. Is pigpiod running?")
        # Open I2C connection to sensor
        # try:
        #     self.handle = self.pi.i2c_open(self.I2C_BUS, self.ADDRESS)
        # except Exception as e:
        #     self.pi.stop()
        #     raise Exception(f"Failed to open I2C connection to SHT41: {e}")

    def run(self):

        ### TODO: Implement actual sensor reading logic here when running on Raspberry Pi ###

        while self.running:
            self.temperature = random.uniform(20, 50)  # Placeholder for actual sensor reading
            self.humidity = random.uniform(10, 50)    # Placeholder
            self.data_updated.emit(self.temperature, self.humidity)
            print(f"SHT41 Reading - Temp: {self.temperature:.1f}°C, Humidity: {self.humidity:.1f}%")
            time.sleep(self.interval)


    def stop(self):

        print("Stopping SHT41 sensor...")
        self.running = False
        
        ### TODO: Implement actual sensor shutdown and cleanup here when running on Raspberry Pi ###
        # # Close I2C connection
        # if hasattr(self, 'handle'):
        #     self.pi.i2c_close(self.handle)
        
        # # Disconnect from pigpio daemon
        # if hasattr(self, 'pi'):
        #     self.pi.stop()
        
        # Wait for thread to finish
        self.wait()