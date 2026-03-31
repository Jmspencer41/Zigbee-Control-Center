"""
zigbee_gateway_patches.py

This file documents the CHANGES to make to your existing zigbee_gateway.py.
It's not a standalone file — apply these changes to your existing code.

── SUMMARY OF CHANGES ─────────────────────────────────────────────────────────

1. Add a new signal:  config_requested
2. Add a new method:  send_configure()
3. Update _parse_message() to handle WAITING_FOR_CONFIG

Below is the complete updated ZigbeeGateway class with all changes marked.
Replace your existing ZigbeeGateway class with this one.
"""

import json
import threading
import time
import serial
from PyQt6.QtCore import QThread, pyqtSignal


class ZigbeeGateway(QThread):
    """
    Background QThread that manages the serial connection to the ESP32 coordinator.
    """

    # ── Qt Signals ─────────────────────────────────────────────────────────────

    gateway_ready = pyqtSignal(str, int, str)         # pan_id, channel, addr
    pairing_status_changed = pyqtSignal(bool, int)    # is_open, seconds
    device_joined = pyqtSignal(str, str)              # short_addr, ieee_addr
    device_descriptor_received = pyqtSignal(str, int, list)
    attribute_reported = pyqtSignal(str, int, int, int, str, int)
    command_ack = pyqtSignal(bool, str)               # is_ok, detail
    connection_status_changed = pyqtSignal(bool)      # is_connected

    # ──────────────────────────────────────────────────────────────────────────
    # NEW: Emitted when ESP32 sends WAITING_FOR_CONFIG (unconfigured device)
    # Args: mac (str), pan_id (str)
    # The GUI connects to this to show a configuration dialog.
    # ──────────────────────────────────────────────────────────────────────────
    config_requested = pyqtSignal(str, str)

    def __init__(self, port: str = "/dev/ttyACM0", baud: int = 115200):
        super().__init__()
        self.port    = port
        self.baud    = baud
        self.running = True
        self._serial: serial.Serial | None = None
        self._write_lock = threading.Lock()
        print(f"ZigbeeGateway: will connect to {port} at {baud} baud")

    # ── Background Thread ──────────────────────────────────────────────────────

    def run(self):
        print("ZigbeeGateway thread started")
        while self.running:
            if not self._connect():
                print(f"ZigbeeGateway: could not open {self.port}, retrying in 3s...")
                time.sleep(3)
                continue
            self._read_loop()
        print("ZigbeeGateway thread stopped")

    def _connect(self) -> bool:
        try:
            self._serial = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                timeout=1.0,
            )
            print(f"ZigbeeGateway: connected to {self.port}")
            self.connection_status_changed.emit(True)
            return True
        except serial.SerialException as e:
            print(f"ZigbeeGateway: serial open failed: {e}")
            self._serial = None
            return False

    def _read_loop(self):
        while self.running:
            try:
                raw_bytes = self._serial.readline()
                if not raw_bytes:
                    continue
                line = raw_bytes.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                self._parse_message(line)
            except serial.SerialException as e:
                print(f"ZigbeeGateway: serial error: {e}")
                self.connection_status_changed.emit(False)
                if self._serial:
                    try:
                        self._serial.close()
                    except Exception:
                        pass
                    self._serial = None
                break
            except UnicodeDecodeError as e:
                print(f"ZigbeeGateway: decode error: {e}")
                continue

    def _parse_message(self, line: str):
        try:
            msg = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"ZigbeeGateway: JSON parse error on line: {line!r} ({e})")
            return

        cmd = msg.get("cmd")
        if not cmd:
            print(f"ZigbeeGateway: message has no 'cmd' field: {msg}")
            return

        print(f"ZigbeeGateway ← ESP32: {cmd}")

        # ── NEW: Handle WAITING_FOR_CONFIG ─────────────────────────────────
        if cmd == "WAITING_FOR_CONFIG":
            mac    = msg.get("mac", "00:00:00:00:00:00")
            pan_id = msg.get("pan_id", "0x0000")
            print(f"  ESP32 needs configuration: MAC={mac} PAN={pan_id}")
            self.config_requested.emit(mac, pan_id)

        elif cmd == "GATEWAY_READY":
            pan_id  = msg.get("pan_id", "0x0000")
            channel = msg.get("channel", 0)
            addr    = msg.get("addr", "0x0000")
            room    = msg.get("room", "Unknown")
            print(f"  Gateway ready: room={room} PAN={pan_id} Ch={channel} Addr={addr}")
            self.gateway_ready.emit(pan_id, channel, addr)

        elif cmd == "NETWORK_OPEN":
            seconds = msg.get("seconds", 0)
            self.pairing_status_changed.emit(True, seconds)

        elif cmd == "NETWORK_CLOSED":
            self.pairing_status_changed.emit(False, 0)

        elif cmd == "DEVICE_JOINED":
            addr = msg.get("addr", "0x0000")
            ieee = msg.get("ieee", "00:00:00:00:00:00:00:00")
            print(f"  New device: {addr} (IEEE: {ieee})")
            self.device_joined.emit(addr, ieee)

        elif cmd == "DEVICE_DESCRIPTOR":
            addr     = msg.get("addr", "0x0000")
            endpoint = msg.get("endpoint", 1)
            clusters = msg.get("clusters", [])
            print(f"  Descriptor for {addr} ep{endpoint}: {[hex(c) for c in clusters]}")
            self.device_descriptor_received.emit(addr, endpoint, clusters)

        elif cmd == "ATTR_REPORT":
            addr      = msg.get("addr", "0x0000")
            endpoint  = msg.get("endpoint", 1)
            cluster   = msg.get("cluster", 0)
            attr      = msg.get("attr", 0)
            type_str  = msg.get("type", "uint8")
            raw_value = msg.get("value", 0)
            self.attribute_reported.emit(addr, endpoint, cluster, attr, type_str, raw_value)

        elif cmd == "CMD_ACK":
            is_ok  = msg.get("status") == "ok"
            detail = msg.get("detail", "")
            self.command_ack.emit(is_ok, detail)

        elif cmd == "ERROR":
            detail = msg.get("detail", "unknown_error")
            print(f"  ESP32 error: {detail}")
            self.command_ack.emit(False, detail)

        else:
            print(f"ZigbeeGateway: unhandled cmd: {cmd}")

    # ── Sending Commands ───────────────────────────────────────────────────────

    def send_command(self, cmd_dict: dict) -> bool:
        if not self._serial or not self._serial.is_open:
            print("ZigbeeGateway: cannot send — not connected")
            return False
        try:
            line = json.dumps(cmd_dict) + "\n"
            with self._write_lock:
                self._serial.write(line.encode("utf-8"))
                self._serial.flush()
            print(f"ZigbeeGateway → ESP32: {cmd_dict['cmd']}")
            return True
        except serial.SerialException as e:
            print(f"ZigbeeGateway: write failed: {e}")
            return False

    # ──────────────────────────────────────────────────────────────────────────
    # NEW: Send configuration to an unconfigured ESP32
    # ──────────────────────────────────────────────────────────────────────────
    def send_configure(self, channel: int, room_name: str) -> bool:
        """
        Send the CONFIGURE command to an unconfigured ESP32.
        The ESP32 saves this to NVS and starts the Zigbee stack.

        Args:
            channel:   Zigbee channel (11-26)
            room_name: Human-readable room name

        Returns:
            True if the command was sent successfully.
        """
        return self.send_command({
            "cmd":     "CONFIGURE",
            "channel": channel,
            "room":    room_name,
        })

    def open_network(self, duration_seconds: int = 180) -> bool:
        return self.send_command({
            "cmd":      "OPEN_NETWORK",
            "duration": min(duration_seconds, 254)
        })

    def close_network(self) -> bool:
        return self.send_command({"cmd": "CLOSE_NETWORK"})

    def set_attribute(self, addr: str, endpoint: int, cluster: int,
                       attr: int, attr_type: str, value) -> bool:
        return self.send_command({
            "cmd":      "SET_ATTR",
            "addr":     addr,
            "endpoint": endpoint,
            "cluster":  cluster,
            "attr":     attr,
            "type":     attr_type,
            "value":    int(value),
        })

    def set_attribute_from_ui(self, addr: str, endpoint: int, cluster: int,
                               attr: int, ui_value) -> bool:
        from zigbee_gateway import CLUSTER_DEFINITIONS, convert_ui_value_to_raw
        cluster_def = CLUSTER_DEFINITIONS.get(cluster)
        if not cluster_def:
            return False
        attr_def = cluster_def["attributes"].get(attr)
        if not attr_def:
            return False
        if not attr_def.get("writable", False):
            return False
        raw_value = convert_ui_value_to_raw(ui_value, attr_def)
        return self.set_attribute(addr, endpoint, cluster, attr,
                                   attr_def["type"], raw_value)

    def read_attribute(self, addr: str, endpoint: int, cluster: int, attr: int) -> bool:
        return self.send_command({
            "cmd":      "READ_ATTR",
            "addr":     addr,
            "endpoint": endpoint,
            "cluster":  cluster,
            "attr":     attr,
        })

    def stop(self):
        print("ZigbeeGateway: stopping...")
        self.running = False
        if self._serial and self._serial.is_open:
            try:
                self._serial.close()
            except Exception:
                pass
        self.wait(3000)
        print("ZigbeeGateway: stopped")