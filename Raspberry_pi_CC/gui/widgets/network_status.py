"""
network_status_widget.py

Compact network status indicator for the main GUI.
Shows a colored dot + label:
  🔴 Network Offline     — ESP32 not connected via serial
  🟡 Network Starting    — Serial connected, waiting for GATEWAY_READY
  🟢 Network Active      — Zigbee network is formed and operational

Connect to DeviceManager signals to update automatically.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class NetworkStatusWidget(QWidget):

    COLORS = {
        "offline":  {"dot": "#e74c3c", "text": "#e74c3c", "label": "Network Offline"},
        "starting": {"dot": "#f39c12", "text": "#f39c12", "label": "Network Starting..."},
        "active":   {"dot": "#2ecc71", "text": "#2ecc71", "label": "Network Active"},
    }

    def __init__(self, screen_height: int, parent=None):
        super().__init__(parent)
        self._state = "offline"
        self._pan_id = ""
        self._channel = 0

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 5, 20, 5)
        layout.setSpacing(10)

        font_size = max(10, int(screen_height * 0.014))
        dot_size = max(12, int(screen_height * 0.015))

        self._dot_label = QLabel("●")
        self._dot_label.setFont(QFont('Arial', dot_size))
        self._dot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._dot_label)

        self._text_label = QLabel("Network Offline")
        self._text_label.setFont(QFont('Arial', font_size, QFont.Weight.Bold))
        self._text_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._text_label)

        self._detail_label = QLabel("")
        self._detail_label.setFont(QFont('Arial', max(8, int(screen_height * 0.011))))
        self._detail_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self._detail_label.setStyleSheet("color: #95a5a6;")
        layout.addWidget(self._detail_label)

        layout.addStretch()
        self._update_display()

    def on_serial_status(self, is_connected: bool):
        if is_connected:
            self._set_state("starting")
        else:
            self._set_state("offline")

    def on_gateway_ready(self, pan_id: str, channel: int, addr: str):
        self._pan_id = pan_id
        self._channel = channel
        self._set_state("active")

    def _set_state(self, state: str):
        if state == self._state:
            return
        self._state = state
        self._update_display()

    def _update_display(self):
        colors = self.COLORS[self._state]
        self._dot_label.setStyleSheet(f"color: {colors['dot']};")
        self._text_label.setStyleSheet(f"color: {colors['text']};")
        self._text_label.setText(colors["label"])

        if self._state == "active" and self._pan_id:
            self._detail_label.setText(f"PAN: {self._pan_id}  Ch: {self._channel}")
            self._detail_label.show()
        else:
            self._detail_label.hide()

    def get_state(self) -> str:
        return self._state