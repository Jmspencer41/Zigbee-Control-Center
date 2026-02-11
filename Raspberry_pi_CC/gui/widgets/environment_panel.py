import os

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton)
from PyQt6.QtGui import (QFont, QIcon)
from PyQt6.QtCore import (Qt, QSize)

class EnvironmentLayout(QVBoxLayout):
    def __init__(self, sensor, screen_height):
        super().__init__()

        self.sensor = sensor  # Store reference to the sensor

        font = QFont('Arial', int(screen_height * 0.04), QFont.Weight.Bold)
        
        # SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

        envi_area_widget = QWidget()
        envi_area_widget.setStyleSheet("background-color: #99ddff; border-radius: 15px;")  
        envi_area_layout = QVBoxLayout()
        envi_area_widget.setLayout(envi_area_layout)
        
        ### TOP HALF: Temperature & Humidity ###
        temp_humid_layout = QHBoxLayout()
        temp_humid_layout.setSpacing(20)
        
        temp_layout = QVBoxLayout()
        temp_layout.addStretch()
        
        temp_label_title = QLabel("Temperature")
        temp_label_title.setFont(font)
        temp_label_title.setStyleSheet("color: #2c3e50;")
        temp_label_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        temp_layout.addWidget(temp_label_title)


        temp_label = QLabel("---°C")
        temp_label.setFont(font)
        temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        border_radius = int(screen_height * 0.05)
        padding = int(screen_height * 0.02)
        min_size = int(screen_height * 0.10)
        temp_label.setStyleSheet(f"""
            color: white;
            background-color: #e74c3c;
            border-radius: {border_radius}px;
            padding: {padding}px;
            min-width: {min_size}px;
            min-height: {min_size}px;
            border: 2px solid rgba(0, 0, 0, 0.2);
        """)
        temp_layout.addWidget(temp_label)
        temp_layout.addStretch()
        
        temp_humid_layout.addLayout(temp_layout)
        
        humid_layout = QVBoxLayout()
        humid_layout.addStretch()
        
        humid_label_title = QLabel("Humidity")
        humid_label_title.setFont(font)
        humid_label_title.setStyleSheet("color: #2c3e50;")
        humid_label_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        humid_layout.addWidget(humid_label_title)
        
        humid_label = QLabel("---%")
        humid_label.setFont(font)
        humid_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        humid_label.setStyleSheet(f"""
            color: white;
            background-color: #3498db;
            border-radius: {border_radius}px;
            padding: {padding}px;
            min-width: {min_size}px;
            min-height: {min_size}px;
            border: 2px solid rgba(0, 0, 0, 0.2);
        """)
        humid_layout.addWidget(humid_label)
        humid_layout.addStretch()

        # Store reference for updates later
        self.temp_label = temp_label
        self.humid_label = humid_label
        
        temp_humid_layout.addLayout(humid_layout)
        
        # Add temp/humid to main layout
        envi_area_layout.addLayout(temp_humid_layout)
        envi_area_layout.setStretch(0, 1)  # Top half gets 50%
        
        ### BOTTOM HALF: Lights Button ###
        Lights_button = QPushButton()
        
        ### TODO: Dynamically set icon and style based on actual light status from device manager when implemented ###
        # icon_path = os.path.join(SCRIPT_DIR, 'icons', 'light_on.png')
        # if os.path.exists(icon_path):

        icon_size = QSize(int(screen_height * 0.12), int(screen_height * 0.12))
        Lights_button.setIcon(QIcon('styles/icons/light_on.png')) # TODO: WHY ICON NO WORK!
        Lights_button.setIconSize(icon_size)

        # TODO: Check actual light status
        light_is_on = True
        light_button_BR = int(screen_height * 0.10)
        light_button_size = int(screen_height * 0.25)

        if light_is_on:
            Lights_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #f1c40f;
                color: #2c3e50;
                border-radius: {light_button_BR}px;
                min-width: {light_button_size}px;
                min-height: {light_button_size}px;
                border: 2px solid rgba(0, 0, 0, 0.2);                        
            }}
            QPushButton:pressed {{
                background-color: #b7950b;
            }}
        """)        
        else:
            Lights_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #00004d;
                color: #2c3e50;
                border-radius: {light_button_BR}px;
                min-width: {light_button_size}px;
                min-height: {light_button_size}px;
            }}
            QPushButton:pressed {{
                background-color: #b7950b;
            }}
        """)
        envi_area_layout.addWidget(Lights_button, alignment=Qt.AlignmentFlag.AlignCenter)
        envi_area_layout.setStretch(1, 1)  # Bottom half gets 50%

        ### === THE CRITICAL CONNECTION === ###
        # Connect the sensor's data_updated signal to our update method
        # When the sensor emits new data, update_sensor_values will be called automatically
        self.sensor.data_updated.connect(self.update_sensor_values)
        
        print("EnvironmentPanel connected to sensor signals")
    
        self.addWidget(envi_area_widget)

    def update_sensor_values(self, temp, humid):
        
        if temp is not None:
            self.temp_label.setText(f"{temp:.1f}°C")
        if humid is not None:
            self.humid_label.setText(f"{humid:.1f}%")
