# source_screen_handlers.py: Event handlers for SourceScreen
#
# Overview:
# Defines functions for file selection, schedule dialog, and status updates.
#
# Recent Changes (as of June 2025):
# - Simplified icon logging.
# - Extracted hardcoded values to config.py.
#
# Dependencies:
# - config.py: Filepaths, input number, colors, icon files.

from PyQt5.QtWidgets import QStyle
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from schedule_dialog import ScheduleDialog
import logging
import os
from config import VIDEO_DIR, ICON_DIR, ICON_FILES, LOCAL_FILES_INPUT_NUM, PLAY_BUTTON_COLOR, TEXT_COLOR, PLAYBACK_STATUS_COLORS, ICON_SIZE

def file_selected(self, item):
    if self.source_name == "Local Files":
        file_path = os.path.join(VIDEO_DIR, item.text())
        self.parent.input_paths[LOCAL_FILES_INPUT_NUM] = file_path
        logging.debug(f"SourceScreen: Selected file: {file_path}")

def open_schedule_dialog(self):
    dialog = ScheduleDialog(self.parent, LOCAL_FILES_INPUT_NUM)
    dialog.exec_()
    logging.debug("SourceScreen: Schedule dialog closed")

def update_sync_status(self, status):
    logging.debug(f"SourceScreen: Updating sync status: {status}")
    self.sync_status_label.setText(f"Sync: {status}")
    self.sync_status_label.update()

def update_playback_state(self):
    is_playing = self.parent.interface.source_states.get(self.source_name, False)
    state = "Playing" if is_playing else "Stopped"
    self.playback_state_label.setText(f"Playback: {state}")
    self.playback_state_label.setStyleSheet(f"color: {PLAYBACK_STATUS_COLORS[state.lower()]}; background: transparent;")
    icon_file = ICON_FILES["pause"] if is_playing else ICON_FILES["play"]
    icon_path = os.path.join(ICON_DIR, icon_file)
    qt_icon = QStyle.SP_MediaPause if is_playing else QStyle.SP_MediaPlay
    if os.path.exists(icon_path):
        self.play_button.setIcon(QIcon(icon_path))
        self.play_button.setIconSize(QSize(*ICON_SIZE))
        logging.debug(f"SourceScreen: Updated play button with custom icon: {icon_path}")
    else:
        self.play_button.setIcon(self.widget.style().standardIcon(qt_icon))
        logging.warning(f"SourceScreen: Play/Pause custom icon not found: {icon_path}")
    self.play_button.setStyleSheet(f"""
        QPushButton {{
            background: {PLAY_BUTTON_COLOR};
            color: {TEXT_COLOR};
            border-radius: {BORDER_RADIUS}px;
            padding: {BUTTON_PADDING['play_stop']}px;
            icon-size: {ICON_SIZE[0]}px;
        }}
    """)
    self.playback_state_label.update()