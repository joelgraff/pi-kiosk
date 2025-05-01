# auth_dialog.py: Authentication dialog for the media kiosk
#
# Overview:
# This file defines the AuthDialog class, a PyQt5 QDialog for user authentication in the
# media kiosk application running on a Raspberry Pi 5 with X11. The dialog (245x184px,
# frameless, PIN entry) prompts for a PIN (default: 1234) at startup, blocking access to
# the main interface until authenticated. It is displayed standalone (no parent) and centered
# on the screen.
#
# Key Functionality:
# - Displays a PIN entry field, "Authenticate" button, and "Enter PIN" label.
# - Hashes the entered PIN (SHA256) and compares it to the expected hash (for PIN 1234).
# - Uses Qt.FramelessWindowHint and Qt.WindowStaysOnTopHint for a clean, modal appearance.
# - Logs visibility and geometry for debugging (showEvent, initialization).
#
# Environment:
# - Raspberry Pi 5, X11 (QT_QPA_PLATFORM=xcb), PyQt5, 787x492px main window.
# - Logs: /home/admin/gui/logs/kiosk.log (app logs, including AuthDialog events).
# - Called by: kiosk.py (show_auth_dialog).
#
# Recent Fixes (as of April 2025):
# - Added showEvent logging to track visibility and geometry.
# - Fixed visibility issues by removing parent, using QTimer delay, and centering on screen (in kiosk.py).
# - Ensured Qt.FramelessWindowHint for no title bar.
#
# Known Considerations:
# - PIN is hardcoded (1234, SHA256 hashed). Consider configurable PIN or secure storage.
# - Ensure dialog remains modal and focused on touchscreen input.
# - Monitor kiosk.log for authentication failures or visibility issues.
#
# Dependencies:
# - PyQt5: GUI framework.
# - hashlib: For PIN hashing.
# - Called by: kiosk.py.

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import hashlib
import logging

class AuthDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        logging.debug("AuthDialog: Initializing")
        self.setWindowTitle("Authentication")
        self.setup_ui()
        logging.debug(f"AuthDialog: Initialized, visible: {self.isVisible()}, geometry: {self.geometry().getRect()}, parent: {self.parent()}")

    def setup_ui(self):
        # Sets up the dialog UI: label, PIN input, and Authenticate button
        logging.debug("AuthDialog: Setting up UI")
        layout = QVBoxLayout(self)
        
        label = QLabel("Enter PIN:")
        label.setFont(QFont("Arial", 16))
        label.setStyleSheet("color: white;")
        layout.addWidget(label)
        
        self.pin_input = QLineEdit()
        self.pin_input.setFont(QFont("Arial", 16))
        self.pin_input.setEchoMode(QLineEdit.Password)
        self.pin_input.setStyleSheet("color: black; background: white;")
        self.pin_input.setFixedWidth(200)
        layout.addWidget(self.pin_input)
        
        auth_button = QPushButton("Authenticate")
        auth_button.setFont(QFont("Arial", 16))
        auth_button.clicked.connect(self.accept)
        auth_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #27ae60, stop:1 #2ecc71);
                color: white;
                border-radius: 6px;
                padding: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6ab7f5, stop:1 #ffffff);
            }
        """)
        layout.addWidget(auth_button)
        
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2c3e50, stop:1 #34495e);
            }
        """)
        logging.debug("AuthDialog: UI setup completed")

    def get_pin(self):
        # Returns the SHA256 hash of the entered PIN
        pin = self.pin_input.text()
        logging.debug("AuthDialog: PIN retrieved")
        return hashlib.sha256(pin.encode()).hexdigest()

    def showEvent(self, event):
        # Logs visibility and geometry when the dialog is shown
        logging.debug(f"AuthDialog: showEvent triggered, visible: {self.isVisible()}, geometry: {self.geometry().getRect()}, parent: {self.parent()}")
        super().showEvent(event)