"""
zigbee_gateway.py

This module is the Raspberry Pi side of the serial bridge to the ESP32-C6 coordinator.
It runs in a background QThread and does three things:

  1. Opens the serial port to the ESP32 (USB or UART)
  2. Reads newline-delimited JSON messages from the ESP32 and emits Qt signals
  3. Provides methods to send commands back to the ESP32

── HOW IT FITS INTO THE APP ─────────────────────────────────────────────────

  ZigbeeGateway is a QThread. It loops forever reading from serial.
  When it gets a message, it emits a Qt signal (like data_updated in SHT41).
  The DeviceManager connects to those signals and updates its device registry.
  The GUI connects to the DeviceManager to update the display.

  Serial port (blocking read) → ZigbeeGateway thread → Qt signals → DeviceManager → GUI

── SERIAL PROTOCOL ───────────────────────────────────────────────────────────

  Every message is one line of JSON ending in \\n.

  FROM ESP32 → Pi (we receive these):
    {"cmd":"GATEWAY_READY","pan_id":"0x1A2B","channel":13,"addr":"0x0000"}
    {"cmd":"NETWORK_OPEN","seconds":180}
    {"cmd":"NETWORK_CLOSED"}
    {"cmd":"DEVICE_JOINED","addr":"0x3C4D","ieee":"aa:bb:cc:dd:ee:ff:00:11"}
    {"cmd":"DEVICE_DESCRIPTOR","addr":"0x3C4D","endpoint":1,"clusters":[6,8,768]}
    {"cmd":"ATTR_REPORT","addr":"0x3C4D","endpoint":1,"cluster":6,"attr":0,"type":"bool","value":1}
    {"cmd":"CMD_ACK","status":"ok","detail":"network_opened"}
    {"cmd":"ERROR","detail":"something_went_wrong"}

  FROM Pi → ESP32 (we send these):
    {"cmd":"OPEN_NETWORK","duration":180}
    {"cmd":"CLOSE_NETWORK"}
    {"cmd":"SET_ATTR","addr":"0x3C4D","endpoint":1,"cluster":6,"attr":0,"type":"bool","value":1}
    {"cmd":"READ_ATTR","addr":"0x3C4D","endpoint":1,"cluster":6,"attr":0}

── ZCL CLUSTER DEFINITIONS ───────────────────────────────────────────────────

  CLUSTER_DEFINITIONS maps Zigbee cluster IDs to human-readable variable definitions.
  This is the single source of truth for what each cluster means.

  When the ESP32 sends DEVICE_DESCRIPTOR with a list of cluster IDs, we look up
  each ID here to know what variables the device has and how to display them.

  Cluster ID → name, attributes → name, type, range, writable

  Attribute types we use:
    bool   → on/off toggle          (value is 0 or 1)
    uint8  → 0-254 integer          (e.g., brightness level)
    uint16 → 0-65535 integer        (e.g., color temperature in Kelvin)
    int16  → signed integer         (e.g., temperature in centidegrees: 2150 = 21.50°C)
    float  → normalized 0.0-1.0     (we convert uint8 0-254 to float 0-1 for the GUI)
"""

import json
import threading
import time
import serial                        # pip install pyserial
from PyQt6.QtCore import QThread, pyqtSignal


