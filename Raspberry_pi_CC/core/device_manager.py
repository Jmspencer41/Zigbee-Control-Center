"""
device_manager.py

Central registry for all devices and sensors in the system.
This is the "model" in the MVC sense — it holds the state, the GUI reads from it.

Responsibilities:
  - Own the ZigbeeGateway thread and connect to its signals
  - Own the SHT41 sensor thread
  - Maintain a registry of all known Zigbee devices (DeviceModel objects)
  - Emit signals when devices are added or their state changes
  - Provide the send-command interface so the GUI doesn't talk to ZigbeeGateway directly

The GUI should NEVER import ZigbeeGateway or DeviceModel directly.
It talks only to DeviceManager.
"""

from PyQt6.QtCore import QObject, pyqtSignal

from Raspberry_pi_CC.sensors.sht41 import TempHumidSensor
from zigbee_gateway import ZigbeeGateway, DeviceModel, CLUSTER_DEFINITIONS


class DeviceManager(QObject):
    """
    Singleton-style manager that owns all hardware interfaces.
    Instantiated once in MainWindow and passed around as needed.
    """

    # ── Signals to the GUI ─────────────────────────────────────────────────────

    # A brand-new device has been discovered and its model is ready
    # The GUI connects to this to add a new button/panel to the device list
    # Args: DeviceModel instance
    device_added = pyqtSignal(object)

    # An existing device's state has changed (attribute update)
    # The GUI connects to this to update displayed values
    # Args: short_addr (str), capability_name (str), new_value
    device_state_changed = pyqtSignal(str, str, object)

    # The Zigbee gateway connection status changed
    # Args: is_connected (bool)
    gateway_connection_changed = pyqtSignal(bool)

    # Pairing window opened or closed
    # Args: is_open (bool), seconds_remaining (int)
    pairing_status_changed = pyqtSignal(bool, int)

    def __init__(self, zigbee_port: str = "/dev/ttyACM0", zigbee_baud: int = 115200):
        super().__init__()

        # ── Device Registry ────────────────────────────────────────────────────
        # Maps short_addr (str) → DeviceModel
        # e.g. {"0x1A2B": <DeviceModel ...>, "0x3C4D": <DeviceModel ...>}
        self._devices: dict[str, DeviceModel] = {}

        # ── SHT41 Temperature/Humidity Sensor ─────────────────────────────────
        self.temperature = None
        self.humidity    = None

        self._temp_humid_sensor = TempHumidSensor(interval=15)
        self._temp_humid_sensor.data_updated.connect(self._on_temp_humid_update)
        self._temp_humid_sensor.start()

        # ── Zigbee Gateway ─────────────────────────────────────────────────────
        self._gateway = ZigbeeGateway(port=zigbee_port, baud=zigbee_baud)

        # Connect all ZigbeeGateway signals to our handler slots
        self._gateway.gateway_ready.connect(self._on_gateway_ready)
        self._gateway.pairing_status_changed.connect(self._on_pairing_status)
        self._gateway.device_joined.connect(self._on_device_joined)
        self._gateway.device_descriptor_received.connect(self._on_device_descriptor)
        self._gateway.attribute_reported.connect(self._on_attribute_reported)
        self._gateway.connection_status_changed.connect(self.gateway_connection_changed)

        # Start the background serial reader thread
        self._gateway.start()

        print("DeviceManager initialized")

    # ── SHT41 Sensor Slots ─────────────────────────────────────────────────────

    def _on_temp_humid_update(self, temp: float, humid: float):
        """Called automatically when SHT41 emits new data."""
        self.temperature = temp
        self.humidity    = humid

    # ── ZigbeeGateway Signal Slots ─────────────────────────────────────────────
    #
    # These run in the MAIN THREAD because Qt automatically queues cross-thread
    # signal emissions. You can safely update UI or data structures here.

    def _on_gateway_ready(self, pan_id: str, channel: int, addr: str):
        """
        The ESP32 coordinator is up and the Zigbee network is active.
        This fires once after boot when the network is formed or restored.
        """
        print(f"DeviceManager: Gateway ready — PAN={pan_id} Ch={channel} Addr={addr}")
        # TODO: Update a status panel in the GUI to show "Zigbee: Connected"

    def _on_pairing_status(self, is_open: bool, seconds: int):
        """Network opened or closed for pairing."""
        if is_open:
            print(f"DeviceManager: Pairing window open for {seconds}s")
        else:
            print("DeviceManager: Pairing window closed")
        self.pairing_status_changed.emit(is_open, seconds)

    def _on_device_joined(self, short_addr: str, ieee_addr: str):
        """
        A device announced itself on the network.
        Create a DeviceModel for it and add it to our registry.
        We don't emit device_added yet — we wait until we have the descriptor
        so the GUI has full capability information to render.
        """
        if short_addr not in self._devices:
            print(f"DeviceManager: New device joined: {short_addr}")
            self._devices[short_addr] = DeviceModel(short_addr, ieee_addr)
        else:
            # Device rejoined after power cycle — it already exists in our registry
            print(f"DeviceManager: Device {short_addr} rejoined (already known)")

    def _on_device_descriptor(self, short_addr: str, endpoint: int, cluster_ids: list):
        """
        We now know what a device can do.
        Update its model and emit device_added so the GUI can render it.
        """
        if short_addr not in self._devices:
            # Descriptor arrived before JOIN (shouldn't happen, but handle it gracefully)
            print(f"DeviceManager: Got descriptor for unknown device {short_addr}, creating model")
            self._devices[short_addr] = DeviceModel(short_addr, "unknown")

        device = self._devices[short_addr]
        device.add_endpoint(endpoint, cluster_ids)

        # Emit device_added — the GUI creates a panel for this device
        # We emit every time we get a descriptor update, not just on first join.
        # The GUI should handle duplicate add gracefully (check if panel already exists).
        print(f"DeviceManager: Device {short_addr} descriptor ready — notifying GUI")
        self.device_added.emit(device)

        # Immediately read all known attributes from the device so we have
        # an initial state to display. Otherwise the GUI shows "---" until
        # the device spontaneously reports.
        self._read_all_attributes(device, endpoint, cluster_ids)

    def _on_attribute_reported(self, short_addr: str, endpoint: int,
                                 cluster: int, attr: int, type_str: str, raw_value: int):
        """
        A device reported an attribute value (either spontaneously or in response to READ_ATTR).
        Update the device model and notify the GUI.
        """
        device = self._devices.get(short_addr)
        if not device:
            print(f"DeviceManager: Attribute report from unknown device {short_addr}")
            return

        # Convert and store the value in the device model
        converted_value = device.update_state(endpoint, cluster, attr, raw_value)

        # Find the capability name for this attribute (for the GUI to use as a key)
        capability_name = f"cluster_{cluster}_attr_{attr}"  # fallback
        cluster_def = CLUSTER_DEFINITIONS.get(cluster)
        if cluster_def:
            attr_def = cluster_def["attributes"].get(attr)
            if attr_def:
                capability_name = attr_def["name"]

        print(f"DeviceManager: {short_addr} {capability_name} = {converted_value}")
        self.device_state_changed.emit(short_addr, capability_name, converted_value)

    # ── Internal Helpers ────────────────────────────────────────────────────────

    def _read_all_attributes(self, device: DeviceModel, endpoint: int, cluster_ids: list):
        """
        After a device is discovered, request the current value of every attribute
        we know about. This populates the initial display without waiting for
        the device to spontaneously report.
        """
        for cluster_id in cluster_ids:
            cluster_def = CLUSTER_DEFINITIONS.get(cluster_id)
            if not cluster_def:
                continue
            for attr_id in cluster_def["attributes"]:
                self._gateway.read_attribute(device.short_addr, endpoint, cluster_id, attr_id)

    # ── Public Interface for the GUI ───────────────────────────────────────────
    #
    # The GUI calls these methods. It never talks to ZigbeeGateway directly.

    def get_sensor(self) -> TempHumidSensor:
        """Return the SHT41 sensor so environment panel can connect to its signals."""
        return self._temp_humid_sensor

    def get_all_devices(self) -> list[DeviceModel]:
        """Return all currently known devices. Used to populate GUI on startup."""
        return list(self._devices.values())

    def get_device(self, short_addr: str) -> DeviceModel | None:
        """Return a specific device by address, or None if not found."""
        return self._devices.get(short_addr)

    def open_pairing(self, duration: int = 180):
        """
        Open the Zigbee network for pairing new devices.
        Called by the Pair Devices button in the GUI.
        """
        print(f"DeviceManager: Opening pairing window for {duration}s")
        self._gateway.open_network(duration)

    def close_pairing(self):
        """Close the pairing window immediately."""
        print("DeviceManager: Closing pairing window")
        self._gateway.close_network()

    def set_device_attribute(self, short_addr: str, endpoint: int,
                              cluster: int, attr: int, ui_value) -> bool:
        """
        Send a control command to a device, using GUI-unit values.
        The ZigbeeGateway handles the unit conversion.

        Args:
            short_addr: Device address, e.g. "0x1A2B"
            endpoint:   Endpoint number (usually 1)
            cluster:    ZCL cluster ID (e.g. 6 for On/Off, 8 for Level)
            attr:       ZCL attribute ID (e.g. 0)
            ui_value:   Value in GUI units (e.g. True/False for on/off, 0.75 for 75% brightness)

        Returns:
            True if the command was sent successfully.

        Example — turn on a light:
            device_manager.set_device_attribute("0x1A2B", 1, 6, 0, True)

        Example — set brightness to 50%:
            device_manager.set_device_attribute("0x1A2B", 1, 8, 0, 0.5)
        """
        return self._gateway.set_attribute_from_ui(short_addr, endpoint, cluster, attr, ui_value)

    def get_temperature(self) -> float | None:
        return self.temperature

    def get_humidity(self) -> float | None:
        return self.humidity

    def stop(self):
        """Stop all background threads. Called from MainWindow.closeEvent()."""
        print("DeviceManager: stopping...")
        self._temp_humid_sensor.stop()
        self._gateway.stop()
        print("DeviceManager: stopped")