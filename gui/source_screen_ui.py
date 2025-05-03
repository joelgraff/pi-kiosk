# source_screen.py: Main class for the source-specific screen (e.g., Local Files)
#
# Overview:
# Defines the SourceScreen class for the media kiosk on Raspberry Pi 5 with X11.
# Handles initialization and delegates UI setup and event handling to separate modules.
#
# Environment:
# - Raspberry Pi 5, X11 (QT_QPA_PLATFORM=xcb), PyQt5, 787x492px window.
# - Logs: /home/admin/kiosk/logs/kiosk.log.
# - Icons: /home/admin/kiosk/icons (128x128px).
# - Videos: /home/admin/kiosk/videos.
#
# Recent Changes (as of June 2025):
# - Added import os for QT_SCALE_FACTOR logging.
#
# Dependencies:
# - PyQt5: GUI framework.
# - source_screen_ui.py: UI setup.
# - source_screen_outputs.py: Output button styling and toggling.
# - source_screen_handlers.py: Event handlers.
# - schedule_dialog.py, utilities.py.

from PyQt5.QtWidgets import QWidget
import logging
import os
from source_screen_ui import setup_ui
from source_screen_outputs import update_output_button_style, toggle_output
from source_screen_handlers import file_selected, open_schedule_dialog, update_sync_status, update_playback_state

class SourceScreen:
    def __init__(self, parent, source_name):
        self.parent = parent
        self.source_name = source_name
        self.widget = QWidget()
        self.output_buttons = {}  # Store output toggle buttons
        self.file_list = None  # Set in setup_ui
        self.play_button = None  # Set in setup_ui
        self.sync_status_label = None  # Set in setup_ui
        self.playback_state_label = None  # Set in setup_ui
        self.setup_ui()
        logging.debug(f"SourceScreen: Initialized for {self.source_name}")
        logging.debug(f"SourceScreen: QT_SCALE_FACTOR={os.environ.get('QT_SCALE_FACTOR', 'Not set')}")

    def setup_ui(self):
        setup_ui(self)

    def update_output_button_style(self, name, is_current, is_other):
        update_output_button_style(self, name, is_current, is_other)

    def toggle_output(self, tv_name, checked):
        toggle_output(self, tv_name, checked)

    def file_selected(self, item):
        file_selected(self, item)

    def open_schedule_dialog(self):
        open_schedule_dialog(self)

    def update_sync_status(self, status):
        update_sync_status(self, status)

    def update_playback_state(self):
        update_playback_state(self)