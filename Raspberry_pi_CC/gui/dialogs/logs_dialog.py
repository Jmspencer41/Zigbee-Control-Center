from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

##TODO: Fill in Logs content###

class LogsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        # Get screen size and set dialog to 80%
        screen = self.screen().availableGeometry()
        width = int(screen.width() * 0.8)
        height = int(screen.height() * 0.8)
        
        self.setWindowTitle("Logs")
        self.resize(width, height)
        
        # Center the dialog on screen
        self.move(
            (screen.width() - width) // 2,
            (screen.height() - height) // 2
        )
        
        # Add border styling
        self.setStyleSheet("""
            QDialog {
                background-color: #2c3e50;
                border: 3px solid #3498db;
                border-radius: 10px;
            }
        """)
        
        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Title
        title = QLabel("Logs")
        title.setFont(QFont('Arial', 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #ecf0f1; border: none;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        layout.addStretch()
        
        # TODO: Add your pairing content here
        content_label = QLabel("Logs interface coming soon...")
        content_label.setFont(QFont('Arial', 16))
        content_label.setStyleSheet("color: #ecf0f1; border: none;")
        content_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(content_label)
        
        layout.addStretch()
        
        # Exit button at bottom
        exit_button = QPushButton('Close')
        exit_button.setMinimumHeight(60)
        exit_button.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        exit_button.clicked.connect(self.close)  # Close this dialog
        exit_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border-radius: 30px;
                padding: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        layout.addWidget(exit_button, alignment=Qt.AlignmentFlag.AlignCenter)