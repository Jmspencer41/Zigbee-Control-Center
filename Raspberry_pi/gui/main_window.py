from PyQt6.QtWidgets import (QMainWindow, 
                             QWidget, 
                             QVBoxLayout, 
                             QHBoxLayout, 
                             QLabel)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from top_layer_buttons import TopLayerButtons
from device_list import DeviceListLayout
from environment import EnvironmentLayout

### TODO: Make sizes of icons, buttons, fonts dynamic based on screen size ###

class MainWindow(QMainWindow):    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
        # TODO: Hide the mouse cursor
        #self.setCursor(Qt.CursorShape.BlankCursor)

    def init_ui(self):
        

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
        title_widget.setFont(QFont('Arial', 20, QFont.Weight.Bold))
        title_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_widget.setStyleSheet("color: #ecf0f1; padding: 20px;")
        main_layout.addWidget(title_widget)

        main_layout.addSpacing(20)

        top_layer_buttons = TopLayerButtons()
        main_layout.addLayout(top_layer_buttons)

        main_layout.addSpacing(30)

        Devices_layout = QHBoxLayout()
        Devices_layout.setSpacing(15)
        device_list_layout = DeviceListLayout()
        envi_area_layout = EnvironmentLayout()
        
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
        