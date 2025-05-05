# source_screen.py: Source screen for media kiosk sources
#
# Overview:
# Defines the SourceScreen class for managing media source screens (e.g., Local Files)
# on a Raspberry Pi 5 with X11. Displays a file listbox (~492x442px), Play/Stop buttons,
# and a sync status label. Supports multiple simultaneous playbacks with dynamic input
# numbers and per-file output selection via OutputDialog. Includes play arrows in the
# listbox to indicate playing files.
#
# Key Functionality:
# - Lists .mp4/.mkv files in /home/admin/videos (Local Files).
# - Plays selected file(s) on chosen outputs (Fellowship 1-3) via Playback.start_playback.
# - Stops individual playbacks via right-click context menu.
# - Shows play arrows in listbox for active files.
# - Displays network sync status for Local Files (via SyncNetworkShare signals).
#
# Environment:
# - Raspberry Pi 5, X11 (QT_QPA_PLATFORM=xcb), PyQt5, 787x492px main window.
# - Logs: /home/admin/kiosk/logs/kiosk.log (app logs), /home/admin/kiosk/logs/mpv.log (mpv).
# - Videos: /home/admin/videos.
# - Icons: /home/admin/kiosk/icons (play.png, stop_all.png).
#
# Recent Fixes (as of April 2025):
# - Fixed multiple simultaneous playbacks by tracking active_files and input_nums.
# - Added play arrows in listbox using custom QStandardItem and QIcon.
# - Fixed AttributeError: 'KioskGUI' object has no attribute 'playback' by accessing self.parent.playback.
#
# Known Considerations:
# - File listbox (~492x442px) assumes 48px item height for ~9 visible items.
# - Play arrows require /home/admin/kiosk/icons/play.png (16x16px recommended).
# - OutputDialog assumes TV_OUTPUTS and HDMI_OUTPUTS in config.py.
# - Sync status label updates only for Local Files.
# - Multiple playbacks may stress Raspberry Pi 5; test performance.
#
# Dependencies:
# - PyQt5: GUI framework.
# - Files: config.py (constants), playback.py (Playback), utilities.py (list_files),
#         output_dialog.py (OutputDialog).

import logging
import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListView, QPushButton, QLabel, QMenu, QAction
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon, QFont
from PyQt5.QtCore import Qt
from config import VIDEO_DIR, PLAY_BUTTON_COLOR, STOP_BUTTON_COLOR, SOURCE_SCREEN_BACKGROUND, TEXT_COLOR, FONT_FAMILY, FONT_SIZES, ICON_FILES, get_next_input_num, TV_OUTPUTS, HDMI_OUTPUTS
from utilities import list_files
from output_dialog import OutputDialog

class SourceScreen:
    def __init__(self, parent, source_name):
        self.parent = parent
        self.source_name = source_name
        self.widget = QWidget()
        self.active_files = {}  # {filename: input_num}
        self.model = QStandardItemModel()
        self.setup_ui()
        self.load_files()
        logging.debug(f"SourceScreen: Initialized for {source_name}")

    def setup_ui(self):
        logging.debug(f"SourceScreen: Setting up UI for {self.source_name}")
        layout = QVBoxLayout(self.widget)
        self.widget.setStyleSheet(f"background: {SOURCE_SCREEN_BACKGROUND}")

        self.listbox = QListView()
        self.listbox.setModel(self.model)
        self.listbox.setStyleSheet(f"color: {TEXT_COLOR}; font: {FONT_SIZES['file_list']}px {FONT_FAMILY};")
        self.listbox.setFixedSize(492, 442)
        self.listbox.clicked.connect(self.on_file_clicked)
        self.listbox.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listbox.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.listbox)

        self.play_button = QPushButton("Play")
        self.play_button.setStyleSheet(f"background: {PLAY_BUTTON_COLOR}; color: white; font: {FONT_SIZES['file_list']}px {FONT_FAMILY};")
        self.play_button.clicked.connect(self.play_file)
        layout.addWidget(self.play_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setStyleSheet(f"background: {STOP_BUTTON_COLOR}; color: white; font: {FONT_SIZES['file_list']}px {FONT_FAMILY};")
        self.stop_button.clicked.connect(self.stop_file)
        layout.addWidget(self.stop_button)

        self.sync_status_label = QLabel("Network Sync: Idle")
        self.sync_status_label.setStyleSheet(f"color: {TEXT_COLOR}; font: {FONT_SIZES['file_list']}px {FONT_FAMILY};")
        layout.addWidget(self.sync_status_label)

    def load_files(self):
        if self.source_name == "Local Files":
            files = list_files(VIDEO_DIR)
            self.model.clear()
            for file in files:
                item = QStandardItem(file)
                item.setEditable(False)
                self.model.appendRow(item)
            logging.debug(f"SourceScreen: Loaded {len(files)} files for {self.source_name}")
        else:
            self.model.clear()
            item = QStandardItem(f"{self.source_name} not implemented")
            item.setEditable(False)
            self.model.appendRow(item)
            logging.debug(f"SourceScreen: Placeholder for {self.source_name}")

    def on_file_clicked(self, index):
        self.selected_file = self.model.itemFromIndex(index).text()
        logging.debug(f"SourceScreen: Selected file: {self.selected_file}")

    def show_context_menu(self, position):
        if not hasattr(self, 'selected_file'):
            return
        menu = QMenu()
        stop_action = QAction("Stop Playback", self.widget)
        stop_action.triggered.connect(self.stop_file)
        menu.addAction(stop_action)
        menu.exec_(self.listbox.viewport().mapToGlobal(position))

    def play_file(self):
        if not hasattr(self, 'selected_file'):
            logging.warning("SourceScreen: No file selected")
            return
        dialog = OutputDialog(self.parent, self.selected_file)
        if dialog.exec_():
            outputs = dialog.get_selected_outputs()
            if not outputs:
                logging.warning("SourceScreen: No outputs selected")
                return
            input_num = get_next_input_num()
            file_path = os.path.join(VIDEO_DIR, self.selected_file)
            hdmi_map = {}
            for hdmi_idx, output_indices in HDMI_OUTPUTS.items():
                for output_idx in output_indices:
                    if output_idx in outputs:
                        if hdmi_idx not in hdmi_map:
                            hdmi_map[hdmi_idx] = []
                        hdmi_map[hdmi_idx].append(output_idx)
            try:
                self.parent.playback.start_playback(self.source_name, file_path, hdmi_map, input_num)
                self.active_files[self.selected_file] = input_num
                for i in range(self.model.rowCount()):
                    item = self.model.item(i)
                    if item.text() == self.selected_file:
                        item.setIcon(QIcon(os.path.join("/home/admin/kiosk/icons", ICON_FILES["play"])))
                logging.debug(f"SourceScreen: Started playback for {self.selected_file} with input {input_num}")
            except Exception as e:
                logging.error(f"SourceScreen: Failed to start playback for {self.selected_file}: {e}")

    def stop_file(self):
        if not hasattr(self, 'selected_file'):
            logging.warning("SourceScreen: No file selected")
            return
        if self.selected_file in self.active_files:
            input_num = self.active_files[self.selected_file]
            try:
                self.parent.playback.stop_input(input_num)
                del self.active_files[self.selected_file]
                for i in range(self.model.rowCount()):
                    item = self.model.item(i)
                    if item.text() == self.selected_file:
                        item.setIcon(QIcon())
                logging.debug(f"SourceScreen: Stopped playback for {self.selected_file} with input {input_num}")
            except Exception as e:
                logging.error(f"SourceScreen: Failed to stop playback for {self.selected_file}: {e}")