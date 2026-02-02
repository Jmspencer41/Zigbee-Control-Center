from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton)
from PyQt6.QtGui import QFont

class EnvironmentLayout(QVBoxLayout):
    def __init__(self):
        super().__init__()
        
        envi_area_widget = QWidget()
        envi_area_widget.setStyleSheet("background-color: #89c2fa; border-radius: 15px;")  
        envi_area_layout = QVBoxLayout()
        envi_area_widget.setLayout(envi_area_layout)
        
        ### TOP HALF: Temperature & Humidity ###
        temp_humid_layout = QHBoxLayout()
        temp_humid_layout.setSpacing(20)
        
        # Temperature side
        temp_layout = QVBoxLayout()
        
        temp_layout.addStretch() ## Maybe?

        temp_label_title = QLabel("Temperature")
        temp_label_title.setFont(QFont('Arial', 20, QFont.Weight.Bold))
        temp_label_title.setStyleSheet("color: #2c3e50;")
        temp_layout.addWidget(temp_label_title)
        
        temp = 22  # Placeholder
        temp_label = QLabel(f"{temp}°C")
        temp_label.setFont(QFont('Arial', 24))
        temp_label.setStyleSheet("color: #2c3e50;")
        temp_layout.addWidget(temp_label)
        
        temp_layout.addStretch() ## Maybe?
        
        temp_humid_layout.addLayout(temp_layout)
        
        # Humidity side
        humid_layout = QVBoxLayout()
        humid_label_title = QLabel("Humidity")
        humid_label_title.setFont(QFont('Arial', 20, QFont.Weight.Bold))
        humid_label_title.setStyleSheet("color: #2c3e50;")
        humid_layout.addWidget(humid_label_title)
        
        humid = 45  # Placeholder
        humid_label = QLabel(f"{humid}%")
        humid_label.setFont(QFont('Arial', 24))
        humid_label.setStyleSheet("color: #2c3e50;")
        humid_layout.addWidget(humid_label)
        
        temp_humid_layout.addLayout(humid_layout)
        
        # Add temp/humid to main layout
        envi_area_layout.addLayout(temp_humid_layout)
        envi_area_layout.setStretch(0, 1)  # Top half gets 50%
        
        ### BOTTOM HALF: Lights Button ###
        Lights_button = QPushButton('Toggle Lights')
        Lights_button.setMinimumHeight(80)
        Lights_button.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        Lights_button.setStyleSheet("""
            QPushButton {
                background-color: #f1c40f;
                color: #2c3e50;
                border-radius: 30px;
                padding: 15px;
            }
            QPushButton:pressed {
                background-color: #b7950b;
            }
        """)
        envi_area_layout.addWidget(Lights_button)
        envi_area_layout.setStretch(1, 1)  # Bottom half gets 50%
        
        # Add the whole thing to self
        self.addWidget(envi_area_widget)