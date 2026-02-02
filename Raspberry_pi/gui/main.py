import sys

from PyQt6.QtWidgets import (QApplication, 
                             QMainWindow, 
                             QWidget, 
                             QVBoxLayout, 
                             QHBoxLayout, 
                             QLabel, 
                             QPushButton, 
                             QScrollArea)
from PyQt6.QtCore import (Qt,
                        QEvent)
from PyQt6.QtGui import (QFont,
                        QCursor)

from top_layer_buttons import TopLayerButtons
from device_list import DeviceListLayout
from environment import EnvironmentLayout

class MainWindow(QMainWindow):    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
        # TODO: Hide the mouse cursor
        #self.setCursor(Qt.CursorShape.BlankCursor)

    def init_ui(self):
        

        Title = "Raspberry Pi Zigbee Controller" #TODO Make Dynamic from user input.


        self.setWindowTitle(Title)
        self.showFullScreen()
        self.setStyleSheet("background-color: #2c3e50;")  # Dark blue-grey background
        

        Central_widget = QWidget()
        main_layout = QVBoxLayout()

        Central_widget.setLayout(main_layout)

        self.setCentralWidget(Central_widget)

        ###### Title ######
        title_widget = QLabel(Title)
        title_widget.setFont(QFont('Arial', 20, QFont.Weight.Bold))
        title_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_widget.setStyleSheet("color: #ecf0f1; padding: 20px;")  # Light grey text
        main_layout.addWidget(title_widget)

        main_layout.addSpacing(20)

        top_layer_buttons = TopLayerButtons()
        main_layout.addLayout(top_layer_buttons)

        main_layout.addSpacing(30)

        Devices_layout = QHBoxLayout()
        Devices_layout.setSpacing(15)
        device_list_layout = DeviceListLayout()
        envi_area_layout = EnvironmentLayout()
        
        Devices_layout.addLayout(device_list_layout)
        Devices_layout.setStretch(Devices_layout.count() - 1, 1)  # device_list_layout gets 50%

        Devices_layout.addLayout(envi_area_layout)
        Devices_layout.setStretch(Devices_layout.count() - 1, 1)  # environment_area_layout gets 50%


        main_layout.addLayout(Devices_layout)

    ### TODO: Temperary - Escape key to exit full screen ###
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
        


def main():

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())



if __name__ == '__main__':
    main()


##3 TODO Implement MQTT functionality ###'''
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