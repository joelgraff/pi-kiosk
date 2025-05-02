# source_screen.py: Source-specific screen for the media kiosk (e.g., Local Files)
#
# Overview:
# This file defines the SourceScreen class for the media kiosk application running on a
# Raspberry Pi 5 with X11. The SourceScreen class is a PyQt5 QWidget for displaying
# source-specific interfaces (e.g., Local Files, 787x492px) with a 28pt title, 20pt fonts,
# 1/2 width file listbox (300px height), 1/2 width TV outputs toggle buttons (200x60px, vivid
# yellow #ffc107 text), and horizontal Play/Stop/Schedule buttons (140x140px, icons only).
# Sync/playback status span the full width at the bottom in a horizontal layout.
#
# Key Functionality:
# - Displays a file listbox (300px height) for /home/admin/videos (Local Files).
# - Shows toggle buttons for selecting TV outputs (Fellowship 1, Fellowship 2, Nursery).
# - Places sync and playback status in a horizontal layout at the bottom (full width).
# - Provides Play, Stop, Schedule buttons (140x140px, 132x132px icons only).
# - Updates KioskGUI.input_paths and input_output_map based on selections.
#
# Environment:
# - Raspberry Pi 5, X11 (QT_QPA_PLATFORM=xcb), PyQt5, 787x492px main window.
# - Logs: /home/admin/gui/logs/kiosk.log (app logs, including file selection, playback).
# - Videos: /home/admin/videos (local storage).
# - Icons: /home/admin/kiosk/icons (128x128px: play.png, stop.png, schedule.png, pause.png).
# - Called by: kiosk.py (show_source_screen).
#
# Integration Notes:
# - SourceScreen is instantiated by KioskGUI.show_source_screen for source navigation.
# - Default to Fellowship 1 (output 1) if no outputs selected (implement in playback.py).
#
# Recent Changes (as of May 2025):
# - Revamped UI: 140x140px icon-only buttons, 28pt/20pt fonts, 1/2 vs. 1/2 layout.
# - Added sync/playback status in horizontal layout at bottom (full width).
# - Replaced Select Outputs button with toggle buttons in outputs list.
# - Fixed alignment: Shortened file list (300px), horizontal buttons, removed text.
# - Fixed AttributeError: Changed self.setStyleSheet to self.widget.setStyleSheet.
# - Fixed AttributeError: Changed self.style() to self.widget.style() for Qt icons.
# - Fixed file list: Case-insensitive extensions, added logging.
# - Removed gradient backgrounds, used solid #2a3b5e.
# - Buttons now 140x140px, horizontal layout, 25px spacing.
# - Increased icon size to 110x110px, reduced padding to 8px.
# - Increased icon size to 120x120px, reduced padding to 4px.
# - Fixed icon path to /home/admin/kiosk/icons, increased icon size to 132x132px, padding to 2px.
#
# Known Considerations:
# - File listbox shows only .mp4/.mkv files (case-insensitive); verify /home/admin/videos.
# - TV outputs map to Fellowship 1 (1), Fellowship 2 (2), Nursery (3); align with HDMI outputs.
# - Custom icons are 128x128px; falls back to Qt icons if missing; ensure pause.png exists.
# - Monitor kiosk.log for UI interaction issues (e.g., touch accuracy, file listing).
# - Monitor scaling/DPI may affect icon size; test with QT_SCALE_FACTOR=1.
#
# Dependencies:
# - PyQt5: GUI framework.
# - Files: kiosk.py (parent), schedule_dialog.py (scheduling), utilities.py (list_files, schedule).
# - os: For file listing.

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QLabel, QPushButton, QStyle
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from schedule_dialog import ScheduleDialog
from utilities import list_files, load_schedule, save_schedule
import logging
import os

