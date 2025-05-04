# kiosk.py: Main application for the media kiosk
#
# Overview:
# Initializes the media kiosk application on Raspberry Pi 5 with X11.
# Sets up the main window (KioskGUI), logging, and signal handling.
#
# Environment:
# - Raspberry Pi 5, X11 (QT_QPA_PLATFORM=xcb), PyQt5, 787x492px main window.
# - Logs: /home/admin/kiosk/logs/kiosk.log.
# - Videos: /home/admin/videos.
#
# Dependencies:
# - PyQt5: GUI framework.
# - config.py: Configuration constants.
# - interface.py: Main interface setup.
# - playback.py: Media playback management.
# - utilities.py: Signal handling and scheduling.

import os
import sys
import logging
import signal
from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel
from PyQt5.QtCore import Qt

try:
    from config import (
        QT_PLATFORM, LOG_FILE, MAIN_WINDOW_GRADIENT, LABEL_COLOR,
        WINDOW_SIZE, INPUTS, FONT_FAMILY, FONT_SIZES
    )
    from interface import Interface
    from playback import Playback
    from utilities import SyncNetworkShare, signal_handler
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

class KioskGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        logging.debug("KioskGUI: Initializing")
        self.interface = None
        self.playback = None
        self.sync_manager = None
        self.input_output_map = {}  # {input_num: [output_indices]}
        self.active_inputs = {}  # {input_num: bool}
        self.source_states = {}  # {source_name: bool}
        self.init_logging()
        self.init_ui()
        self.init_playback()
        self.init_sync()
        logging.debug("KioskGUI: Initialization complete")

    def init_logging(self):
        try:
            os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
            logging.basicConfig(
                filename=LOG_FILE,
                level=logging.DEBUG,
                format="%(asctime)s,%(msecs)d %(levelname)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            logging.debug("KioskGUI: Logging initialized")
        except Exception as e:
            print(f"Failed to initialize logging: {e}")
            sys.exit(1)

    def init_ui(self):
        try:
            logging.debug(f"KioskGUI: Setting window size to {WINDOW_SIZE}")
            if not isinstance(WINDOW_SIZE, (tuple, list)) or len(WINDOW_SIZE) != 2:
                logging.error(f"KioskGUI: Invalid WINDOW_SIZE: {WINDOW_SIZE}")
                raise ValueError("WINDOW_SIZE must be a tuple of (width, height)")
            width, height = WINDOW_SIZE
            self.setFixedSize(width, height)
            self.setStyleSheet(MAIN_WINDOW_GRADIENT)

            # Initialize interface
            self.interface = Interface(self)
            self.setCentralWidget(self.interface.widget)

            # Example label for testing LABEL_COLOR
            self.status_label = QLabel("Media Kiosk", self)
            self.status_label.setStyleSheet(f"color: {LABEL_COLOR}; background: transparent; font: {FONT_SIZES['tile']}px {FONT_FAMILY};")
            self.status_label.setAlignment(Qt.AlignCenter)
            self.status_label.resize(width, 30)
            self.status_label.move(0, height - 30)

            logging.debug("KioskGUI: UI initialized")
        except Exception as e:
            logging.error(f"KioskGUI: Failed to initialize UI: {e}")
            raise

    def init_playback(self):
        try:
            self.playback = Playback()
            if self.playback is None:
                raise ValueError("Playback initialization returned None")
            logging.debug("KioskGUI: Playback initialized")
        except Exception as e:
            logging.error(f"KioskGUI: Failed to initialize playback: {e}")
            self.playback = None  # Explicitly set to None for clarity
            raise  # Re-raise to halt initialization if playback fails

    def init_sync(self):
        try:
            self.sync_manager = SyncNetworkShare()
            self.sync_manager.progress.connect(self.interface.update_sync_status)
            self.sync_manager.progress.connect(self.update_source_sync_status)
            logging.debug("KioskGUI: Sync manager initialized")
        except Exception as e:
            logging.error(f"KioskGUI: Failed to initialize sync manager: {e}")
            raise

    def update_source_sync_status(self, status):
        logging.debug(f"KioskGUI: Sync status updated: {status}")
        if self.interface and hasattr(self.interface, 'source_screens'):
            for source_name, screen in self.interface.source_screens.items():
                if source_name == "Local Files":
                    screen.sync_status_label.setText(f"Network Sync: {status}")
                    screen.sync_status_label.update()

    def closeEvent(self, event):
        logging.debug("KioskGUI: Closing application")
        try:
            if self.playback is not None:
                self.playback.stop_all_playback()
            else:
                logging.warning("KioskGUI: No playback instance available to stop")
        except Exception as e:
            logging.error(f"KioskGUI: Failed to stop playback: {e}")
        event.accept()

def main():
    try:
        # Set Qt platform
        os.environ["QT_QPA_PLATFORM"] = QT_PLATFORM
        logging.debug(f"Main: Set QT_QPA_PLATFORM to {QT_PLATFORM}")

        # Initialize application
        app = QApplication(sys.argv)
        app.setStyle("Fusion")

        # Initialize KioskGUI
        gui = KioskGUI()
        gui.show()

        # Set up signal handling
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        logging.debug("Main: Application started")
        sys.exit(app.exec_())
    except Exception as e:
        logging.error(f"Main: Application failed: {e}")
        print(f"Application failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()