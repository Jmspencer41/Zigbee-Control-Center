from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea)
from PyQt6.QtCore import (Qt, QEvent)
from PyQt6.QtGui import QFont

class DeviceListLayout(QHBoxLayout):
    def __init__(self):
        super().__init__()
 
        scrollable_area = TouchScrollArea()
        scrollable_area.setStyleSheet("background-color: #89c2fa; border-radius: 15px;")  

        device_list_widget = QWidget()
        device_list_layout = QVBoxLayout()
        device_list_widget.setLayout(device_list_layout)

        # Example device buttons TODO: Make dynamic from actual devices
        for i in range(20):
            device_button = self.create_device_button(f"Device {i+1}")
            device_list_layout.addWidget(device_button)
            device_list_layout.addSpacing(10)

        scrollable_area.setWidget(device_list_widget)
        scrollable_area.setWidgetResizable(True)

        self.addWidget(scrollable_area)

    def create_device_button(self, name):
        button = QPushButton(name)
        button.setMinimumHeight(100)
        button.setFont(QFont('Arial', 12))

        if True: #TODO implement device status check
            button.setStyleSheet("""
                QPushButton {
                    background-color: #00B814;
                    color: white;
                    border-radius: 25px;
                    padding: 10px;
                    text-align: left;
                                }
                    QPushButton:pressed {
                        background-color: #626d6e;
                    }
                """)
        else:
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
