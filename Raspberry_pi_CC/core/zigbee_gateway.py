import json
import threading
import time
import serial
from PyQt6.QtCore import QThread, pyqtSignal


# ── CLUSTER_DEFINITIONS ────────────────────────────────────────────────────────
# Maps ZCL cluster/attr IDs to names and types.
# device_manager.py imports this to resolve capability names from ATTR_REPORT messages.

CLUSTER_DEFINITIONS = {
    0x0006: {
        "name": "On/Off Switch",
        "attributes": {
            0x0000: {
                "name":     "on_off",
                "type":     "bool",
                "writable": True,
                "scale":    1,
                "unit":     "",
            }
        }
    },
    0x0008: {
        "name": "Brightness",
        "attributes": {
            0x0000: {
                "name":     "level",
                "type":     "uint8",
                "writable": True,
                "scale":    1,
                "unit":     "",
            }
        }
    },
    0x0402: {
        "name": "Temperature",
        "attributes": {
            0x0000: {
                "name":     "temperature",
                "type":     "int16",
                "writable": False,
                "scale":    100,
                "unit":     "°C",
            }
        }
    },
    0x0405: {
        "name": "Humidity",
        "attributes": {
            0x0000: {
                "name":     "humidity",
                "type":     "uint16",
                "writable": False,
                "scale":    100,
                "unit":     "%",
            }
        }
    },
}


def convert_ui_value_to_raw(ui_value, attr_def: dict):
    """Convert a GUI value back to a raw ZCL integer."""
    scale     = attr_def.get("scale", 1)
    attr_type = attr_def.get("type", "uint8")

    if attr_type == "bool":
        return 1 if ui_value else 0

    raw = int(round(float(ui_value) * scale))

    if attr_type == "uint8":
        return max(0, min(254, raw))
    if attr_type == "uint16":
        return max(0, min(65534, raw))
    if attr_type == "int16":
        return max(-32768, min(32767, raw))

    return raw


# ── DEVICE MODEL ───────────────────────────────────────────────────────────────
# device_manager.py imports DeviceModel to track joined devices.

class DeviceModel:
    def __init__(self, short_addr: str, ieee_addr: str):
        self.short_addr = short_addr
        self.ieee_addr  = ieee_addr
        self.name       = short_addr
        self._endpoints: dict[int, list] = {}
        self._state:     dict[tuple, object] = {}

    def add_endpoint(self, endpoint: int, cluster_ids: list):
        self._endpoints[endpoint] = cluster_ids
        self._derive_name()

    def _derive_name(self):
        clusters = set()
        for cl in self._endpoints.values():
            clusters.update(cl)

        if 0x0006 in clusters and 0x0008 in clusters:
            self.name = "Dimmable Light"
        elif 0x0006 in clusters:
            self.name = "On/Off Switch"
        elif 0x0402 in clusters and 0x0405 in clusters:
            self.name = "Temp/Humidity Sensor"
        elif 0x0402 in clusters:
            self.name = "Temperature Sensor"
        else:
            self.name = f"Device {self.short_addr}"

    def update_state(self, endpoint: int, cluster_id: int,
                     attr_id: int, raw_value: int):
        cluster_def = CLUSTER_DEFINITIONS.get(cluster_id)
        if cluster_def:
            attr_def = cluster_def["attributes"].get(attr_id)
            if attr_def:
                scale     = attr_def.get("scale", 1)
                converted = raw_value / scale if scale != 1 else raw_value
                self._state[(endpoint, cluster_id, attr_id)] = converted
                return converted
        self._state[(endpoint, cluster_id, attr_id)] = raw_value
        return raw_value

    def get_state(self, endpoint: int, cluster_id: int, attr_id: int):
        return self._state.get((endpoint, cluster_id, attr_id))

    def get_on_off(self, endpoint: int = 1) -> bool | None:
        val = self.get_state(endpoint, 0x0006, 0x0000)
        return bool(val) if val is not None else None

    @property
    def endpoints(self):
        return self._endpoints


# ══════════════════════════════════════════════════════════════════════════════
# ZIGBEE GATEWAY  —  original class, unchanged
# ══════════════════════════════════════════════════════════════════════════════

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
            print(f"  ✓ ESP32 coordinator connected and Zigbee network is live")
            self.gateway_ready.emit(pan_id, channel, addr)

        elif cmd == "NETWORK_OPEN":
            seconds = msg.get("seconds", 0)
            print(f"  Network open for {seconds}s — pairing window active")
            self.pairing_status_changed.emit(True, seconds)

        elif cmd == "NETWORK_CLOSED":
            print(f"  Pairing window closed")
            self.pairing_status_changed.emit(False, 0)

        elif cmd == "DEVICE_JOINED":
            addr = msg.get("addr", "0x0000")
            ieee = msg.get("ieee", "00:00:00:00:00:00:00:00")
            print(f"  New device joined: addr={addr} ieee={ieee}")
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
            print(f"  Attr report: {addr} cluster=0x{cluster:04X} attr=0x{attr:04X} value={raw_value}")
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

    def send_configure(self, channel: int, room_name: str) -> bool:
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