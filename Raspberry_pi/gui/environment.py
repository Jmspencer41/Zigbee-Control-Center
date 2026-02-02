from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton)
from PyQt6.QtGui import (QFont, QIcon)
from PyQt6.QtCore import (Qt, QSize)

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
        temp_layout.addStretch()
        
        temp_label_title = QLabel("Temperature")
        temp_label_title.setFont(QFont('Arial', 20, QFont.Weight.Bold))
        temp_label_title.setStyleSheet("color: #2c3e50;")
        temp_label_title.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center horizontally
        temp_layout.addWidget(temp_label_title)
        
        temp = 22  # Placeholder
        temp_label = QLabel(f"{temp}°C")
        temp_label.setFont(QFont('Arial', 24))
        temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center horizontally
        temp_label.setStyleSheet("""
            color: white;
            background-color: #e74c3c;
            border-radius: 50px;
            padding: 20px;
            min-width: 100px;
            min-height: 100px;
        """)
        temp_layout.addWidget(temp_label)
        temp_layout.addStretch()
        
        temp_humid_layout.addLayout(temp_layout)
        
        # Humidity side
        humid_layout = QVBoxLayout()
        humid_layout.addStretch()
        
        humid_label_title = QLabel("Humidity")
        humid_label_title.setFont(QFont('Arial', 20, QFont.Weight.Bold))
        humid_label_title.setStyleSheet("color: #2c3e50;")
        humid_label_title.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center horizontally
        humid_layout.addWidget(humid_label_title)
        
        humid = 45  # Placeholder
        humid_label = QLabel(f"{humid}%")
        humid_label.setFont(QFont('Arial', 24))
        humid_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center horizontally
        humid_label.setStyleSheet("""
            color: white;
            background-color: #3498db;
            border-radius: 50px;
            padding: 20px;
            min-width: 100px;
            min-height: 100px;
        """)
        humid_layout.addWidget(humid_label)
        humid_layout.addStretch()
        
        temp_humid_layout.addLayout(humid_layout)
        
        # Add temp/humid to main layout
        envi_area_layout.addLayout(temp_humid_layout)
        envi_area_layout.setStretch(0, 1)  # Top half gets 50%
        
        ### BOTTOM HALF: Lights Button ###
        Lights_button = QPushButton()
        Lights_button.setIcon(QIcon('images/light_on.png'))  # Set the icon
        Lights_button.setIconSize(QSize(80, 80))
        Lights_button.setFont(QFont('Arial', 20))  # Large emoji
        Lights_button.setStyleSheet("""
            QPushButton {
                background-color: #f1c40f;
                color: #2c3e50;
                border-radius: 100px;
                min-width: 200px;
                min-height: 200px;
            }
            QPushButton:pressed {
                background-color: #b7950b;
            }
        """)
        envi_area_layout.addWidget(Lights_button, alignment=Qt.AlignmentFlag.AlignCenter)
        envi_area_layout.setStretch(1, 1)  # Bottom half gets 50%
        
        # Add the whole thing to self
        self.addWidget(envi_area_widget)