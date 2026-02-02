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

        #scrollable_area = QScrollArea() # Old scroll area using custom class for touch screen now.
        
        scrollable_area = TouchScrollArea()
        scrollable_area.setStyleSheet("background-color: #89c2fa; border-radius: 15px;")  

        device_list_widget = QWidget()
        device_list_layout = QVBoxLayout()
        device_list_widget.setLayout(device_list_layout)

        # Example device buttons TODO: Make dynamic from actual devices
        for i in range(20):
            device_button = create_device_button(f"Device {i+1}")
            device_list_layout.addWidget(device_button)
            device_list_layout.addSpacing(10)

        scrollable_area.setWidget(device_list_widget)
        scrollable_area.setWidgetResizable(True)

        envi_area_widget = QWidget()
        envi_area_widget.setStyleSheet("background-color: #89c2fa; border-radius: 15px;")    
        envi_area_layout = QVBoxLayout()
        envi_area_widget.setLayout(envi_area_layout)

        ### TODO: Make dynamic from actual environment data ###
        temp_humid_layout = QHBoxLayout()
        temp_humid_layout.setSpacing(20)
        temp_humid_layout.setSizeConstraint(QHBoxLayout.SizeConstraint.SetFixedSize)

        ### TODO: Replace with actual sensor data ###
        temp = 22  # Placeholder temperature
        humid = 45  # Placeholder humidity
        
        temp_layout = QVBoxLayout()
        temp_label_title = QLabel("Temperature")
        temp_label_title.setFont(QFont('Arial', 20, QFont.Weight.Bold))
        temp_label_title.setStyleSheet("color: #2c3e50;")
        temp_layout.addWidget(temp_label_title)
        temp_humid_layout.addLayout(temp_layout)

        humid_layout = QVBoxLayout()
        humid_label_title = QLabel("Humidity")
        humid_label_title.setFont(QFont('Arial', 20, QFont.Weight.Bold))
        humid_label_title.setStyleSheet("color: #2c3e50;")  
        humid_layout.addWidget(humid_label_title)
        temp_humid_layout.addLayout(humid_layout)

        temp_label = QLabel(f"{temp}°C")
        temp_label.setFont(QFont('Arial', 24))
        temp_label.setStyleSheet("color: #2c3e50;") 

        temp_layout.addWidget(temp_label)
        
        humid_label = QLabel(f"{humid}%")
        humid_label.setFont(QFont('Arial', 24))
        humid_label.setStyleSheet("color: #2c3e50;")

        humid_layout.addWidget(humid_label)

        envi_area_layout.addLayout(temp_humid_layout)
        
        Lights_button = QPushButton('Toggle Lights')
        Lights_button.setMinimumHeight(80)
        Lights_button.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        #Lights_button.clicked.connect(self.on_button1_clicked)
        Lights_button.setStyleSheet("""
            QPushButton {
                background-color: #f1c40f;
                color: #2c3e50;
                border-radius: 30px;
                padding: 15px;
            }
            QPushButton:pressed {
                background-color: #b7950b;
            }
        """)
        envi_area_layout.addWidget(Lights_button)

        Devices_layout.addWidget(scrollable_area)
        Devices_layout.setStretch(Devices_layout.count() - 1, 1)  # scrollable_area gets 50%

        Devices_layout.addWidget(envi_area_widget)
        Devices_layout.setStretch(Devices_layout.count() - 1, 1)  # environment_area_widget gets 50%


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