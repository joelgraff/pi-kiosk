# source_screen.py: Source-specific screen for the media kiosk (e.g., Local Files)
#
# Overview:
# This file defines the SourceScreen class, a PyQt5 QWidget for displaying source-specific
# interfaces in the media kiosk application on a Raspberry Pi 5 with X11. For Local Files,
# it shows a screen (787x492px) with a 30pt title, 20pt fonts, 2/3 width file listbox,
# 1/3 width TV outputs list (yellow #f1c40f text), and horizontal Play/Stop/Schedule buttons
# (61x61px). It handles file selection, output selection (via OutputDialog), playback, and
# scheduling.
#
# Key Functionality:
# - Displays a file listbox for /home/admin/videos (Local Files).
# - Shows selected TV outputs (updated via OutputDialog).
# - Provides Play, Stop, Schedule, and Select Outputs buttons.
# - Updates KioskGUI.input_paths and input_output_map based on selections.
# - Supports sync status updates for Local Files.
#
# Environment:
# - Raspberry Pi 5, X11 (QT_QPA_PLATFORM=xcb), PyQt5, 787x492px main window.
# - Logs: /home/admin/gui/logs/kiosk.log (app logs, including file selection, playback).
# - Videos: /home/admin/videos (local storage).
# - Icons: /home/admin/gui/icons (61x61px: play.png, stop.png, etc.).
# - Called by: kiosk.py (show_source_screen).
#
# Recent Fixes (as of April 2025):
# - None (placeholder file based on described functionality).
# - Assumed to work with fixed show_source_screen in kiosk.py.
#
# Known Considerations:
# - Placeholder code: Actual implementation may differ. Verify with provided source_screen.py.
# - File listbox should only show supported formats (.mp4, .mkv).
# - TV outputs list (yellow text) needs correct mapping to HDMI-A-1/HDMI-A-2.
# - Ensure Select Outputs button aligns with file listbox bottom.
# - Sync status updates rely on SyncNetworkShare signals (utilities.py).
#
# Dependencies:
# - PyQt5: GUI framework.
# - Files: kiosk.py (parent), output_dialog.py (output selection), schedule_dialog.py (scheduling).
# - os: For file listing.

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QLabel, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
import logging
import os

class SourceScreen:
    def __init__(self, parent, source_name):
        # Initialize SourceScreen with KioskGUI parent and source name
        self.parent = parent
        self.source_name = source_name
        self.widget = QWidget()
        self.setup_ui()
        logging.debug(f"SourceScreen: Initialized for {source_name}")

    def setup_ui(self):
        # Sets up the Local Files screen UI: title, file list, outputs, buttons
        logging.debug(f"SourceScreen: Setting up UI for {self.source_name}")
        layout = QHBoxLayout(self.widget)
        
        # Left side: File listbox (2/3 width)
        left_layout = QVBoxLayout()
        title = QLabel(self.source_name)
        title.setFont(QFont("Arial", 30))
        title.setStyleSheet("color: white;")
        left_layout.addWidget(title)
        
        self.file_list = QListWidget()
        self.file_list.setFont(QFont("Arial", 20))
        self.file_list.setStyleSheet("color: white; background: #34495e;")
        self.file_list.itemClicked.connect(self.file_selected)
        left_layout.addWidget(self.file_list)
        
        # Populate file list for Local Files
        if self.source_name == "Local Files":
            video_dir = "/home/admin/videos"
            for file in os.listdir(video_dir):
                if file.endswith((".mp4", ".mkv")):
                    self.file_list.addItem(file)
        
        layout.addLayout(left_layout, 2)
        
        # Right side: TV outputs and buttons (1/3 width)
        right_layout = QVBoxLayout()
        outputs_label = QLabel("Selected Outputs:")
        outputs_label.setFont(QFont("Arial", 20))
        outputs_label.setStyleSheet("color: #f1c40f;")
        right_layout.addWidget(outputs_label)
        
        self.outputs_list = QListWidget()
        self.outputs_list.setFont(QFont("Arial", 20))
        self.outputs_list.setStyleSheet("color: #f1c40f; background: #34495e;")
        right_layout.addWidget(self.outputs_list)
        
        buttons_layout = QHBoxLayout()
        for action, icon in [("Play", "play.png"), ("Stop", "stop.png"), ("Schedule", "schedule.png")]:
            button = QPushButton()
            button.setFixedSize(61, 61)
            icon_path = f"/home/admin/gui/icons/{icon}"
            if os.path.exists(icon_path):
                button.setIcon(QIcon(icon_path))
                button.setIconSize(Qt.Size(61, 61))
            button.setStyleSheet("""
                QPushButton {
                    background: #34495e;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background: #6ab7f5;
                }
            """)
            if action == "Play":
                button.clicked.connect(lambda: self.parent.playback.toggle_play_pause(self.source_name))
            elif action == "Stop":
                button.clicked.connect(lambda: self.parent.playback.stop_input(2))
            elif action == "Schedule":
                button.clicked.connect(self.open_schedule_dialog)
            buttons_layout.addWidget(button)
        
        right_layout.addLayout(buttons_layout)
        
        select_outputs_button = QPushButton("Select Outputs")
        select_outputs_button.setFont(QFont("Arial", 16))
        select_outputs_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #27ae60, stop:1 #2ecc71);
                color: white;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6ab7f5, stop:1 #ffffff);
            }
        """)
        select_outputs_button.clicked.connect(self.open_output_dialog)
        right_layout.addWidget(select_outputs_button, alignment=Qt.AlignBottom)
        
        layout.addLayout(right_layout, 1)
        logging.debug("SourceScreen: UI setup completed")

    def file_selected(self, item):
        # Updates input_paths when a file is selected
        if self.source_name == "Local Files":
            file_path = os.path.join("/home/admin/videos", item.text())
            self.parent.input_paths[2] = file_path
            logging.debug(f"SourceScreen: Selected file: {file_path}")

    def open_output_dialog(self):
        # Opens OutputDialog to select TV outputs
        from output_dialog import OutputDialog
        dialog = OutputDialog(self.parent, 2)  # Input 2 for Local Files
        if dialog.exec_():
            outputs = self.parent.input_output_map.get(2, [])
            self.outputs_list.clear()
            for output in outputs:
                self.outputs_list.addItem(f"Output {output}")
            logging.debug(f"SourceScreen: Updated outputs: {outputs}")

    def open_schedule_dialog(self):
        # Opens ScheduleDialog to schedule playback
        from schedule_dialog import ScheduleDialog
        dialog = ScheduleDialog(self.parent, 2)  # Input 2 for Local Files
        dialog.exec_()
        logging.debug("SourceScreen: Schedule dialog closed")

    def update_sync_status(self, status):
        # Updates sync status for Local Files
        logging.debug(f"SourceScreen: Updating sync status: {status}")
        # Placeholder: Add sync status label if needed
        pass