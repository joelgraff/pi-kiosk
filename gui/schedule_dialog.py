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

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import logging
import re
from utilities import load_schedule, save_schedule
from config import TV_OUTPUTS

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

    def _show_validation_error(self, message):
        logging.warning(f"ScheduleDialog: {message}")
        QMessageBox.warning(self, "Invalid Schedule Input", message)

    def save_schedule(self):
        # Saves the schedule task to schedule.json
        try:
            time = self.time_input.text().strip()
            outputs_raw = self.outputs_input.text().strip()
            path = self.path_input.text().strip()

            if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", time):
                self._show_validation_error("Time must be in 24-hour HH:MM format.")
                return

            allowed_outputs = set(TV_OUTPUTS.values())
            output_tokens = [token.strip() for token in outputs_raw.split(",") if token.strip()]
            if not output_tokens:
                self._show_validation_error("Provide at least one output number.")
                return

            outputs = []
            for token in output_tokens:
                if not token.isdigit():
                    self._show_validation_error(f"Output '{token}' is not a valid number.")
                    return
                output_num = int(token)
                if output_num not in allowed_outputs:
                    self._show_validation_error(
                        f"Output '{output_num}' is not configured. Valid outputs: {sorted(allowed_outputs)}."
                    )
                    return
                if output_num not in outputs:
                    outputs.append(output_num)

            if not time or not outputs or not path:
                self._show_validation_error("Time, outputs, and video path are required.")
                return
            
            schedule_entry = {
                "input": self.input_num,
                "time": time,
                "outputs": outputs,
                "path": path,
                "repeat": "Daily"
            }
            
            schedule_data = load_schedule()
            schedule_data.append(schedule_entry)
            save_schedule(schedule_data)
            
            logging.debug(f"ScheduleDialog: Saved schedule entry: {schedule_entry}")
            self.accept()
        except Exception as e:
            logging.error(f"ScheduleDialog: Failed to save schedule: {e}")
            self.reject()