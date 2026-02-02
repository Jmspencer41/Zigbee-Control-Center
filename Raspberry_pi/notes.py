from Raspberry_pi.temp_humid import TempHumidSensor
import tkinter as tk
from threading import Thread

class TempHumidGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Temperature and Humidity Monitor")

        # Labels to display temperature and humidity
        self.temp_label = tk.Label(root, text="Temperature: -- °C", font=("Arial", 16))
        self.temp_label.pack(pady=10)

        self.humid_label = tk.Label(root, text="Humidity: -- %", font=("Arial", 16))
        self.humid_label.pack(pady=10)

        # Start button
        self.start_button = tk.Button(root, text="Start", command=self.start_sensor)
        self.start_button.pack(pady=10)

        # Stop button
        self.stop_button = tk.Button(root, text="Stop", command=self.stop_sensor, state=tk.DISABLED)
        self.stop_button.pack(pady=10)

        self.sensor_thread = None

    def start_sensor(self):
        self.sensor_thread = TempHumidSensor()
        self.sensor_thread.start()
        self.update_gui()
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

    def stop_sensor(self):
        if self.sensor_thread:
            self.sensor_thread.stop()
            self.sensor_thread.join()
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def update_gui(self):
        if self.sensor_thread and self.sensor_thread.running:
            if self.sensor_thread.temperature is not None and self.sensor_thread.humidity is not None:
                self.temp_label.config(text=f"Temperature: {self.sensor_thread.temperature:.1f} °C")
                self.humid_label.config(text=f"Humidity: {self.sensor_thread.humidity:.1f} %")
            self.root.after(1000, self.update_gui)  # Update every second

if __name__ == "__main__":
    root = tk.Tk()
    app = TempHumidGUI(root)
    root.mainloop()