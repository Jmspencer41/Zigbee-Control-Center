'''
LD2410C Presence Sensor Interface

Not implemented yet for this build.
'''

import pigpio
import time

class LD2410C:
    def __init__(self, gpio_pin, baud_rate=115200): #TODO: define which GPIO pin to use for serial communication
        self.pi = pigpio.pi()
        self.gpio_pin = gpio_pin
        self.baud_rate = baud_rate
        self.light_on = False
        
        # Open serial connection
        self.serial = self.pi.serial_open("/dev/ttyAMA0", self.baud_rate)
    
    def read_sensor(self):
        try:
            count, data = self.pi.serial_read(self.serial, 32)
            if count > 0:
                # Parse sensor data and update light_on
                self._parse_data(data)
        except Exception as e:
            print(f"Error reading sensor: {e}")
    
    def _parse_data(self, data):
        # LD2410C returns presence detection in specific byte positions
        # Adjust based on your sensor's protocol
        if len(data) >= 5:
            # Typically byte 4-5 contains presence info
            presence_byte = data[4]
            self.light_on = bool(presence_byte & 0x01)  # Check if presence detected
    
    def cleanup(self):
        # Clean up pigpio resources
        self.pi.serial_close(self.serial)
        self.pi.stop()

# Usage example
if __name__ == "__main__":
    sensor = LD2410C("/dev/ttyAMA0")
    
    try:
        while True:
            sensor.read_sensor()
            print(f"Light on: {sensor.light_on}")
            time.sleep(0.5)
    finally:
        sensor.cleanup()