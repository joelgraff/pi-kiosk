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
# - Videos: /home/admin/videos.
#
# Recent Changes (as of June 2025):
# - Added import os for QT_SCALE_FACTOR logging.
# - Moved setup_ui import to top for early error detection.
# - Enhanced import logging to debug circular imports.
#
# Dependencies:
# - PyQt5: GUI framework.
# - source_screen_ui.py: UI setup and event handlers.
# - utilities.py.

from PyQt5.QtWidgets import QWidget
import logging
import os
import sys

try:
    from source_screen_ui import setup_ui
    logging.debug("SourceScreen: Successfully imported setup_ui")
except ImportError as e:
    logging.error(f"SourceScreen: Failed to import setup_ui: {e}")
    logging.error(f"SourceScreen: sys.path: {sys.path}")
    logging.error(f"SourceScreen: sys.modules: {list(sys.modules.keys())}")
    raise

class SourceScreen:
    def __init__(self, parent, source_name):
        self.parent = parent
        self.source_name = source_name
        self.widget = QWidget()
        self.output_buttons = {}  # Store output toggle buttons
        self.file_list = None  # Set in setup_ui
        self.play_button = None  # Set in setup_ui
        self.stop_button = None  # Set in setup_ui
        self.sync_status_label = None  # Set in setup_ui
        self.playback_state_label = None  # Set in setup_ui
        self.setup_ui()
        logging.debug(f"SourceScreen: Initialized for {self.source_name}")
        logging.debug(f"SourceScreen: QT_SCALE_FACTOR={os.environ.get('QT_SCALE_FACTOR', 'Not set')}")

    def setup_ui(self):
        try:
            setup_ui(self)
        except Exception as e:
            logging.error(f"SourceScreen: Failed to execute setup_ui: {e}")
            raise