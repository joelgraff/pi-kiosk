# schedule_dialog.py: Dialog for scheduling playback tasks in the media kiosk
#
# Overview:
# This file defines the ScheduleDialog class, a PyQt5 QDialog for scheduling media playback
# tasks in the media kiosk application on a Raspberry Pi 5 with X11. The dialog (assumed
# 300x300px, frameless) allows users to set a time, input, outputs, and video path for daily
# playback tasks, saved to /home/admin/gui/schedule.json (loaded by kiosk.py).
#
# Key Functionality:
# - Provides fields for time (e.g., HH:MM), input number, outputs, and video path.
# - Saves schedule data to schedule.json on confirmation.
# - Uses Qt.FramelessWindowHint for no title bar.
#
# Environment:
# - Raspberry Pi 5, X11 (QT_QPA_PLATFORM=xcb), PyQt5, 787x492px main window.
# - Logs: /home/admin/gui/logs/kiosk.log (app logs, including scheduling).
# - Schedule file: /home/admin/gui/schedule.json.
# - Called by: source_screen.py (Schedule button).
#
# Recent Fixes (as of April 2025):
# - None (placeholder file based on described functionality).
# - Assumed to work with Local Files screen and kiosk.py’s load_and_apply_schedule.
#
# Known Considerations:
# - Placeholder code: Actual implementation may differ. Verify with provided schedule_dialog.py.
# - Schedule file format and storage location (/home/admin/gui/schedule.json) need confirmation.
# - Ensure time input is validated (e.g., 24-hour format).
# - Dialog size (300x300px) is assumed; adjust for touchscreen usability.
#
# Dependencies:
# - PyQt5: GUI framework.
# - json: For schedule file handling.
# - Called by: source_screen.py.
# - Used by: kiosk.py (load_and_apply_schedule).

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import logging
import json
import os

class ScheduleDialog(QDialog):
    def __init__(self, parent, input_num):
        # Initialize ScheduleDialog with KioskGUI parent and input number
        super().__init__(parent)
        self.input_num = input_num
        self.setWindowTitle("Schedule Playback")
        self.setFixedSize(300, 300)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setup_ui()
        logging.debug(f"ScheduleDialog: Initialized for input {input_num}")

    def setup_ui(self):
        # Sets up the dialog UI: time, outputs, path inputs, and Save button
        logging.debug("ScheduleDialog: Setting up UI")
        layout = QVBoxLayout(self)
        
        time_label = QLabel("Time (HH:MM):")
        time_label.setFont(QFont("Arial", 16))
        time_label.setStyleSheet("color: white;")
        layout.addWidget(time_label)
        
        self.time_input = QLineEdit()
        self.time_input.setFont(QFont("Arial", 16))
        self.time_input.setPlaceholderText("e.g., 14:30")
        layout.addWidget(self.time_input)
        
        outputs_label = QLabel("Outputs (comma-separated, e.g., 1,3):")
        outputs_label.setFont(QFont("Arial", 16))
        outputs_label.setStyleSheet("color: white;")
        layout.addWidget(outputs_label)
        
        self.outputs_input = QLineEdit()
        self.outputs_input.setFont(QFont("Arial", 16))
        layout.addWidget(self.outputs_input)
        
        path_label = QLabel("Video Path:")
        path_label.setFont(QFont("Arial", 16))
        path_label.setStyleSheet("color: white;")
        layout.addWidget(path_label)
        
        self.path_input = QLineEdit()
        self.path_input.setFont(QFont("Arial", 16))
        layout.addWidget(self.path_input)
        
        save_button = QPushButton("Save")
        save_button.setFont(QFont("Arial", 16))
        save_button.setStyleSheet("""
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
        save_button.clicked.connect(self.save_schedule)
        layout.addWidget(save_button)
        
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2c3e50, stop:1 #34495e);
            }
        """)
        logging.debug("ScheduleDialog: UI setup completed")

    def save_schedule(self):
        # Saves the schedule task to schedule.json
        try:
            time = self.time_input.text()
            outputs = [int(o) for o in self.outputs_input.text().split(",") if o.strip()]
            path = self.path_input.text()
            if not time or not outputs or not path:
                logging.warning("ScheduleDialog: Incomplete input")
                return
            
            schedule_entry = {
                "input": self.input_num,
                "time": time,
                "outputs": outputs,
                "path": path,
                "repeat": "Daily"
            }
            
            schedule_file = "/home/admin/gui/schedule.json"
            try:
                with open(schedule_file, "r") as f:
                    schedule_data = json.load(f)
            except FileNotFoundError:
                schedule_data = []
            
            schedule_data.append(schedule_entry)
            with open(schedule_file, "w") as f:
                json.dump(schedule_data, f, indent=4)
            
            logging.debug(f"ScheduleDialog: Saved schedule entry: {schedule_entry}")
            self.accept()
        except Exception as e:
            logging.error(f"ScheduleDialog: Failed to save schedule: {e}")
            self.reject()