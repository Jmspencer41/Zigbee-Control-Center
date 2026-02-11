from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton)
from PyQt6.QtGui import QFont
from .dialogs.pair_devices_dialog import PairDevicesDialog
from .dialogs.settings_dialog import SettingsDialog
from .dialogs.logs_dialog import LogsDialog 

class TopLayerButtons(QVBoxLayout):
    def __init__(self, screen_height):
        super().__init__()

        Button_Layout = QHBoxLayout()
        Button_Layout.setSpacing(int(screen_height * 0.02))

        #Button to pair new devices into network
        pair_button = QPushButton('Pair Devices')
        pair_button.setMinimumHeight(int(screen_height * 0.06))
        pair_button.setFont(QFont('Arial', int(screen_height * 0.015), QFont.Weight.Bold))
        pair_button.clicked.connect(self.on_pair_clicked)

        border_radius = int(screen_height * 0.03)
        padding = int(screen_height * 0.01)
        pair_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #3498db;
                color: white;
                border-radius: {border_radius}px;
                padding: {padding}px;
            }}
            QPushButton:pressed {{
                background-color: #21618c;
            }}
        """)
        Button_Layout.addWidget(pair_button)

        #Button to view device logs
        logs_button = QPushButton('View Logs')
        logs_button.setMinimumHeight(int(screen_height * 0.06))
        logs_button.setFont(QFont('Arial', int(screen_height * 0.015), QFont.Weight.Bold))
        logs_button.clicked.connect(self.on_logs_clicked)
        logs_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #3498db;
                color: white;
                border-radius: {border_radius}px;
                padding: {padding}px;
            }}
            QPushButton:pressed {{
                background-color: #21618c;
            }}
        """)
        Button_Layout.addWidget(logs_button)


        #Button to view device settings
        settings_button = QPushButton('Settings')
        settings_button.setMinimumHeight(int(screen_height * 0.06))
        settings_button.setFont(QFont('Arial', int(screen_height * 0.015), QFont.Weight.Bold))
        settings_button.clicked.connect(self.on_settings_clicked)
        settings_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #3498db;
                color: white;
                border-radius: {border_radius}px;
                padding: {padding}px;
            }}
            QPushButton:pressed {{
                background-color: #21618c;
            }}
        """)
        Button_Layout.addWidget(settings_button)

        self.addLayout(Button_Layout)

    def on_pair_clicked(self):
        dialog = PairDevicesDialog()
        dialog.exec()

    def on_settings_clicked(self):
        dialog = SettingsDialog()
        dialog.exec()
    
    def on_logs_clicked(self):
        dialog = LogsDialog()
        dialog.exec()
        