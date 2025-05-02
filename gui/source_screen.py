# source_screen.py: Source-specific screen for the media kiosk (e.g., Local Files)
#
# Overview:
# This file defines the SourceScreen and OutputDialog classes for the media kiosk application
# running on a Raspberry Pi 5 with X11. The SourceScreen class is a PyQt5 QWidget for displaying
# source-specific interfaces (e.g., Local Files, 787x492px) with a 28pt title, 20pt fonts,
# 2/3 width file listbox, 1/3 width TV outputs list (vivid yellow #ffc107 text), and vertical
# Play/Stop/Schedule buttons (100x100px). The OutputDialog class is a PyQt5 QDialog (245x184px,
# frameless) for selecting TV outputs (Fellowship 1, Fellowship 2, Nursery). SourceScreen
# handles file selection, output selection (via OutputDialog), playback, and scheduling.
#
# Key Functionality:
# - SourceScreen:
#   - Displays a file listbox for /home/admin/videos (Local Files).
#   - Shows selected TV outputs, sync status, and playback state with color-coded feedback.
#   - Provides Play, Stop, Schedule, and Select Outputs buttons (100x100px) with text and icons.
#   - Updates KioskGUI.input_paths and input_output_map based on selections.
# - OutputDialog:
#   - Displays toggleable buttons for Fellowship 1 (output 1), Fellowship 2 (output 2), and
#     Nursery (output 3).
#   - Styles buttons: blue for current input, red for other active inputs, gray for unassigned.
#   - Updates KioskGUI.input_output_map when outputs are toggled.
#
# Environment:
# - Raspberry Pi 5, X11 (QT_QPA_PLATFORM=xcb), PyQt5, 787x492px main window.
# - Logs: /home/admin/gui/logs/kiosk.log (app logs, including file selection, playback).
# - Videos: /home/admin/videos (local storage).
# - Icons: /home/admin/gui/icons (100x100px: play.png, stop.png, schedule.png, pause.png; 32x32px: back.png).
# - Called by: kiosk.py (show_source_screen).
#
# Integration Notes:
# - SourceScreen is instantiated by KioskGUI.show_source_screen for source navigation.
# - OutputDialog is opened by SourceScreen.open_output_dialog for Local Files (input 2).
# - Default to Fellowship 1 (output 1) if no outputs selected (implement in playback.py).
#
# Recent Changes (as of May 2025):
# - Merged OutputDialog class from output_dialog.py.
# - Revamped UI: 100x100px buttons, 28pt/20pt fonts, 2/3 vs. 1/3 layout, vibrant colors.
# - Added prominent sync status and playback state labels with color-coded feedback.
# - Optimized for touchscreen: 15px margins/spacing, 60px list items, no hover effects.
#
# Known Considerations:
# - File listbox shows only .mp4/.mkv files; verify /home/admin/videos accessibility.
# - TV outputs map to Fellowship 1 (1), Fellowship 2 (2), Nursery (3); align with HDMI outputs.
# - Dialog size (245x184px) may need increase (e.g., 300x240px) in future phases.
# - Icons must be 100x100px or scaled; ensure pause.png exists for playback state.
# - Monitor kiosk.log for UI interaction issues (e.g., touch accuracy, sync updates).
#
# Dependencies:
# - PyQt5: GUI framework.
# - Files: kiosk.py (parent), schedule_dialog.py (scheduling), utilities.py (list_files, schedule).
# - os: For file listing.

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QLabel, QPushButton, QDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from schedule_dialog import ScheduleDialog
from utilities import list_files, load_schedule, save_schedule
import logging
import os

