from PyQt6.QtWidgets import QPushButton

class ScrollableButton(QPushButton):
    def __init__(self, name):
        super().__init__(name)
        self.press_pos = None
        self.is_dragging = False
        
    def mousePressEvent(self, event):
        self.press_pos = event.globalPosition().toPoint()
        self.is_dragging = False
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        if self.press_pos is not None and not self.is_dragging:
            delta = (event.globalPosition().toPoint() - self.press_pos).manhattanLength()
            if delta > 8:
                self.is_dragging = True
                self.setDown(False)  # Release button visual
                
        if self.is_dragging:
            # Forward to scroll area
            scroll_area = self.find_scroll_area()
            if scroll_area:
                scroll_area.mouseMoveEvent(event)
            event.accept()
        else:
            super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event):
        if not self.is_dragging:
            super().mouseReleaseEvent(event)
        
        self.press_pos = None
        self.is_dragging = False
        event.accept()
    
    def find_scroll_area(self):
        parent = self.parent()
        while parent:
            if hasattr(parent, 'mouseMoveEvent') and 'TouchScrollArea' in type(parent).__name__:
                return parent
            parent = parent.parent()
        return None