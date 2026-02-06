import sys
import os

### Adjust sys.path to include project root | Only needed to launch from VS Code Run button ###
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PyQt6.QtWidgets import QApplication
from Raspberry_pi_CC.gui.main_window import MainWindow
#from Raspberry_pi_CC.gui.Functionality.temp_humid_monitor import tempHumidMonitor

def main():

    app = QApplication(sys.argv)
    #temp_humid_monitor = tempHumidMonitor()
    window = MainWindow(None)
    window.show()

    try:
        sys.exit(app.exec())
    finally:
        #temp_humid_monitor.stop() 
        pass # Stop the temp/humid monitor thread on exit

if __name__ == '__main__':
    main()


### TODO: Implement MQTT functionality ###'''
            ### MQTT code snippet ###
'''
        def connect_mqtt(self): 
        def on_connect(client, userdata, connect_flags, reason_code, properties):
            if reason_code == 0:
                self.log("✓ Connected to MQTT broker")
                client.subscribe("zigbee/#")
            else:
                self.log(f"✗ MQTT connection failed (code {reason_code})")

        def on_message(client, userdata, msg):
            try:
                topic = msg.topic
                payload = json.loads(msg.payload.decode())

                if topic == "zigbee/bridge/network":
                    self.update_network_info(payload)
                elif topic == "zigbee/bridge/devices":
                    pass  # Could refresh full list here
                elif "/info" in topic:
                    ieee = topic.split('/')[1]
                    self.add_device(ieee, payload)
                elif "/state" in topic:
                    ieee = topic.split('/')[1]
                    self.update_device_state(ieee, payload)

            except Exception as e:
                self.log(f"Error processing message: {e}")

        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqtt_client.on_connect = on_connect
        self.mqtt_client.on_message = on_message

        try:
            self.mqtt_client.connect("localhost", 1883, 60)
            threading.Thread(target=self.mqtt_client.loop_forever, daemon=True).start()
        except Exception as e:
            self.log(f"Failed to connect to MQTT: {e}")
'''
            ### End of MQTT code snippet ###