"""
device_manager.py  (UPDATED — zero-config support)

Changes from original:
  - Added gateway_ready_received signal for network status widget
  - Added config_requested signal for unconfigured ESP32 detection
  - Added send_configure() method
  - _on_config_requested handler emits to GUI
"""

from PyQt6.QtCore import QObject, pyqtSignal

from Raspberry_pi_CC.sensors.sht41 import TempHumidSensor
from zigbee_gateway import ZigbeeGateway, DeviceModel, CLUSTER_DEFINITIONS


class DeviceManager(QObject):

    # ── Signals to the GUI ─────────────────────────────────────────────────────

    device_added = pyqtSignal(object)
    device_state_changed = pyqtSignal(str, str, object)
    gateway_connection_changed = pyqtSignal(bool)

    # Emitted when ESP32 sends GATEWAY_READY
    # Args: pan_id (str), channel (int), coordinator_addr (str)
    gateway_ready_received = pyqtSignal(str, int, str)

    # Emitted when ESP32 sends WAITING_FOR_CONFIG (needs setup)
    # Args: mac (str), pan_id (str)
    config_requested = pyqtSignal(str, str)

    pairing_status_changed = pyqtSignal(bool, int)

    def __init__(self, zigbee_port: str = "/dev/ttyACM0", zigbee_baud: int = 115200):
        super().__init__()

        self._devices: dict[str, DeviceModel] = {}

        # ── SHT41 sensor ──────────────────────────────────────────────────
        self.temperature = None
        self.humidity    = None
        self._temp_humid_sensor = TempHumidSensor(interval=15)
        self._temp_humid_sensor.data_updated.connect(self._on_temp_humid_update)
        self._temp_humid_sensor.start()

        # ── Zigbee Gateway ────────────────────────────────────────────────
        self._gateway = ZigbeeGateway(port=zigbee_port, baud=zigbee_baud)

        self._gateway.gateway_ready.connect(self._on_gateway_ready)
        self._gateway.pairing_status_changed.connect(self._on_pairing_status)
        self._gateway.device_joined.connect(self._on_device_joined)
        self._gateway.device_descriptor_received.connect(self._on_device_descriptor)
        self._gateway.attribute_reported.connect(self._on_attribute_reported)
        self._gateway.connection_status_changed.connect(self.gateway_connection_changed)
        self._gateway.config_requested.connect(self._on_config_requested)

        self._gateway.start()
        print("DeviceManager initialized")

    # ── Sensor ─────────────────────────────────────────────────────────────────

    def _on_temp_humid_update(self, temp: float, humid: float):
        self.temperature = temp
        self.humidity    = humid

    # ── Gateway Slots ──────────────────────────────────────────────────────────

    def _on_gateway_ready(self, pan_id: str, channel: int, addr: str):
        print(f"DeviceManager: Gateway ready — PAN={pan_id} Ch={channel}")
        self.gateway_ready_received.emit(pan_id, channel, addr)

    def _on_config_requested(self, mac: str, pan_id: str):
        """ESP32 is unconfigured — forward to GUI to show setup dialog."""
        print(f"DeviceManager: ESP32 needs configuration (MAC={mac}, PAN={pan_id})")
        self.config_requested.emit(mac, pan_id)

    def _on_pairing_status(self, is_open: bool, seconds: int):
        if is_open:
            print(f"DeviceManager: Pairing open for {seconds}s")
        else:
            print("DeviceManager: Pairing closed")
        self.pairing_status_changed.emit(is_open, seconds)

    def _on_device_joined(self, short_addr: str, ieee_addr: str):
        if short_addr not in self._devices:
            print(f"DeviceManager: New device: {short_addr}")
            self._devices[short_addr] = DeviceModel(short_addr, ieee_addr)
        else:
            print(f"DeviceManager: Device {short_addr} rejoined")

    def _on_device_descriptor(self, short_addr: str, endpoint: int, cluster_ids: list):
        if short_addr not in self._devices:
            self._devices[short_addr] = DeviceModel(short_addr, "unknown")
        device = self._devices[short_addr]
        device.add_endpoint(endpoint, cluster_ids)
        self.device_added.emit(device)
        self._read_all_attributes(device, endpoint, cluster_ids)

    def _on_attribute_reported(self, short_addr: str, endpoint: int,
                                 cluster: int, attr: int, type_str: str, raw_value: int):
        device = self._devices.get(short_addr)
        if not device:
            return
        converted_value = device.update_state(endpoint, cluster, attr, raw_value)
        capability_name = f"cluster_{cluster}_attr_{attr}"
        cluster_def = CLUSTER_DEFINITIONS.get(cluster)
        if cluster_def:
            attr_def = cluster_def["attributes"].get(attr)
            if attr_def:
                capability_name = attr_def["name"]
        self.device_state_changed.emit(short_addr, capability_name, converted_value)

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _read_all_attributes(self, device, endpoint, cluster_ids):
        for cluster_id in cluster_ids:
            cluster_def = CLUSTER_DEFINITIONS.get(cluster_id)
            if not cluster_def:
                continue
            for attr_id in cluster_def["attributes"]:
                self._gateway.read_attribute(device.short_addr, endpoint, cluster_id, attr_id)

    # ── Public Interface ───────────────────────────────────────────────────────

    def get_sensor(self):
        return self._temp_humid_sensor

    def get_all_devices(self):
        return list(self._devices.values())

    def get_device(self, short_addr: str):
        return self._devices.get(short_addr)

    def open_pairing(self, duration: int = 180):
        self._gateway.open_network(duration)

    def close_pairing(self):
        self._gateway.close_network()

    def send_configure(self, channel: int, room_name: str):
        """
        Send CONFIGURE command to an unconfigured ESP32.
        Called by the GUI after the user fills in the config dialog.
        """
        print(f"DeviceManager: Sending CONFIGURE — room=\"{room_name}\", ch={channel}")
        self._gateway.send_configure(channel, room_name)

    def set_device_attribute(self, short_addr: str, endpoint: int,
                              cluster: int, attr: int, ui_value) -> bool:
        return self._gateway.set_attribute_from_ui(short_addr, endpoint, cluster, attr, ui_value)

    def get_temperature(self):
        return self.temperature

    def get_humidity(self):
        return self.humidity

    def stop(self):
        print("DeviceManager: stopping...")
        self._temp_humid_sensor.stop()
        self._gateway.stop()
        print("DeviceManager: stopped")