# ── ZCL Cluster Definitions ────────────────────────────────────────────────────
#
# This dictionary maps 16-bit Zigbee cluster IDs to their meaning.
# Add entries here as you support more device types.
#
# Structure:
#   cluster_id (int): {
#     "name": human-readable cluster name (used for logging/debugging),
#     "attributes": {
#       attr_id (int): {
#         "name":     variable name (used as dict key in device state),
#         "type":     how to interpret the raw value from the ESP32,
#         "writable": True if we can SET this attribute (False = read-only sensor data),
#         "range":    (min, max) of the raw value from Zigbee,
#         "ui_range": (min, max) as presented in the GUI (we do the conversion),
#         "ui_type":  "toggle", "slider", "display" — hints for the GUI factory
#       }
#     }
#   }
#
CLUSTER_DEFINITIONS = {

    # ── On/Off Cluster (0x0006) ────────────────────────────────────────────────
    # The simplest cluster. One attribute: is the device on or off?
    # Used by: lights, switches, outlets, fans (binary on/off only)
    0x0006: {
        "name": "on_off",
        "attributes": {
            0x0000: {
                "name":     "on_off",
                "type":     "bool",
                "writable": True,
                "range":    (0, 1),
                "ui_range": (0, 1),
                "ui_type":  "toggle",
            }
        }
    },

    # ── Level Control Cluster (0x0008) ─────────────────────────────────────────
    # Dimming control. Level goes from 0 (off) to 254 (full brightness).
    # We normalize this to 0.0-1.0 for the GUI slider.
    # Used by: dimmable lights, fan speed controllers
    0x0008: {
        "name": "level_control",
        "attributes": {
            0x0000: {
                "name":     "current_level",
                "type":     "uint8",
                "writable": True,
                "range":    (0, 254),
                "ui_range": (0.0, 1.0),   # GUI shows 0-100%, we map 0-254 → 0.0-1.0
                "ui_type":  "slider",
            }
        }
    },

    # ── Color Control Cluster (0x0300) ─────────────────────────────────────────
    # RGB and color temperature control for smart bulbs.
    # Hue: 0-254 maps to 0°-360° on the color wheel
    # Saturation: 0 = white, 254 = fully saturated color
    # Color temperature: in "mireds" (1,000,000 / Kelvin), lower = cooler/bluer
    0x0300: {
        "name": "color_control",
        "attributes": {
            0x0000: {
                "name":     "hue",
                "type":     "uint8",
                "writable": True,
                "range":    (0, 254),
                "ui_range": (0, 360),     # GUI shows degrees
                "ui_type":  "hue_slider",
            },
            0x0001: {
                "name":     "saturation",
                "type":     "uint8",
                "writable": True,
                "range":    (0, 254),
                "ui_range": (0.0, 1.0),
                "ui_type":  "slider",
            },
            0x0007: {
                "name":     "color_temperature",
                "type":     "uint16",
                "writable": True,
                "range":    (153, 500),   # ~2000K to 6500K in mireds
                "ui_range": (2000, 6500), # GUI shows Kelvin
                "ui_type":  "slider",
            }
        }
    },

    # ── Window Covering Cluster (0x0102) ───────────────────────────────────────
    # For motorized blinds, curtains, vents, dampers.
    # Lift percentage: 0 = fully closed, 100 = fully open
    0x0102: {
        "name": "window_covering",
        "attributes": {
            0x0008: {
                "name":     "lift_percent",
                "type":     "uint8",
                "writable": True,
                "range":    (0, 100),
                "ui_range": (0.0, 1.0),
                "ui_type":  "slider",
            }
        }
    },

    # ── Temperature Measurement Cluster (0x0402) ───────────────────────────────
    # Read-only sensor data. Value is in centidegrees Celsius (divide by 100).
    # e.g., value 2150 = 21.50°C
    0x0402: {
        "name": "temperature",
        "attributes": {
            0x0000: {
                "name":     "temperature",
                "type":     "int16",
                "writable": False,        # Sensor data — we can't write to it
                "range":    (-27315, 32767),
                "ui_range": (-273.15, 327.67),
                "ui_type":  "display",    # GUI shows this as a read-only value
                "scale":    0.01,         # Multiply raw value by this to get Celsius
            }
        }
    },

    # ── Relative Humidity Cluster (0x0405) ─────────────────────────────────────
    # Value is in centipercent (divide by 100). e.g., 6500 = 65.00%
    0x0405: {
        "name": "humidity",
        "attributes": {
            0x0000: {
                "name":     "humidity",
                "type":     "uint16",
                "writable": False,
                "range":    (0, 10000),
                "ui_range": (0.0, 100.0),
                "ui_type":  "display",
                "scale":    0.01,
            }
        }
    },

    # ── Occupancy Sensing Cluster (0x0406) ─────────────────────────────────────
    # Motion/presence sensor. Value is a bitmap — bit 0 = occupied/motion detected.
    0x0406: {
        "name": "occupancy",
        "attributes": {
            0x0000: {
                "name":     "occupancy",
                "type":     "uint8",
                "writable": False,
                "range":    (0, 1),
                "ui_range": (0, 1),
                "ui_type":  "display",
            }
        }
    },
}


