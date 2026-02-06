from Raspberry_pi_CC.sensors.dht22 import TempHumidSensor
# TODO: from Raspberry_pi_CC.sensors.ld2410c import LidarSensor 
# TODO: from Raspberry_pi_CC.sensors.camera import CameraSensor 

class deviceManager:
    def __init__(self):
        self.temperature = None
        self.humidity = None
        self.sensor_thread = TempHumidSensor(interval=30) # Read every 30 seconds
        self.sensor_thread.daemon = True
        self.sensor_thread.start()

    def get_temperature(self):
        print("THM: " + str(self.sensor_thread.temperature))
        return self.sensor_thread.temperature
    def get_humidity(self):
        print("THM: " + str(self.sensor_thread.humidity))
        return self.sensor_thread.humidity

    def stop(self):
        self.sensor_thread.stop()
