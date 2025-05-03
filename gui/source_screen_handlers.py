# source_screen_handlers.py: Event handlers for SourceScreen
#
# Overview:
# Defines functions for file selection, schedule dialog, and status updates.
#
# Recent Changes (as of June 2025):
# - Simplified icon logging.

from PyQt5.QtWidgets import QStyle
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from schedule_dialog import ScheduleDialog
import logging
import os

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
    self.playback_state_label.setStyleSheet(f"color: {'#4caf50' if is_playing else '#e53935'}; background: transparent;")
    icon_path = f"/home/admin/kiosk/gui/icons/{'pause.png' if is_playing else 'play.png'}"
    qt_icon = QStyle.SP_MediaPause if is_playing else QStyle.SP_MediaPlay
    if os.path.exists(icon_path):
        self.play_button.setIcon(QIcon(icon_path))
        self.play_button.setIconSize(QSize(112, 112))
        logging.debug(f"SourceScreen: Updated play button with custom icon: {icon_path}")
    else:
        self.play_button.setIcon(self.widget.style().standardIcon(qt_icon))
        logging.warning(f"SourceScreen: Play/Pause custom icon not found: {icon_path}")
    self.play_button.setStyleSheet(f"""
        QPushButton {{
            background: #4caf50;
            color: #ffffff;
            border-radius: 8px;
            padding: 2px;
            icon-size: 112px;
        }}
    """)
    self.playback_state_label.update()