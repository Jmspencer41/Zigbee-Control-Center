from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton)
from PyQt6.QtGui import QFont
from .dialogs.pair_devices_dialog import PairDevicesDialog
from .dialogs.settings_dialog import SettingsDialog
from .dialogs.logs_dialog import LogsDialog 

class TopLayerButtons(QVBoxLayout):
    def __init__(self):
        super().__init__()

###### TODO: Add buttons and functionality below ######
        Button_Layout = QHBoxLayout()
        Button_Layout.setSpacing(20)

        #Button to pair new devices into network
        pair_button = QPushButton('Pair Devices')
        pair_button.setMinimumHeight(60)
        pair_button.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        pair_button.clicked.connect(self.on_pair_clicked)
        pair_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 30px;
                padding: 10px;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        Button_Layout.addWidget(pair_button)

        #Button to view device logs
        logs_button = QPushButton('View Logs')
        logs_button.setMinimumHeight(60)
        logs_button.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        logs_button.clicked.connect(self.on_logs_clicked)
        logs_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 30px;
                padding: 10px;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        Button_Layout.addWidget(logs_button)


        #Button to view device settings
        settings_button = QPushButton('Settings')
        settings_button.setMinimumHeight(60)
        settings_button.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        settings_button.clicked.connect(self.on_settings_clicked)
        settings_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 30px;
                padding: 10px;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
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
        