def convert_raw_value(raw_value, attr_def):
    """
    Convert a raw Zigbee attribute value to a GUI-friendly value.

    The ESP32 sends raw Zigbee values (e.g., brightness 0-254).
    The GUI wants normalized values (e.g., brightness 0.0-1.0) or scaled values
    (e.g., temperature centidegrees → degrees).

    Args:
        raw_value: The integer value received from the ESP32
        attr_def:  The attribute definition dict from CLUSTER_DEFINITIONS

    Returns:
        The converted value appropriate for the GUI
    """
    ui_type = attr_def.get("ui_type", "display")

    # Apply a fixed scale factor (e.g., temperature /100 for °C)
    if "scale" in attr_def:
        return raw_value * attr_def["scale"]

    raw_min, raw_max = attr_def.get("range", (0, 255))
    ui_min, ui_max   = attr_def.get("ui_range", (0, 1))

    # If the UI range is float (0.0-1.0), normalize the raw value
    if isinstance(ui_min, float) or isinstance(ui_max, float):
        if raw_max == raw_min:
            return ui_min
        # Linear interpolation from raw range to UI range
        normalized = (raw_value - raw_min) / (raw_max - raw_min)
        return ui_min + normalized * (ui_max - ui_min)

    # If UI range is integer and different from raw range, remap
    if (ui_min, ui_max) != (raw_min, raw_max):
        if raw_max == raw_min:
            return ui_min
        normalized = (raw_value - raw_min) / (raw_max - raw_min)
        return int(ui_min + normalized * (ui_max - ui_min))

    # No conversion needed — return as-is
    return raw_value


def convert_ui_value_to_raw(ui_value, attr_def):
    """
    Convert a GUI value back to a raw Zigbee value for sending commands.

    This is the inverse of convert_raw_value(). When the user moves a slider
    in the GUI, we get a float 0.0-1.0 and need to convert it to 0-254 to
    send to the ESP32.

    Args:
        ui_value:  The value from the GUI (float, int, or bool)
        attr_def:  The attribute definition dict from CLUSTER_DEFINITIONS

    Returns:
        Integer raw value to send in SET_ATTR command
    """
    if attr_def.get("type") == "bool":
        return 1 if ui_value else 0

    raw_min, raw_max = attr_def.get("range", (0, 255))
    ui_min, ui_max   = attr_def.get("ui_range", (0, 1))

    # Undo scale factor
    if "scale" in attr_def:
        return int(ui_value / attr_def["scale"])

    # Undo normalization
    if isinstance(ui_min, float) or isinstance(ui_max, float):
        if ui_max == ui_min:
            return raw_min
        normalized = (ui_value - ui_min) / (ui_max - ui_min)
        return int(raw_min + normalized * (raw_max - raw_min))

    return int(ui_value)


