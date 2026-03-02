"""
network_status_widget.py

A compact network status indicator for the main GUI.
Shows a colored dot + label:
  🔴 Network Offline     — ESP32 not connected via serial
  🟡 Network Starting    — Serial connected, waiting for GATEWAY_READY
  🟢 Network Active      — Zigbee network is formed and operational

Sits in the top area of the main window, always visible.
Connect it to DeviceManager signals to update automatically.

Usage in main_window.py:
    from .widgets.network_status_widget import NetworkStatusWidget

    self.network_status = NetworkStatusWidget(screen_height)
    main_layout.addWidget(self.network_status)

    # Wire it up to device manager signals
    self.device_manager.gateway_connection_changed.connect(self.network_status.on_serial_status)
    self.device_manager.gateway_ready_received.connect(self.network_status.on_gateway_ready)
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont


class NetworkStatusWidget(QWidget):
    """
    Compact status indicator showing Zigbee network health.
    
    States:
        "offline"   → red dot,    "Network Offline"
        "starting"  → yellow dot, "Network Starting..."
        "active"    → green dot,  "Network Active"  (+ PAN/channel info)
    """

    # Color definitions matching the app's dark theme
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

        # ── Layout ──────────────────────────────────────────────────────────
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 5, 20, 5)
        layout.setSpacing(10)

        font_size = max(10, int(screen_height * 0.014))
        dot_size = max(12, int(screen_height * 0.015))

        # Colored dot indicator
        self._dot_label = QLabel("●")
        self._dot_label.setFont(QFont('Arial', dot_size))
        self._dot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._dot_label)

        # Status text
        self._text_label = QLabel("Network Offline")
        self._text_label.setFont(QFont('Arial', font_size, QFont.Weight.Bold))
        self._text_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._text_label)

        # Network details (PAN ID, channel) — shown only when active
        self._detail_label = QLabel("")
        self._detail_label.setFont(QFont('Arial', max(8, int(screen_height * 0.011))))
        self._detail_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self._detail_label.setStyleSheet("color: #95a5a6;")
        layout.addWidget(self._detail_label)

        layout.addStretch()

        # Apply initial styling
        self._update_display()

    # ── Public Slots (connect to DeviceManager signals) ─────────────────────

    def on_serial_status(self, is_connected: bool):
        """
        Called when the serial connection to the ESP32 changes.
        Connect to: device_manager.gateway_connection_changed
        """
        if is_connected:
            self._set_state("starting")
        else:
            self._set_state("offline")

    def on_gateway_ready(self, pan_id: str, channel: int, addr: str):
        """
        Called when the ESP32 reports GATEWAY_READY.
        Connect to: device_manager.gateway_ready_received
        """
        self._pan_id = pan_id
        self._channel = channel
        self._set_state("active")

    # ── Internal ────────────────────────────────────────────────────────────

    def _set_state(self, state: str):
        """Update the visual state."""
        if state == self._state:
            return
        self._state = state
        self._update_display()

    def _update_display(self):
        """Apply colors and text based on current state."""
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
        """Return current state string: 'offline', 'starting', or 'active'."""
        return self._state