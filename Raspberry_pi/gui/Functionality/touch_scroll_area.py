from PyQt6.QtWidgets import QScrollArea
from PyQt6.QtCore import Qt, QEvent

class TouchScrollArea(QScrollArea):
    def __init__(self):
        super().__init__()
        self.scroll_position = None
        self.setMouseTracking(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)

        self.setStyleSheet("""
            QScrollArea {
                background-color: #89c2fa;
                border-radius: 15px;
            }
            QScrollArea > QWidget > QWidget {
                background-color: #89c2fa;
            }
        """)
        self.viewport().setAutoFillBackground(False)
        
    def mousePressEvent(self, event):
        self.scroll_position = event.pos()
        event.accept()

    def mouseMoveEvent(self, event):
        if self.scroll_position is None:
            # If we don't have a start position, use current position
            self.scroll_position = event.pos()
            
        if event.buttons() == Qt.MouseButton.LeftButton or event.buttons() == Qt.MouseButton.NoButton:
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