class OutputDialog(QDialog):
    def __init__(self, parent, input_num, input_output_map, active_inputs):
        super().__init__(parent)
        self.input_num = input_num
        self.input_output_map = input_output_map
        self.active_inputs = active_inputs
        self.setWindowTitle("Select TV Outputs")
        self.setFixedSize(245, 184)
        self.setWindowFlags(Qt.FramelessWindowHint)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        self.buttons = {
            "Fellowship 1": QPushButton("Fellowship 1"),
            "Fellowship 2": QPushButton("Fellowship 2"),
            "Nursery": QPushButton("Nursery")
        }
        for name, button in self.buttons.items():
            button.setFont(QFont("Arial", 16))
            button.setCheckable(True)
            button.setFixedHeight(40)
            output_idx = {"Fellowship 1": 1, "Fellowship 2": 2, "Nursery": 3}[name]
            is_current = input_num in input_output_map and output_idx in input_output_map.get(input_num, [])
            is_other = any(other_input != input_num and output_idx in input_output_map.get(other_input, []) and active_inputs.get(other_input, False) for other_input in input_output_map)
            self.update_button_style(name, is_current, is_other)
            button.clicked.connect(lambda checked, n=name: self.update_output(n, checked))
            layout.addWidget(button)
        
        layout.addStretch()
        
        done_button = QPushButton("Done")
        done_button.setFont(QFont("Arial", 16))
        done_button.clicked.connect(self.accept)
        done_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #27ae60, stop:1 #2ecc71);
                color: white;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        layout.addWidget(done_button)

    def update_button_style(self, name, is_current, is_other):
        button = self.buttons[name]
        if is_current:
            button.setText(f"{name} (This Input)")
            button.setStyleSheet("""
                QPushButton {
                    background: #1f618d;
                    color: white;
                    border-radius: 6px;
                    padding: 8px;
                }
            """)
        elif is_other:
            button.setText(f"{name} (Other Input)")
            button.setStyleSheet("""
                QPushButton {
                    background: #c0392b;
                    color: white;
                    border-radius: 6px;
                    padding: 8px;
                }
            """)
        else:
            button.setText(name)
            button.setStyleSheet("""
                QPushButton {
                    background: #7f8c8d;
                    color: white;
                    border-radius: 6px;
                    padding: 8px;
                }
            """)
        button.setChecked(is_current or is_other)

    def update_output(self, tv_name, checked):
        output_map = {"Fellowship 1": 1, "Fellowship 2": 2, "Nursery": 3}
        output_idx = output_map[tv_name]
        if checked:
            if self.input_num not in self.input_output_map:
                self.input_output_map[self.input_num] = []
            if output_idx not in self.input_output_map[self.input_num]:
                self.input_output_map[self.input_num].append(output_idx)
        else:
            if self.input_num in self.input_output_map and output_idx in self.input_output_map[self.input_num]:
                self.input_output_map[self.input_num].remove(output_idx)
                if not self.input_output_map[self.input_num]:
                    del self.input_output_map[self.input_num]
        is_current = self.input_num in self.input_output_map and output_idx in self.input_output_map.get(self.input_num, [])
        is_other = any(other_input != self.input_num and output_idx in self.input_output_map.get(other_input, []) and self.active_inputs.get(other_input, False) for other_input in input_output_map)
        self.update_button_style(tv_name, is_current, is_other)