class SourceScreen:
    def __init__(self, parent, source_name):
        self.parent = parent
        self.source_name = source_name
        self.widget = QWidget()
        self.output_buttons = {}  # Store output toggle buttons
        self.setup_ui()
        logging.debug(f"SourceScreen: Initialized for {source_name}")
        logging.debug(f"SourceScreen: QT_SCALE_FACTOR={os.environ.get('QT_SCALE_FACTOR', 'Not set')}")

    def setup_ui(self):
        logging.debug(f"SourceScreen: Setting up UI for {self.source_name}")
        main_layout = QVBoxLayout(self.widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Top layout: File list and outputs/buttons (1/2 vs. 1/2)
        top_layout = QHBoxLayout()
        top_layout.setSpacing(20)
        
        # Left side: File listbox (1/2 width)
        left_layout = QVBoxLayout()
        title = QLabel(self.source_name)
        title.setFont(QFont("Arial", 28, QFont.Bold))
        title.setStyleSheet("color: #ffffff; background: transparent;")
        left_layout.addWidget(title)
        
        self.file_list = QListWidget()
        self.file_list.setFont(QFont("Arial", 20))
        self.file_list.setFixedHeight(300)  # Shortened for balance
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
        left_layout.addStretch()
        
        if self.source_name == "Local Files":
            video_dir = "/home/admin/videos"
            logging.debug(f"Scanning video_dir: {video_dir}")
            if not os.path.exists(video_dir):
                logging.error(f"Video directory not found: {video_dir}")
            else:
                try:
                    files = os.listdir(video_dir)
                    logging.debug(f"Files found in {video_dir}: {files}")
                    for file in files:
                        if file.lower().endswith((".mp4", ".mkv")):
                            self.file_list.addItem(file)
                    logging.debug(f"Loaded video files: {[item.text() for item in self.file_list.findItems('*', Qt.MatchWildcard)]}")
                except Exception as e:
                    logging.error(f"Failed to list files in {video_dir}: {e}")
        
        top_layout.addLayout(left_layout, 1)
        
        # Right side: TV outputs and buttons (1/2 width)
        right_layout = QVBoxLayout()
        outputs_label = QLabel("Select Outputs:")
        outputs_label.setFont(QFont("Arial", 20, QFont.Bold))
        outputs_label.setStyleSheet("color: #ffc107; background: transparent;")
        right_layout.addWidget(outputs_label)
        
        # Outputs toggle buttons
        outputs_layout = QVBoxLayout()
        outputs_layout.setSpacing(10)
        self.output_buttons = {
            "Fellowship 1": QPushButton("Fellowship 1"),
            "Fellowship 2": QPushButton("Fellowship 2"),
            "Nursery": QPushButton("Nursery")
        }
        for name, button in self.output_buttons.items():
            button.setFont(QFont("Arial", 20))
            button.setFixedSize(200, 60)
            button.setCheckable(True)
            output_idx = {"Fellowship 1": 1, "Fellowship 2": 2, "Nursery": 3}[name]
            is_current = 2 in self.parent.input_output_map and output_idx in self.parent.input_output_map.get(2, [])
            is_other = any(other_input != 2 and output_idx in self.parent.input_output_map.get(other_input, []) and self.parent.active_inputs.get(other_input, False) for other_input in self.parent.input_output_map)
            self.update_output_button_style(name, is_current, is_other)
            button.clicked.connect(lambda checked, n=name: self.toggle_output(n, checked))
            outputs_layout.addWidget(button)
        
        right_layout.addLayout(outputs_layout)
        
        # Play/Stop/Schedule buttons (horizontal)
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(25)  # Increased for larger buttons
        for action, icon, color, qt_icon in [
            ("Play", "play.png", "#4caf50", QStyle.SP_MediaPlay),
            ("Stop", "stop.png", "#e53935", QStyle.SP_MediaStop),
            ("Schedule", "schedule.png", "#4caf50", QStyle.SP_FileDialogContentsView)
        ]:
            button = QPushButton()
            button.setFixedSize(140, 140)  # Larger, touch-friendly
            button.setFont(QFont("Arial", 20))
            icon_path = f"/home/admin/kiosk/icons/{icon}"
            icon_dir = "/home/admin/kiosk/icons"
            if not os.path.exists(icon_dir):
                logging.error(f"Icon directory not found: {icon_dir}")
            else:
                try:
                    logging.debug(f"SourceScreen: Icon directory contents: {os.listdir(icon_dir)}")
                except Exception as e:
                    logging.warning(f"SourceScreen: Failed to list icon directory {icon_dir}: {e}")
            if os.path.exists(icon_path):
                button.setIcon(QIcon(icon_path))
                button.setIconSize(Qt.Size(132, 132))  # Maximum size for custom icons
                try:
                    logging.debug(f"SourceScreen: Loaded custom icon for {action}: {icon_path}, size: 132x132px, file_size: {os.path.getsize(icon_path)} bytes")
                except Exception as e:
                    logging.warning(f"SourceScreen: Failed to get file size for {icon_path}: {e}")
            else:
                button.setIcon(self.widget.style().standardIcon(qt_icon))  # Qt fallback
                logging.warning(f"SourceScreen: Custom icon not found for {action}: {icon_path}, using Qt icon {qt_icon}, size: 132x132px")
            button.setStyleSheet(f"""
                QPushButton {{
                    background: {color};
                    color: #ffffff;
                    border-radius: 8px;
                    padding: 2px;
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
        top_layout.addLayout(right_layout, 1)
        
        main_layout.addLayout(top_layout)
        
        # Bottom layout: Status messages (full width)
        bottom_layout = QHBoxLayout()
        self.sync_status_label = QLabel("Sync: Idle")
        self.sync_status_label.setFont(QFont("Arial", 20, QFont.Bold))
        self.sync_status_label.setStyleSheet("color: #ffc107; background: transparent;")
        bottom_layout.addWidget(self.sync_status_label)
        
        bottom_layout.addStretch()
        
        self.playback_state_label = QLabel("Playback: Stopped")
        self.playback_state_label.setFont(QFont("Arial", 20, QFont.Bold))
        self.playback_state_label.setStyleSheet("color: #e53935;")  # Red for Stopped
        bottom_layout.addWidget(self.playback_state_label)
        
        main_layout.addLayout(bottom_layout)
        
        # Apply solid background to the QWidget
        self.widget.setStyleSheet("QWidget { background: #2a3b5e; }")
        logging.debug("SourceScreen: UI setup completed")

    def update_output_button_style(self, name, is_current, is_other):
        button = self.output_buttons[name]
        if is_current:
            button.setText(f"{name} (Selected)")
            button.setStyleSheet("""
                QPushButton {
                    background: #1f618d;
                    color: white;
                    border-radius: 8px;
                    padding: 10px;
                }
            """)
        elif is_other:
            button.setText(f"{name} (Other Input)")
            button.setStyleSheet("""
                QPushButton {
                    background: #c0392b;
                    color: white;
                    border-radius: 8px;
                    padding: 10px;
                }
            """)
        else:
            button.setText(name)
            button.setStyleSheet("""
                QPushButton {
                    background: #7f8c8d;
                    color: white;
                    border-radius: 8px;
                    padding: 10px;
                }
            """)
        button.setChecked(is_current or is_other)

    def toggle_output(self, tv_name, checked):
        output_map = {"Fellowship 1": 1, "Fellowship 2": 2, "Nursery": 3}
        output_idx = output_map[tv_name]
        input_num = 2  # Local Files
        if checked:
            if input_num not in self.parent.input_output_map:
                self.parent.input_output_map[input_num] = []
            if output_idx not in self.parent.input_output_map[input_num]:
                self.parent.input_output_map[input_num].append(output_idx)
        else:
            if input_num in self.parent.input_output_map and output_idx in self.parent.input_output_map[input_num]:
                self.parent.input_output_map[input_num].remove(output_idx)
                if not self.parent.input_output_map[input_num]:
                    del self.parent.input_output_map[input_num]
        is_current = input_num in self.parent.input_output_map and output_idx in self.parent.input_output_map.get(input_num, [])
        is_other = any(other_input != input_num and output_idx in self.parent.input_output_map.get(other_input, []) and self.parent.active_inputs.get(other_input, False) for other_input in self.parent.input_output_map)
        self.update_output_button_style(tv_name, is_current, is_other)
        logging.debug(f"SourceScreen: Toggled output {tv_name}: checked={checked}, map={self.parent.input_output_map}")

    def file_selected(self, item):
        if self.source_name == "Local Files":
            file_path = os.path.join("/home/admin/videos", item.text())
            self.parent.input_paths[2] = file_path
            logging.debug(f"SourceScreen: Selected file: {file_path}")

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
        self.playback_state_label.setStyleSheet(f"color: {'#4caf50' if is_playing else '#e53935'}; background: transparent;")  # Green for Playing, Red for Stopped
        icon_path = f"/home/admin/kiosk/icons/{'pause.png' if is_playing else 'play.png'}"
        qt_icon = QStyle.SP_MediaPause if is_playing else QStyle.SP_MediaPlay
        icon_dir = "/home/admin/kiosk/icons"
        if not os.path.exists(icon_dir):
            logging.error(f"Icon directory not found: {icon_dir}")
        else:
            try:
                logging.debug(f"SourceScreen: Icon directory contents: {os.listdir(icon_dir)}")
            except Exception as e:
                logging.warning(f"SourceScreen: Failed to list icon directory {icon_dir}: {e}")
        if os.path.exists(icon_path):
            self.play_button.setIcon(QIcon(icon_path))
            self.play_button.setIconSize(Qt.Size(132, 132))  # Maximum size for custom icons
            try:
                logging.debug(f"SourceScreen: Updated play button with custom icon: {icon_path}, size: 132x132px, file_size: {os.path.getsize(icon_path)} bytes")
            except Exception as e:
                logging.warning(f"SourceScreen: Failed to get file size for {icon_path}: {e}")
        else:
            self.play_button.setIcon(self.widget.style().standardIcon(qt_icon))  # Qt fallback
            logging.warning(f"SourceScreen: Play/Pause custom icon not found: {icon_path}, using Qt icon {qt_icon}, size: 132x132px")
        self.playback_state_label.update()