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

        ###### TODO: Add buttons and functionality below ######
        Button_Layout = QHBoxLayout()
        Button_Layout.setSpacing(20)
        main_layout.addLayout(Button_Layout)

        #Button to pair new devices into network
        pair_button = QPushButton('Pair Devices')
        pair_button.setMinimumHeight(60)
        pair_button.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        #pair_button.clicked.connect(self.on_button1_clicked)
        pair_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 30px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        Button_Layout.addWidget(pair_button)

        #Button to view device logs
        logs_button = QPushButton('View Logs')
        logs_button.setMinimumHeight(60)
        logs_button.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        #logs_button.clicked.connect(self.on_button1_clicked)
        logs_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 30px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        Button_Layout.addWidget(logs_button)


        #Button to view device logs
        settings_button = QPushButton('Settings')
        settings_button.setMinimumHeight(60)
        settings_button.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        #settings_button.clicked.connect(self.on_button1_clicked)
        settings_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 30px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        Button_Layout.addWidget(settings_button)

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

        scrollable_area.setWidget(device_list_widget)
        scrollable_area.setWidgetResizable(True)

        envi_area_widget = QWidget()
        envi_area_widget.setStyleSheet("background-color: #89c2fa; border-radius: 15px;")    
        envi_area_layout = QVBoxLayout()
        envi_area_widget.setLayout(envi_area_layout)

        ### TODO: Make dynamic from actual environment data ###
        temp_humid_layout = QHBoxLayout()
        temp_humid_layout.setSpacing(20)
        
        temp_label = QLabel("Temp: 22°C")
        temp_label.setFont(QFont('Arial', 16))
        temp_label.setStyleSheet("color: #2c3e50;") 
        
        humid_label = QLabel("Humidity: 45%")
        humid_label.setFont(QFont('Arial', 16))
        humid_label.setStyleSheet("color: #2c3e50;")
        
        temp_humid_layout.addWidget(temp_label)
        temp_humid_layout.addWidget(humid_label)

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


def create_device_button(name):
    button = QPushButton(name)
    button.setMinimumHeight(100)
    button.setFont(QFont('Arial', 12))
    button.setStyleSheet("""
        QPushButton {
            background-color: #1abc9c;
            color: white;
            border-radius: 25px;
            padding: 10px;
            text-align: left;
                         }
            QPushButton:pressed {
                background-color: #626d6e;
            }
        """)
    return button

### TODO: Make this a proper class in its own file ###
### Fix this AI slop!!! ###
class TouchScrollArea(QScrollArea):
    def __init__(self):
        super().__init__()
        self.scroll_position = None
        self.setMouseTracking(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
        
    def mousePressEvent(self, event):
        self.scroll_position = event.pos()
        event.accept()
        
    def mouseMoveEvent(self, event):
        if self.scroll_position is not None and event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.pos().y() - self.scroll_position.y()
            self.scroll_position = event.pos()
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta
            )
        event.accept()
    
    def mouseReleaseEvent(self, event):
        self.scroll_position = None
        event.accept()
    
    def touchEvent(self, event):
        if event.type() == QEvent.Type.TouchBegin:
            self.scroll_position = event.touchPoints()[0].pos().toPoint()
        elif event.type() == QEvent.Type.TouchUpdate:
            if self.scroll_position is not None:
                delta = event.touchPoints()[0].pos().toPoint().y() - self.scroll_position.y()
                self.scroll_position = event.touchPoints()[0].pos().toPoint()
                self.verticalScrollBar().setValue(
                    self.verticalScrollBar().value() - delta
                )
        elif event.type() == QEvent.Type.TouchEnd:
            self.scroll_position = None
        event.accept()

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