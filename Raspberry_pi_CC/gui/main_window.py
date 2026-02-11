from PyQt6.QtWidgets import (QMainWindow, 
                             QWidget, 
                             QVBoxLayout, 
                             QHBoxLayout, 
                             QLabel)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from .top_layer_buttons import TopLayerButtons
from .widgets.device_panel import DeviceListLayout
from .widgets.environment_panel import EnvironmentLayout
from core.device_manager import deviceManager

class MainWindow(QMainWindow):    
    def __init__(self):
        super().__init__()

        # Initialize the device manager - this starts all sensor threads
        self.device_manager = deviceManager()

        # Build the UI
        self.init_ui()
        
        # TODO: Hide the mouse cursor
        #self.setCursor(Qt.CursorShape.BlankCursor)

    def init_ui(self):
        

        screen = self.screen()
        height = screen.geometry().height()

        titleSize = int(height * 0.04)
        spacingSize = int(height * 0.03)

        Title = "Raspberry Pi Zigbee Controller" #TODO Make Dynamic from user input.

        self.setWindowTitle(Title)
        self.showFullScreen()
        self.setStyleSheet("background-color: #2c3e50;") 
        

        Central_widget = QWidget()
        main_layout = QVBoxLayout()

        Central_widget.setLayout(main_layout)

        self.setCentralWidget(Central_widget)

        ###### Title ######
        title_widget = QLabel(Title)
        title_widget.setFont(QFont('Arial', titleSize, QFont.Weight.Bold))
        title_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_widget.setStyleSheet("color: #ecf0f1; padding: 20px;")
        main_layout.addWidget(title_widget)
        main_layout.addSpacing(spacingSize)

        ###### settings, device pairing, and logs ######
        top_layer_buttons = TopLayerButtons(height)
        main_layout.addLayout(top_layer_buttons)

        main_layout.addSpacing(spacingSize)

        ###### Devices and Environment Area ######
        Devices_layout = QHBoxLayout()
        Devices_layout.setSpacing(int(height * 0.015))
        device_list_layout = DeviceListLayout(height)
        
        # Environment panel - pass the sensor from device manager
        # The sensor parameter allows the environment panel to connect to sensor signals
        sensor = self.device_manager.get_sensor()
        envi_area_layout = EnvironmentLayout(sensor, height)
        
        Devices_layout.addLayout(device_list_layout)
        Devices_layout.setStretch(Devices_layout.count() - 1, 1)  # device_list_layout gets 50%

        Devices_layout.addLayout(envi_area_layout)
        Devices_layout.setStretch(Devices_layout.count() - 1, 1)  # environment_area_layout gets 50%


        main_layout.addLayout(Devices_layout)

    ### TODO: Temperary - Escape key to exit full screen ###
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


    def closeEvent(self, event):
        
        ### Called when the window is about to close. Clean up all resources and stop sensor threads.
        print("Closing application...")
        self.device_manager.stop()
        event.accept()
        print("Application closed")
        