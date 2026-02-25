from PyQt6.QtCore import QObject
from Raspberry_pi_CC.sensors.sht41 import TempHumidSensor
# TODO: from Raspberry_pi_CC.sensors.ld2410c import LidarSensor 
# TODO: from Raspberry_pi_CC.sensors.camera import CameraSensor 

class deviceManager(QObject):
    def __init__(self):


        self.temperature = None
        self.humidity = None
        self.temp_humid_sensor = TempHumidSensor(interval=15) # Read every 15 seconds

        self.temp_humid_sensor.data_updated.connect(self.update_temp_humid) # Connect signal to update method
        self.temp_humid_sensor.start() # Start the sensor thread

        print("DeviceManager initialized - sensors started")


    def update_temp_humid(self, temp, humid):
    
        ### SLOT: This method is called automatically when the sensor emits data_updated.
        ### It runs in the main thread (Qt handles the thread switching).
        
        self.temperature = temp
        self.humidity = humid
        print(f"DeviceManager cached - Temp: {temp:.1f}°C, Humidity: {humid:.1f}%")

    def get_temperature(self):
        return self.temperature
    
    def get_humidity(self):
        return self.humidity
    
    def get_sensor(self):
        return self.temp_humid_sensor
    
    def stop(self):
        print("Stopping DeviceManager...")
        self.temp_humid_sensor.stop()
        # TODO: Stop other sensors when added
        print("DeviceManager stopped")
