from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout)
from PyQt6.QtGui import QFont
from Functionality.scrollable_button import ScrollableButton
from Functionality.touch_scroll_area import TouchScrollArea

class DeviceListLayout(QHBoxLayout):
    def __init__(self):
        super().__init__()
 
        scrollable_area = TouchScrollArea()

        device_list_widget = QWidget()
        device_list_widget.setStyleSheet("background-color: #89c2fa; border-radius: 15px;")  # Match background
        device_list_layout = QVBoxLayout()
        device_list_layout.setContentsMargins(10, 10, 10, 10)  # Add padding inside
        device_list_widget.setLayout(device_list_layout)

        # Example device buttons TODO: Make dynamic from actual devices
        for i in range(20):
            device_button = self.create_device_button(f"Device {i+1}")
            device_list_layout.addWidget(device_button)
            device_list_layout.addSpacing(25)

        scrollable_area.setWidget(device_list_widget)
        scrollable_area.setWidgetResizable(True)

        self.addWidget(scrollable_area)

    def create_device_button(self, name):
        
        device_status = True #TODO: Implement actual device status check
        button = ScrollableButton(name) 
        button.setMinimumHeight(100)
        button.setFont(QFont('Arial', 12))

        if device_status:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #00B814;
                    color: white;
                    border-radius: 25px;
                    padding: 10px;
                    text-align: left;
                                }
                    QPushButton:pressed {
                        background-color: #626d6e;
                    }
                """)
        else:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #1abc9c;
                    color: white;
                    border-radius: 25px;
                    padding: 10px;
                    text-align: left;
                                }
                    QPushButton:pressed {
                        background-color: #626d6e;
                    }
                """)
        return button
    