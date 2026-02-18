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
    MEASURE_CMD = 0xFD  # High precision measurement
    SOFT_RESET_CMD = 0x89
    I2C_BUS = 1  # Raspberry Pi I2C bus number
    
    def __init__(self, interval):
        super().__init__()
        self.interval = interval
        self.running = True
        self.temperature = None
        self.humidity = None
        
        # TODO: Uncomment when running on Raspberry Pi
        # self.pi = pigpio.pi()
        # if not self.pi.connected:
        #     raise Exception("Failed to connect to pigpio daemon. Is pigpiod running?")
        # 
        # # Open I2C connection to sensor
        # try:
        #     self.handle = self.pi.i2c_open(self.I2C_BUS, self.ADDRESS)
        #     # Optional: Reset sensor on startup
        #     self.pi.i2c_write_byte(self.handle, self.SOFT_RESET_CMD)
        #     time.sleep(0.001)  # Wait 1ms after reset
        # except Exception as e:
        #     self.pi.stop()
        #     raise Exception(f"Failed to open I2C connection to SHT41: {e}")
    
    def _crc8(self, data):
        """Calculate CRC-8 checksum for SHT41 (polynomial 0x31)"""
        crc = 0xFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x31
                else:
                    crc = crc << 1
        return crc & 0xFF
    
    def _read_sensor(self):
        """Read temperature and humidity from SHT41 sensor"""
        # TODO: Uncomment when running on Raspberry Pi
        # try:
        #     # Send measurement command
        #     self.pi.i2c_write_byte(self.handle, self.MEASURE_CMD)
        #     
        #     # Wait for measurement to complete (high precision takes ~8.2ms)
        #     time.sleep(0.01)
        #     
        #     # Read 6 bytes: temp_msb, temp_lsb, temp_crc, hum_msb, hum_lsb, hum_crc
        #     (count, data) = self.pi.i2c_read_device(self.handle, 6)
        #     
        #     if count != 6:
        #         print("Error: Expected 6 bytes from sensor")
        #         return None, None
        #     
        #     # Verify CRC for temperature
        #     if self._crc8(data[0:2]) != data[2]:
        #         print("Temperature CRC error")
        #         return None, None
        #     
        #     # Verify CRC for humidity
        #     if self._crc8(data[3:5]) != data[5]:
        #         print("Humidity CRC error")
        #         return None, None
        #     
        #     # Convert temperature: T = -45 + 175 * (raw / 65535)
        #     temp_raw = (data[0] << 8) | data[1]
        #     temperature = -45 + 175 * (temp_raw / 65535.0)
        #     
        #     # Convert humidity: RH = -6 + 125 * (raw / 65535)
        #     hum_raw = (data[3] << 8) | data[4]
        #     humidity = -6 + 125 * (hum_raw / 65535.0)
        #     humidity = max(0, min(100, humidity))  # Clamp to 0-100%
        #     
        #     return temperature, humidity
        #     
        # except Exception as e:
        #     print(f"Error reading sensor: {e}")
        #     return None, None
        
        # Placeholder for development/testing
        return random.uniform(20, 50), random.uniform(10, 50)
    
    def run(self):
        """Main thread loop - continuously reads sensor and emits signals"""
        while self.running:
            temp, hum = self._read_sensor()
            
            if temp is not None and hum is not None:
                self.temperature = temp
                self.humidity = hum
                self.data_updated.emit(self.temperature, self.humidity)
                print(f"SHT41 Reading - Temp: {self.temperature:.1f}°C, Humidity: {self.humidity:.1f}%")
            else:
                print("Failed to read sensor data")
            
            time.sleep(self.interval)
    
    def stop(self):
        """Stop the sensor thread and cleanup resources"""
        print("Stopping SHT41 sensor...")
        self.running = False
        
        # TODO: Uncomment when running on Raspberry Pi
        # # Close I2C connection
        # if hasattr(self, 'handle'):
        #     try:
        #         self.pi.i2c_close(self.handle)
        #     except Exception as e:
        #         print(f"Error closing I2C handle: {e}")
        # 
        # # Disconnect from pigpio daemon
        # if hasattr(self, 'pi'):
        #     self.pi.stop()
        
        # Wait for thread to finish
        self.wait()
    
    def get_latest_reading(self):
        """Get the most recent temperature and humidity reading"""
        return self.temperature, self.humidity