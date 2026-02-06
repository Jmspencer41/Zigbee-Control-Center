import RPi.GPIO as GPIO
import time
import threading

class TempHumidSensor(threading.Thread):
    def __init__(self, pin=4, interval=30):
        super().__init__()
        self.pin = pin
        self.interval = interval
        self.temperature = None
        self.humidity = None
        self.running = False
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
    def read_dht22(self):
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)
        time.sleep(0.02)
        GPIO.output(self.pin, GPIO.HIGH)
        time.sleep(0.00004)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Collect timing data
        unchanged_count = 0
        last = -1
        data = []
        while True:
            current = GPIO.input(self.pin)
            data.append(current)
            if last != current:
                unchanged_count = 0
                last = current
            else:
                unchanged_count += 1
                if unchanged_count > 255:
                    break
        
        # Parse the lengths of data pull up periods
        state = 1  # Start with HIGH
        lengths = []
        current_length = 0
        
        for current in data:
            current_length += 1
            if state != current:
                if state == 1:  # Was HIGH, collect length
                    lengths.append(current_length)
                state = current
                current_length = 0
        
        # Skip first pulse (start signal), then we have 40 data bits
        if len(lengths) < 41:
            return None, None
            
        bits = lengths[1:]
        the_bytes = []
        byte = 0
        
        for i in range(0, min(40, len(bits))):
            byte <<= 1
            if bits[i] > 30:  # Adjusted threshold - long pulse = 1
                byte |= 1
            if (i + 1) % 8 == 0:
                the_bytes.append(byte)
                byte = 0
        
        if len(the_bytes) != 5:
            return None, None
        
        # Verify checksum
        checksum = (the_bytes[0] + the_bytes[1] + the_bytes[2] + the_bytes[3]) & 0xFF
        if the_bytes[4] != checksum:
            return None, None
        
        # Calculate values
        humidity = ((the_bytes[0] << 8) + the_bytes[1]) / 10.0
        temperature = (((the_bytes[2] & 0x7F) << 8) + the_bytes[3]) / 10.0
        if the_bytes[2] & 0x80:
            temperature = -temperature
            
        return temperature, humidity

    def run(self):
        self.running = True
        while self.running:
            temp, humid = self.read_dht22()
            if temp is not None and humid is not None:
                self.temperature = temp
                self.humidity = humid
                print(f"Temperature: {self.temperature:.1f}°C, Humidity: {self.humidity:.1f}%")
            else:
                print("Failed to read sensor, retrying...")
            time.sleep(self.interval)

    def stop(self):
        self.running = False
        GPIO.cleanup()