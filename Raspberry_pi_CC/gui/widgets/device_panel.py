from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout)
from PyQt6.QtGui import QFont
from ..Functionality.scrollable_button import ScrollableButton
from ..Functionality.touch_scroll_area import TouchScrollArea

class DeviceListLayout(QHBoxLayout):
    def __init__(self, screen_height):
        super().__init__()
 
        scrollable_area = TouchScrollArea()

        device_list_widget = QWidget()
        device_list_widget.setStyleSheet("background-color: #99ddff; border-radius: 15px;")  # Match background
        device_list_layout = QVBoxLayout()

        padding = int(screen_height * 0.01)
        device_list_layout.setContentsMargins(padding, padding, padding, padding)  # Add padding inside
        device_list_widget.setLayout(device_list_layout)

        # Example device buttons TODO: Make dynamic from actual devices
        for i in range(20):
            device_button = self.create_device_button(f"Device {i+1}", screen_height)
            device_list_layout.addWidget(device_button)
            device_list_layout.addSpacing(int(screen_height * 0.03))  # Add spacing between buttons 30% of screen height

        scrollable_area.setWidget(device_list_widget)
        scrollable_area.setWidgetResizable(True)

        self.addWidget(scrollable_area)

    def create_device_button(self, name, screen_height):
        
        device_status = True #TODO: Implement actual device status check
        button = ScrollableButton(name) 
        button.setMinimumHeight(int(screen_height * 0.12))  # Set minimum height to 12% of screen height
        button.setFont(QFont('Arial', int(screen_height * 0.02)))

        border_radius = int(screen_height * 0.03)
        padding = int(screen_height * 0.01)  

        if device_status:
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: #00994d;
                    color: white;
                    border-radius: {border_radius}px;
                    padding: {padding}px;
                    text-align: left;
                    border: 2px solid rgba(0, 0, 0, 0.2);
                }}
                    QPushButton:pressed {{
                        background-color: #626d6e;
                    }}
                """)
        else:
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: #1abc9c;
                    color: white;
                    border-radius: {border_radius}px;
                    padding: {padding}px;
                    text-align: left;
                    border: 2px solid rgba(0, 0, 0, 0.2);
                }}
                QPushButton:pressed {{
                    background-color: #626d6e;
                }}
                """)
        return button
    