class SourceScreen:
    def __init__(self, parent, source_name):
        self.parent = parent
        self.source_name = source_name
        self.widget = QWidget()
        self.setup_ui()
        logging.debug(f"SourceScreen: Initialized for {source_name}")

    def setup_ui(self):
        logging.debug(f"SourceScreen: Setting up UI for {self.source_name}")
        layout = QHBoxLayout(self.widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Left side: File listbox (2/3 width)
        left_layout = QVBoxLayout()
        title = QLabel(self.source_name)
        title.setFont(QFont("Arial", 28, QFont.Bold))
        title.setStyleSheet("color: #ffffff;")
        left_layout.addWidget(title)
        
        self.file_list = QListWidget()
        self.file_list.setFont(QFont("Arial", 20))
        self.file_list.setStyleSheet("""
            QListWidget {
                color: #ffffff;
                background: #2a3b5e;
                border: 2px solid #ffffff;
                border-radius: 8px;
            }
            QListWidget::item { height: 60px; padding: 5px; }
        """)
        self.file_list.itemClicked.connect(self.file_selected)
        left_layout.addWidget(self.file_list)
        
        if self.source_name == "Local Files":
            video_dir = "/home/admin/videos"
            for file in os.listdir(video_dir):
                if file.endswith((".mp4", ".mkv")):
                    self.file_list.addItem(file)
        
        layout.addLayout(left_layout, 2)
        
        # Right side: TV outputs, status, and buttons (1/3 width)
        right_layout = QVBoxLayout()
        outputs_label = QLabel("Selected Outputs:")
        outputs_label.setFont(QFont("Arial", 20, QFont.Bold))
        outputs_label.setStyleSheet("color: #ffc107;")
        right_layout.addWidget(outputs_label)
        
        self.outputs_list = QListWidget()
        self.outputs_list.setFont(QFont("Arial", 20))
        self.outputs_list.setStyleSheet("""
            QListWidget {
                color: #ffc107;
                background: #2a3b5e;
                border: 2px solid #ffffff;
                border-radius: 8px;
            }
            QListWidget::item { height: 60px; padding: 5px; }
        """)
        right_layout.addWidget(self.outputs_list)
        
        self.sync_status_label = QLabel("Sync: Idle")
        self.sync_status_label.setFont(QFont("Arial", 20, QFont.Bold))
        self.sync_status_label.setStyleSheet("color: #ffc107;")
        right_layout.addWidget(self.sync_status_label)
        
        self.playback_state_label = QLabel("Playback: Stopped")
        self.playback_state_label.setFont(QFont("Arial", 20, QFont.Bold))
        self.playback_state_label.setStyleSheet("color: #e53935;")  # Red for Stopped
        right_layout.addWidget(self.playback_state_label)
        
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(15)
        for action, icon, color in [
            ("Play", "play.png", "#4caf50"),  # Green
            ("Stop", "stop.png", "#e53935"),  # Red
            ("Schedule", "schedule.png", "#4caf50")  # Green
        ]:
            button = QPushButton(action)
            button.setFixedSize(100, 100)
            button.setFont(QFont("Arial", 20))
            icon_path = f"/home/admin/gui/icons/{icon}"
            if os.path.exists(icon_path):
                button.setIcon(QIcon(icon_path))
                button.setIconSize(Qt.Size(80, 80))  # Slightly smaller icon for balance
                logging.debug(f"SourceScreen: Loaded icon for {action}: {icon_path}")
            else:
                logging.warning(f"SourceScreen: Icon not found for {action}: {icon_path}")
            button.setStyleSheet(f"""
                QPushButton {{
                    background: {color};
                    color: #ffffff;
                    border-radius: 8px;
                    padding: 15px;
                }}
            """)
            if action == "Play":
                self.play_button = button
                button.clicked.connect(lambda: self.parent.playback.toggle_play_pause(self.source_name))
            elif action == "Stop":
                button.clicked.connect(lambda: self.parent.playback.stop_input(2))
            elif action == "Schedule":
                button.clicked.connect(self.open_schedule_dialog)
            buttons_layout.addWidget(button)
        
        right_layout.addLayout(buttons_layout)
        
        select_outputs_button = QPushButton("Select Outputs")
        select_outputs_button.setFont(QFont("Arial", 20))
        select_outputs_button.setStyleSheet("""
            QPushButton {
                background: #1e88e5;  /* Blue */
                color: #ffffff;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        select_outputs_button.clicked.connect(self.open_output_dialog)
        right_layout.addWidget(select_outputs_button)
        
        right_layout.addStretch()
        layout.addLayout(right_layout, 1)
        
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1e2a44, stop:1 #2a3b5e);
            }
        """)
        logging.debug("SourceScreen: UI setup completed")

    def file_selected(self, item):
        if self.source_name == "Local Files":
            file_path = os.path.join("/home/admin/videos", item.text())
            self.parent.input_paths[2] = file_path
            logging.debug(f"SourceScreen: Selected file: {file_path}")

    def open_output_dialog(self):
        dialog = OutputDialog(self.parent, 2, self.parent.input_output_map, self.parent.active_inputs)
        if dialog.exec_():
            outputs = self.parent.input_output_map.get(2, [])
            self.outputs_list.clear()
            output_map = {1: "Fellowship 1", 2: "Fellowship 2", 3: "Nursery"}
            for output in outputs:
                self.outputs_list.addItem(output_map[output])
            logging.debug(f"SourceScreen: Updated outputs: {outputs}")

    def open_schedule_dialog(self):
        dialog = ScheduleDialog(self.parent, 2)
        dialog.exec_()
        logging.debug("SourceScreen: Schedule dialog closed")

    def update_sync_status(self, status):
        logging.debug(f"SourceScreen: Updating sync status: {status}")
        self.sync_status_label.setText(f"Sync: {status}")
        self.sync_status_label.update()

    def update_playback_state(self):
        is_playing = self.parent.interface.source_states.get(self.source_name, False)
        self.playback_state_label.setText(f"Playback: {'Playing' if is_playing else 'Stopped'}")
        self.playback_state_label.setStyleSheet(f"color: {'#4caf50' if is_playing else '#e53935'};")  # Green for Playing, Red for Stopped
        icon_path = f"/home/admin/gui/icons/{'pause.png' if is_playing else 'play.png'}"
        if os.path.exists(icon_path):
            self.play_button.setIcon(QIcon(icon_path))
            self.play_button.setIconSize(Qt.Size(80, 80))
            logging.debug(f"SourceScreen: Updated play button icon: {icon_path}")
        else:
            self.play_button.setText("Pause" if is_playing else "Play")
            logging.warning(f"SourceScreen: Play/Pause icon not found: {icon_path}")
        self.playback_state_label.update()