class DeviceModel:
    """
    Represents a single Zigbee device that has joined the network.

    This is the data model for a device — not a GUI widget. It stores:
      - The device's network addresses
      - What it can do (clusters and their attributes)
      - The current state of each attribute

    The GUI reads from this model to build the appropriate controls.
    """

    def __init__(self, short_addr: str, ieee_addr: str):
        """
        Args:
            short_addr: 16-bit network address as hex string, e.g. "0x1A2B"
            ieee_addr:  64-bit permanent address as hex string, e.g. "aa:bb:cc:dd:ee:ff:00:11"
        """
        self.short_addr = short_addr    # e.g. "0x1A2B" — used for all commands
        self.ieee_addr  = ieee_addr     # e.g. "aa:bb:..." — used for persistent storage
        self.name       = f"Device {short_addr}"  # Default name, can be changed by user

        # endpoint → list of cluster IDs that endpoint supports
        # e.g. {1: [6, 8, 768]} means endpoint 1 supports on/off, level, color
        self.endpoints: dict[int, list[int]] = {}

        # Current known state of each attribute
        # Key: (endpoint, cluster_id, attr_id) tuple
        # Value: the GUI-converted value
        # e.g. {(1, 6, 0): True, (1, 8, 0): 0.75}
        self.state: dict[tuple, object] = {}

    def add_endpoint(self, endpoint: int, cluster_ids: list[int]):
        """Called when we receive a DEVICE_DESCRIPTOR message for this device."""
        self.endpoints[endpoint] = cluster_ids
        print(f"  Device {self.short_addr} endpoint {endpoint}: clusters {cluster_ids}")

    def update_state(self, endpoint: int, cluster_id: int, attr_id: int, raw_value):
        """
        Called when we receive an ATTR_REPORT for this device.
        Converts the raw Zigbee value to a GUI-friendly value and stores it.

        Returns the converted value so callers can use it directly.
        """
        converted = raw_value  # Default: no conversion

        # Look up the cluster and attribute definitions
        cluster_def = CLUSTER_DEFINITIONS.get(cluster_id)
        if cluster_def:
            attr_def = cluster_def["attributes"].get(attr_id)
            if attr_def:
                converted = convert_raw_value(raw_value, attr_def)

        key = (endpoint, cluster_id, attr_id)
        self.state[key] = converted
        return converted

    def get_capabilities(self) -> list[dict]:
        """
        Returns a flat list of all capabilities this device has.
        Each capability is a dict describing one controllable/readable variable.

        This is what the GUI factory reads to decide what controls to render.

        Example return value:
        [
          {"endpoint": 1, "cluster": 6, "attr": 0, "name": "on_off",
           "type": "bool", "writable": True, "ui_type": "toggle",
           "current_value": True},
          {"endpoint": 1, "cluster": 8, "attr": 0, "name": "current_level",
           "type": "uint8", "writable": True, "ui_type": "slider",
           "current_value": 0.75},
        ]
        """
        capabilities = []
        for endpoint, cluster_ids in self.endpoints.items():
            for cluster_id in cluster_ids:
                cluster_def = CLUSTER_DEFINITIONS.get(cluster_id)
                if not cluster_def:
                    # Unknown cluster — we don't know what it does, skip for now
                    continue
                for attr_id, attr_def in cluster_def["attributes"].items():
                    key = (endpoint, cluster_id, attr_id)
                    cap = {
                        "endpoint":      endpoint,
                        "cluster":       cluster_id,
                        "attr":          attr_id,
                        "cluster_name":  cluster_def["name"],
                        "name":          attr_def["name"],
                        "type":          attr_def["type"],
                        "writable":      attr_def["writable"],
                        "ui_type":       attr_def.get("ui_type", "display"),
                        "ui_range":      attr_def.get("ui_range", (0, 1)),
                        "current_value": self.state.get(key, None),
                    }
                    capabilities.append(cap)
        return capabilities

    def __repr__(self):
        n_clusters = sum(len(c) for c in self.endpoints.values())
        return f"<DeviceModel {self.short_addr} ({n_clusters} clusters)>"


