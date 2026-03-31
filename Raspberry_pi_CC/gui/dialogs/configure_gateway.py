"""
configure_gateway_dialog.py

Dialog shown when the ESP32 sends WAITING_FOR_CONFIG — meaning it's a brand
new device that hasn't been assigned a room name and channel yet.

The user picks a room name and channel, clicks Configure, and the Pi sends
the CONFIGURE command to the ESP32. The ESP32 saves it to NVS and starts
the Zigbee network.

Usage:
    dialog = ConfigureGatewayDialog(mac="AA:BB:CC:DD:EE:FF", pan_id="0x3B7A")
    if dialog.exec():
        channel   = dialog.selected_channel
        room_name = dialog.selected_room_name
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QGroupBox,
    QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


# Channels that sit between common Wi-Fi channels — best choices
PREFERRED_CHANNELS = [
    (15, "Channel 15  (best — between Wi-Fi 1 & 6)"),
    (20, "Channel 20  (best — between Wi-Fi 6 & 11)"),
    (25, "Channel 25  (best — above Wi-Fi 11)"),
]

SECONDARY_CHANNELS = [
    (11, "Channel 11  (some Wi-Fi overlap)"),
    (17, "Channel 17  (some Wi-Fi overlap)"),
    (22, "Channel 22  (some Wi-Fi overlap)"),
    (26, "Channel 26  (some Wi-Fi overlap)"),
]


class ConfigureGatewayDialog(QDialog):
    """
    First-boot configuration dialog for a new ESP32 coordinator.
    """

    def __init__(self, mac: str = "", pan_id: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure New Zigbee Coordinator")
        self.setMinimumWidth(450)
        self.setStyleSheet("""
            QDialog { background-color: #2c3e50; }
            QLabel { color: #ecf0f1; }
            QLineEdit {
                background-color: #34495e;
                color: #ecf0f1;
                border: 1px solid #7f8c8d;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }
            QComboBox {
                background-color: #34495e;
                color: #ecf0f1;
                border: 1px solid #7f8c8d;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }
            QGroupBox {
                color: #bdc3c7;
                border: 1px solid #7f8c8d;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        self.selected_channel = None
        self.selected_room_name = None

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # ── Header ──────────────────────────────────────────────────────────
        header = QLabel("New Coordinator Detected")
        header.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #3498db;")
        layout.addWidget(header)

        desc = QLabel(
            "An unconfigured ESP32 coordinator has been connected.\n"
            "Assign a room name and Zigbee channel to get started."
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("color: #95a5a6; font-size: 12px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # ── Device info ─────────────────────────────────────────────────────
        info_group = QGroupBox("Device Info")
        info_layout = QVBoxLayout(info_group)

        mac_label = QLabel(f"MAC Address:  {mac}")
        mac_label.setFont(QFont('Courier', 11))
        mac_label.setStyleSheet("color: #2ecc71;")
        info_layout.addWidget(mac_label)

        pan_label = QLabel(f"Generated PAN ID:  {pan_id}")
        pan_label.setFont(QFont('Courier', 11))
        pan_label.setStyleSheet("color: #2ecc71;")
        info_layout.addWidget(pan_label)

        layout.addWidget(info_group)

        # ── Room name ───────────────────────────────────────────────────────
        config_group = QGroupBox("Configuration")
        config_layout = QVBoxLayout(config_group)

        room_label = QLabel("Room Name:")
        room_label.setFont(QFont('Arial', 12))
        config_layout.addWidget(room_label)

        self._room_input = QLineEdit()
        self._room_input.setPlaceholderText("e.g. Living Room, Kitchen, Bedroom 1...")
        self._room_input.setMaxLength(30)
        config_layout.addWidget(self._room_input)

        config_layout.addSpacing(10)

        # ── Channel selection ───────────────────────────────────────────────
        channel_label = QLabel("Zigbee Channel:")
        channel_label.setFont(QFont('Arial', 12))
        config_layout.addWidget(channel_label)

        self._channel_combo = QComboBox()
        for ch_num, ch_desc in PREFERRED_CHANNELS:
            self._channel_combo.addItem(ch_desc, ch_num)
        self._channel_combo.insertSeparator(len(PREFERRED_CHANNELS))
        for ch_num, ch_desc in SECONDARY_CHANNELS:
            self._channel_combo.addItem(ch_desc, ch_num)
        config_layout.addWidget(self._channel_combo)

        channel_hint = QLabel(
            "Each room should use a different channel.\n"
            "Preferred channels have no Wi-Fi interference."
        )
        channel_hint.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        channel_hint.setWordWrap(True)
        config_layout.addWidget(channel_hint)

        layout.addWidget(config_group)

        # ── Buttons ─────────────────────────────────────────────────────────
        button_layout = QHBoxLayout()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #7f8c8d;
                color: white;
                border-radius: 8px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:pressed { background-color: #5d6d7e; }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        configure_btn = QPushButton("Configure & Start")
        configure_btn.setMinimumHeight(40)
        configure_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border-radius: 8px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:pressed { background-color: #27ae60; }
        """)
        configure_btn.clicked.connect(self._on_configure)
        button_layout.addWidget(configure_btn)

        layout.addLayout(button_layout)

    def _on_configure(self):
        room = self._room_input.text().strip()
        if not room:
            QMessageBox.warning(self, "Missing Room Name",
                                "Please enter a room name.")
            return

        self.selected_room_name = room
        self.selected_channel = self._channel_combo.currentData()
        self.accept()