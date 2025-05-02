# source_screen.py: Source-specific screen for the media kiosk (e.g., Local Files)
#
# Overview:
# This file defines the SourceScreen and OutputDialog classes for the media kiosk application
# running on a Raspberry Pi 5 with X11. The SourceScreen class is a PyQt5 QWidget for displaying
# source-specific interfaces (e.g., Local Files, 787x492px) with a 28pt title, 20pt fonts,
# 3/5 width file listbox (300px height), 2/5 width TV outputs list (150px height, vivid yellow
# #ffc107 text), and vertical Play/Stop/Schedule buttons (100x100px). Status messages are
# at the bottom of the left side. The OutputDialog class is a PyQt5 QDialog (245x184px,
# frameless) for selecting TV outputs (Fellowship 1, Fellowship 2, Nursery).
#
# Key Functionality:
# - SourceScreen:
#   - Displays a file listbox (300px height) for /home/admin/videos (Local Files).
#   - Shows selected TV outputs (150px height), with Select Outputs button nearby.
#   - Places sync status and playback state at the bottom of the left side.
#   - Provides Play, Stop, Schedule buttons (100x100px) with icons and text.
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
# - Icons: /home/admin/gui/icons (100x100px: play.png, stop.png, schedule.png, pause.png).
# - Called by: kiosk.py (show_source_screen).
#
# Integration Notes:
# - SourceScreen is instantiated by KioskGUI.show_source_screen for source navigation.
# - OutputDialog is opened by SourceScreen.open_output_dialog for Local Files (input 2).
# - Default to Fellowship 1 (output 1) if no outputs selected (implement in playback.py).
#
# Recent Changes (as of May 2025):
# - Merged OutputDialog class from output_dialog.py.
# - Revamped UI: 100x100px buttons, 28pt/20pt fonts, 3/5 vs. 2/5 layout, vibrant colors.
# - Added prominent sync status and playback state labels with color-coded feedback.
# - Fixed AttributeError: Changed self.setStyleSheet to self.widget.setStyleSheet.
# - Fixed alignment: Shortened file list (300px), moved status messages to bottom left,
#   repositioned Select Outputs near outputs list, fixed button overlap, added icon fallbacks.
#
# Known Considerations:
# - File listbox shows only .mp4/.mkv files; verify /home/admin/videos accessibility.
# - TV outputs map to Fellowship 1 (1), Fellowship 2 (2), Nursery (3); align with HDMI outputs.
# - Dialog size (245x184px) may need increase (e.g., 300x240px) in future phases.
# - Icons must be 100x100px; falls back to Qt icons if missing; ensure pause.png exists.
# - Monitor kiosk.log for UI interaction issues (e.g., touch accuracy, icon loading).
#
# Dependencies:
# - PyQt5: GUI framework.
# - Files: kiosk.py (parent), schedule_dialog.py (scheduling), utilities.py (list_files, schedule).
# - os: For file listing.
# - Note: list_files and save_schedule from utilities.py are used by OutputDialog, not SourceScreen.

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QLabel, QPushButton, QDialog, QStyle
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
        is_other = any(other_input != self.input_num and output_idx in input_output_map.get(other_input, []) and self.active_inputs.get(other_input, False) for other_input in input_output_map)
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
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Left side: File listbox and status messages (3/5 width)
        left_layout = QVBoxLayout()
        title = QLabel(self.source_name)
        title.setFont(QFont("Arial", 28, QFont.Bold))
        title.setStyleSheet("color: #ffffff;")
        left_layout.addWidget(title)
        
        self.file_list = QListWidget()
        self.file_list.setFont(QFont("Arial", 20))
        self.file_list.setFixedHeight(300)  # Shortened to leave space for status
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
        
        # Status messages below file list
        status_layout = QVBoxLayout()
        self.sync_status_label = QLabel("Sync: Idle")
        self.sync_status_label.setFont(QFont("Arial", 20, QFont.Bold))
        self.sync_status_label.setStyleSheet("color: #ffc107;")
        status_layout.addWidget(self.sync_status_label)
        
        self.playback_state_label = QLabel("Playback: Stopped")
        self.playback_state_label.setFont(QFont("Arial", 20, QFont.Bold))
        self.playback_state_label.setStyleSheet("color: #e53935;")  # Red for Stopped
        status_layout.addWidget(self.playback_state_label)
        
        left_layout.addLayout(status_layout)
        left_layout.addStretch()
        
        layout.addLayout(left_layout, 3)
        
        # Right side: TV outputs and buttons (2/5 width)
        right_layout = QVBoxLayout()
        outputs_label = QLabel("Selected Outputs:")
        outputs_label.setFont(QFont("Arial", 20, QFont.Bold))
        outputs_label.setStyleSheet("color: #ffc107;")
        right_layout.addWidget(outputs_label)
        
        self.outputs_list = QListWidget()
        self.outputs_list.setFont(QFont("Arial", 20))
        self.outputs_list.setFixedHeight(150)  # Shortened for compactness
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
        
        select_outputs_button = QPushButton("Select Outputs")
        select_outputs_button.setFont(QFont("Arial", 20))
        select_outputs_button.setFixedSize(150, 50)  # Smaller for better fit
        select_outputs_button.setStyleSheet("""
            QPushButton {
                background: #1e88e5;  /* Blue */
                color: #ffffff;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        select_outputs_button.clicked.connect(self.open_output_dialog)
        right_layout.addWidget(select_outputs_button)
        
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(20)  # Increased to prevent overlap
        for action, icon, color, qt_icon in [
            ("Play", "play.png", "#4caf50", QStyle.SP_MediaPlay),
            ("Stop", "stop.png", "#e53935", QStyle.SP_MediaStop),
            ("Schedule", "schedule.png", "#4caf50", QStyle.SP_FileDialogDetailedView)
        ]:
            button = QPushButton(action)
            button.setFixedSize(100, 100)
            button.setFont(QFont("Arial", 20))
            icon_path = f"/home/admin/gui/icons/{icon}"
            if os.path.exists(icon_path):
                button.setIcon(QIcon(icon_path))
                button.setIconSize(Qt.Size(90, 90))  # Larger for prominence
                logging.debug(f"SourceScreen: Loaded icon for {action}: {icon_path}")
            else:
                button.setIcon(self.style().standardIcon(qt_icon))  # Qt fallback
                logging.warning(f"SourceScreen: Icon not found for {action}: {icon_path}, using Qt icon")
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
        right_layout.addStretch()
        layout.addLayout(right_layout, 2)
        
        # Apply stylesheet to the QWidget
        self.widget.setStyleSheet("""
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
        qt_icon = QStyle.SP_MediaPause if is_playing else QStyle.SP_MediaPlay
        if os.path.exists(icon_path):
            self.play_button.setIcon(QIcon(icon_path))
            self.play_button.setIconSize(Qt.Size(90, 90))
            logging.debug(f"SourceScreen: Updated play button icon: {icon_path}")
        else:
            self.play_button.setIcon(self.style().standardIcon(qt_icon))
            logging.warning(f"SourceScreen: Play/Pause icon not found: {icon_path}, using Qt icon")
            self.play_button.setText("Pause" if is_playing else "Play")
        self.playback_state_label.update()