class ZigbeeGateway(QThread):
    """
    Background QThread that manages the serial connection to the ESP32 coordinator.

    Runs a blocking readline loop. When a complete JSON line arrives, it parses
    it and emits the appropriate Qt signal. Other parts of the app (DeviceManager,
    GUI) connect to these signals to receive updates.

    Never call Zigbee API functions from this thread — it's just I/O and parsing.
    The actual device model updates happen in DeviceManager (main thread via signals).
    """

    # ── Qt Signals ─────────────────────────────────────────────────────────────
    # These are class-level attributes. Qt requires signals to be defined here.
    # Any object can connect a slot (function) to these signals.

    # Emitted when the ESP32 reports the coordinator is up and running
    # Args: pan_id (str), channel (int), coordinator_addr (str)
    gateway_ready = pyqtSignal(str, int, str)

    # Emitted when the network opens/closes for pairing
    # Args: is_open (bool), seconds (int, 0 when closed)
    pairing_status_changed = pyqtSignal(bool, int)

    # Emitted the moment a new device announces itself
    # Args: short_addr (str), ieee_addr (str)
    device_joined = pyqtSignal(str, str)

    # Emitted when we learn what a device can do (after descriptor query)
    # Args: short_addr (str), endpoint (int), cluster_ids (list of ints)
    device_descriptor_received = pyqtSignal(str, int, list)

    # Emitted when any attribute value is reported (scheduled report or read response)
    # Args: short_addr (str), endpoint (int), cluster_id (int), attr_id (int),
    #       type_str (str), raw_value (int)
    attribute_reported = pyqtSignal(str, int, int, int, str, int)

    # Emitted for ACKs and errors from the ESP32 (useful for UI feedback)
    # Args: is_ok (bool), detail (str)
    command_ack = pyqtSignal(bool, str)

    # Emitted when the serial connection is lost or re-established
    # Args: is_connected (bool)
    connection_status_changed = pyqtSignal(bool)

    def __init__(self, port: str = "/dev/ttyACM0", baud: int = 115200):
        """
        Args:
            port: Serial port device path.
                  USB Serial JTAG on Pi usually appears as /dev/ttyACM0 or /dev/ttyUSB0.
                  When wired to GPIO UART pins, it will be /dev/ttyAMA0 or /dev/ttyS0.
                  Check `ls /dev/tty*` before and after plugging in the ESP32.
            baud: Baud rate. 115200 is the standard default.
                  Must match what the ESP32's UART is configured for.
        """
        super().__init__()
        self.port    = port
        self.baud    = baud
        self.running = True

        # The serial.Serial object — None until successfully opened
        self._serial: serial.Serial | None = None

        # Lock to protect serial writes (reads happen only in this thread,
        # but writes can be called from the main thread via send_command())
        self._write_lock = threading.Lock()

        print(f"ZigbeeGateway: will connect to {port} at {baud} baud")

    # ── Background Thread: Reading from ESP32 ──────────────────────────────────

    def run(self):
        """
        Main loop of the background thread.
        Keeps trying to open the serial port, reads lines, parses JSON.
        """
        print("ZigbeeGateway thread started")

        while self.running:
            # Try to open the serial port. If it fails (ESP32 not plugged in yet),
            # wait and retry rather than crashing.
            if not self._connect():
                print(f"ZigbeeGateway: could not open {self.port}, retrying in 3s...")
                time.sleep(3)
                continue

            # Serial port is open — read lines until connection drops
            self._read_loop()

        print("ZigbeeGateway thread stopped")

    def _connect(self) -> bool:
        """
        Attempts to open the serial port.
        Returns True on success, False on failure.
        """
        try:
            self._serial = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                timeout=1.0,    # 1 second read timeout — prevents blocking forever
                                # if no data arrives. run() loop will keep calling readline().
            )
            print(f"ZigbeeGateway: connected to {self.port}")
            self.connection_status_changed.emit(True)
            return True
        except serial.SerialException as e:
            print(f"ZigbeeGateway: serial open failed: {e}")
            self._serial = None
            return False

    def _read_loop(self):
        """
        Blocking loop that reads one line at a time from the ESP32.
        Each line should be a complete JSON message ending in \\n.
        Exits when the serial connection drops or self.running becomes False.
        """
        while self.running:
            try:
                # readline() blocks until \\n or timeout (1s, set in _connect)
                raw_bytes = self._serial.readline()

                if not raw_bytes:
                    # Timeout — no data in 1 second. Normal — just loop again.
                    continue

                # Decode bytes to string and strip whitespace/newlines
                line = raw_bytes.decode("utf-8", errors="replace").strip()

                if not line:
                    continue  # Empty line — ignore

                # Parse and dispatch the JSON message
                self._parse_message(line)

            except serial.SerialException as e:
                # Connection dropped — USB unplugged, ESP32 reset, etc.
                print(f"ZigbeeGateway: serial error: {e}")
                self.connection_status_changed.emit(False)
                if self._serial:
                    try:
                        self._serial.close()
                    except Exception:
                        pass
                    self._serial = None
                break  # Exit read loop — run() will try to reconnect

            except UnicodeDecodeError as e:
                # Garbage bytes on the line — skip and continue
                print(f"ZigbeeGateway: decode error (garbage bytes?): {e}")
                continue

    def _parse_message(self, line: str):
        """
        Parse one JSON line from the ESP32 and emit the appropriate signal.

        Args:
            line: A single JSON string, e.g. '{"cmd":"GATEWAY_READY","pan_id":"0x1A2B",...}'
        """
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

        # ── Route to the appropriate signal ──────────────────────────────────

        if cmd == "GATEWAY_READY":
            # {"cmd":"GATEWAY_READY","pan_id":"0x1A2B","channel":13,"addr":"0x0000"}
            pan_id  = msg.get("pan_id", "0x0000")
            channel = msg.get("channel", 0)
            addr    = msg.get("addr", "0x0000")
            print(f"  Gateway ready: PAN={pan_id} Ch={channel} Addr={addr}")
            self.gateway_ready.emit(pan_id, channel, addr)

        elif cmd == "NETWORK_OPEN":
            # {"cmd":"NETWORK_OPEN","seconds":180}
            seconds = msg.get("seconds", 0)
            self.pairing_status_changed.emit(True, seconds)

        elif cmd == "NETWORK_CLOSED":
            # {"cmd":"NETWORK_CLOSED"}
            self.pairing_status_changed.emit(False, 0)

        elif cmd == "DEVICE_JOINED":
            # {"cmd":"DEVICE_JOINED","addr":"0x3C4D","ieee":"aa:bb:cc:dd:ee:ff:00:11"}
            addr = msg.get("addr", "0x0000")
            ieee = msg.get("ieee", "00:00:00:00:00:00:00:00")
            print(f"  New device: {addr} (IEEE: {ieee})")
            self.device_joined.emit(addr, ieee)

        elif cmd == "DEVICE_DESCRIPTOR":
            # {"cmd":"DEVICE_DESCRIPTOR","addr":"0x3C4D","endpoint":1,"clusters":[6,8,768]}
            addr     = msg.get("addr", "0x0000")
            endpoint = msg.get("endpoint", 1)
            clusters = msg.get("clusters", [])
            # Filter to only clusters we know about
            known    = [c for c in clusters if c in CLUSTER_DEFINITIONS]
            unknown  = [c for c in clusters if c not in CLUSTER_DEFINITIONS]
            if unknown:
                print(f"  Unknown clusters (add to CLUSTER_DEFINITIONS): {[hex(c) for c in unknown]}")
            print(f"  Descriptor for {addr} ep{endpoint}: known={[hex(c) for c in known]}")
            self.device_descriptor_received.emit(addr, endpoint, clusters)

        elif cmd == "ATTR_REPORT":
            # {"cmd":"ATTR_REPORT","addr":"0x3C4D","endpoint":1,
            #  "cluster":6,"attr":0,"type":"bool","value":1}
            addr      = msg.get("addr", "0x0000")
            endpoint  = msg.get("endpoint", 1)
            cluster   = msg.get("cluster", 0)
            attr      = msg.get("attr", 0)
            type_str  = msg.get("type", "uint8")
            raw_value = msg.get("value", 0)
            self.attribute_reported.emit(addr, endpoint, cluster, attr, type_str, raw_value)

        elif cmd == "CMD_ACK":
            # {"cmd":"CMD_ACK","status":"ok","detail":"network_opened"}
            is_ok  = msg.get("status") == "ok"
            detail = msg.get("detail", "")
            self.command_ack.emit(is_ok, detail)

        elif cmd == "ERROR":
            # {"cmd":"ERROR","detail":"something_went_wrong"}
            detail = msg.get("detail", "unknown_error")
            print(f"  ESP32 error: {detail}")
            self.command_ack.emit(False, detail)

        else:
            print(f"ZigbeeGateway: unhandled cmd: {cmd}")

    # ── Main Thread: Sending Commands to ESP32 ─────────────────────────────────
    #
    # These methods are called from the main thread (GUI events, button clicks).
    # They're thread-safe because we use _write_lock.

    def send_command(self, cmd_dict: dict) -> bool:
        """
        Send a JSON command to the ESP32 over serial.

        Args:
            cmd_dict: Python dict that will be serialized to JSON.
                      Must include a "cmd" key.

        Returns:
            True if the write succeeded, False if not connected or write failed.
        """
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

    def open_network(self, duration_seconds: int = 180) -> bool:
        """
        Tell the ESP32 to open the Zigbee network for pairing.

        Args:
            duration_seconds: How long to allow joining (max 254). Default 3 minutes.

        Returns:
            True if the command was sent successfully.
        """
        return self.send_command({
            "cmd":      "OPEN_NETWORK",
            "duration": min(duration_seconds, 254)
        })

    def close_network(self) -> bool:
        """
        Tell the ESP32 to close the network immediately (stop pairing).
        """
        return self.send_command({"cmd": "CLOSE_NETWORK"})

    def set_attribute(self, addr: str, endpoint: int, cluster: int,
                       attr: int, attr_type: str, value) -> bool:
        """
        Send a ZCL Write Attribute command to a device.
        Use this to control a device: turn on a light, set brightness, etc.

        Args:
            addr:      Device short address, e.g. "0x1A2B"
            endpoint:  Endpoint number on the device, usually 1
            cluster:   ZCL cluster ID (int), e.g. 6 for On/Off
            attr:      ZCL attribute ID (int), e.g. 0 for on_off attribute
            attr_type: Type string matching what ESP32 expects:
                       "bool", "uint8", "uint16", "int16"
            value:     The raw Zigbee value to set (already converted from UI units)

        Returns:
            True if the command was sent successfully.

        Example: Turn on a light at address "0x1A2B", endpoint 1:
            gateway.set_attribute("0x1A2B", 1, 6, 0, "bool", 1)
        """
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
        """
        Higher-level version of set_attribute() that accepts GUI values.
        Automatically looks up the attribute definition and converts the UI value
        to the raw Zigbee value.

        Args:
            addr:      Device short address
            endpoint:  Endpoint number
            cluster:   ZCL cluster ID
            attr:      ZCL attribute ID
            ui_value:  The value as the GUI represents it (e.g., float 0.0-1.0 for brightness)

        Returns:
            True if the command was sent successfully.

        Example: Set brightness to 75% on a dimmable light:
            gateway.set_attribute_from_ui("0x1A2B", 1, 8, 0, 0.75)
            # Internally converts 0.75 → 190 (75% of 254) and sends uint8
        """
        cluster_def = CLUSTER_DEFINITIONS.get(cluster)
        if not cluster_def:
            print(f"ZigbeeGateway: unknown cluster {cluster:#06x}")
            return False

        attr_def = cluster_def["attributes"].get(attr)
        if not attr_def:
            print(f"ZigbeeGateway: unknown attr {attr} in cluster {cluster:#06x}")
            return False

        if not attr_def.get("writable", False):
            print(f"ZigbeeGateway: attribute {attr_def['name']} is read-only")
            return False

        raw_value = convert_ui_value_to_raw(ui_value, attr_def)
        return self.set_attribute(addr, endpoint, cluster, attr,
                                   attr_def["type"], raw_value)

    def read_attribute(self, addr: str, endpoint: int, cluster: int, attr: int) -> bool:
        """
        Request the current value of an attribute from a device.
        The response comes back asynchronously via the attribute_reported signal.

        Args:
            addr:     Device short address
            endpoint: Endpoint number
            cluster:  ZCL cluster ID
            attr:     ZCL attribute ID

        Returns:
            True if the command was sent successfully.
        """
        return self.send_command({
            "cmd":      "READ_ATTR",
            "addr":     addr,
            "endpoint": endpoint,
            "cluster":  cluster,
            "attr":     attr,
        })

    # ── Cleanup ────────────────────────────────────────────────────────────────

    def stop(self):
        """
        Stop the background thread and close the serial port.
        Call this from DeviceManager.stop() before the app exits.
        """
        print("ZigbeeGateway: stopping...")
        self.running = False

        # Close the serial port to unblock any pending readline()
        if self._serial and self._serial.is_open:
            try:
                self._serial.close()
            except Exception:
                pass

        # Wait for the thread to finish (with a reasonable timeout)
        self.wait(3000)  # 3 second timeout
        print("ZigbeeGateway: stopped")