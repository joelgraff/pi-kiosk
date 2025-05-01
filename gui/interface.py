# interface.py: Main interface screen for the media kiosk
#
# Overview:
# This file defines the Interface class, responsible for the main interface screen of the
# media kiosk application on a Raspberry Pi 5 with X11. The interface displays tile buttons
# (~245x190px) for media sources (e.g., Local Files, Audio, DVD, Web) and a Stop All button.
# Clicking a source navigates to its SourceScreen (via kiosk.py's show_source_screen).
#
# Key Functionality:
# - Creates a QGridLayout with source buttons and a Stop All button.
# - Handles button clicks to navigate to SourceScreen (e.g., Local Files).
# - Updates sync status for Local Files (connected to SyncNetworkShare signals).
# - Maintains source_states to track playback status.
#
# Environment:
# - Raspberry Pi 5, X11 (QT_QPA_PLATFORM=xcb), PyQt5, 787x492px main window.
# - Logs: /home/admin/gui/logs/kiosk.log (app logs, including navigation).
# - Icons: /home/admin/gui/icons (64x64px: audio.png, local_files.png, etc.).
# - Called by: kiosk.py (initializes Interface).
#
# Recent Fixes (as of April 2025):
# - Fixed AttributeError: 'KioskGUI' object has no attribute 'show_source_screen' (line 49)
#   by adding show_source_screen to KioskGUI in kiosk.py.
#
# Known Considerations:
# - Ensure icon files exist in /home/admin/gui/icons to avoid warnings.
# - Button sizes (~245x190px) and layout may need adjustment for touchscreen usability.
# - Sync status updates rely on SyncNetworkShare signals (utilities.py).
# - Placeholder code assumed for tile button setup; verify actual implementation.
#
# Dependencies:
# - PyQt5: GUI framework.
# - Files: kiosk.py (parent), source_screen.py (navigation target).

from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont
import logging
import os

class Interface:
    def __init__(self, parent):
        # Initialize Interface with KioskGUI parent
        self.parent = parent
        self.main_widget = QWidget()
        self.source_states = {"Local Files": False, "Audio": False, "DVD": False, "Web": False}
        self.setup_ui()
        logging.debug("Interface: Initialized")

    def setup_ui(self):
        # Sets up the main interface with source buttons and Stop All
        logging.debug("Interface: Setting up UI")
        layout = QGridLayout(self.main_widget)
        sources = ["Local Files", "Audio", "DVD", "Web"]
        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]

        for source, pos in zip(sources, positions):
            button = QPushButton(source)
            button.setFont(QFont("Arial", 16))
            icon_path = f"/home/admin/gui/icons/{source.lower().replace(' ', '_')}.png"
            if os.path.exists(icon_path):
                button.setIcon(QIcon(icon_path))
                button.setIconSize(Qt.Size(64, 64))
            button.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2980b9, stop:1 #3498db);
                    color: white;
                    border-radius: 6px;
                    padding: 10px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6ab7f5, stop:1 #ffffff);
                }
            """)
            button.setFixedSize(245, 190)
            button.clicked.connect(lambda checked, s=source: self.source_clicked(s))
            layout.addWidget(button, *pos)

        stop_all_button = QPushButton("Stop All")
        stop_all_button.setFont(QFont("Arial", 16))
        if os.path.exists("/home/admin/gui/icons/stop_all.png"):
            stop_all_button.setIcon(QIcon("/home/admin/gui/icons/stop_all.png"))
            stop_all_button.setIconSize(Qt.Size(64, 64))
        stop_all_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #c0392b, stop:1 #e74c3c);
                color: white;
                border-radius: 6px;
                padding: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6ab7f5, stop:1 #ffffff);
            }
        """)
        stop_all_button.clicked.connect(self.parent.playback.stop_all_playback)
        layout.addWidget(stop_all_button, 2, 0, 1, 2, Qt.AlignCenter)
        logging.debug("Interface: UI setup completed")

    def source_clicked(self, source_name):
        # Handles source button clicks, navigating to SourceScreen
        logging.debug(f"Interface: Source clicked: {source_name}")
        self.parent.selected_source = source_name
        self.parent.show_source_screen(source_name)  # Line 49: Calls KioskGUI.show_source_screen

    def update_sync_status(self, status):
        # Updates sync status display (connected to SyncNetworkShare signals)
        logging.debug(f"Interface: Updating sync status: {status}")
        # Placeholder: Add sync status label or indicator if needed
        pass