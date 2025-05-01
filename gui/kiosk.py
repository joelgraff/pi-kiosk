# kiosk.py: Main application file for the media kiosk GUI
#
# Overview:
# This file defines the KioskGUI class, the primary PyQt5 application window for a media kiosk
# running on a Raspberry Pi 5 with X11 (QT_QPA_PLATFORM=xcb). The application provides a
# touchscreen interface (787x492px window, mimicking a 10" display on a 24" 1920x1080 monitor)
# for managing media playback (via mpv), network share syncing, and scheduling. It handles
# authentication, source selection (e.g., Local Files, Web, Cast), and navigation between screens.
#
# Key Functionality:
# - Initializes a fixed-size main window (787x492px, gradient background) with a QStackedWidget
#   for screen navigation.
# - Displays AuthDialog (245x184px, PIN 1234, frameless, standalone) at startup, hiding the
#   main window until authentication succeeds.
# - Manages source screens (e.g., Local Files: 30pt title, 20pt fonts, 2/3 file listbox,
#   1/3 TV outputs with yellow #f1c40f text) via show_source_screen.
# - Coordinates playback (via playback.py), network sync (via utilities.py), and scheduling
#   (via schedule library and schedule_dialog.py).
# - Maintains state: input_map (source-to-input mapping), input_paths (input-to-file/URL),
#   input_output_map (input-to-outputs), active_inputs (playback status), media_processes (mpv PIDs).
#
# Environment:
# - Raspberry Pi 5, X11, PyQt5, mpv for playback.
# - Logs: /home/admin/gui/logs/kiosk.log (app), /home/admin/gui/logs/mpv.log (mpv output),
#   /home/admin/gui/logs/mpv_err.log (mpv errors).
# - Videos: /home/admin/videos (local), /mnt/share (network share), /mnt/usb (USB storage).
# - Icons: /home/admin/gui/icons (64x64px for sources/playback, 61x61px for buttons, 32x32px for back).
#
# Integration Notes:
# - AuthDialog (auth_dialog.py) is displayed standalone (no parent) to ensure visibility.
# - SourceScreen (output_dialog.py or source_screen.py) handles source-specific UI, with the
#   updated version in output_dialog.py supporting Web, Cast, and USB storage.
# - OutputDialog (output_dialog.py) configures TV outputs (Fellowship 1, Fellowship 2, Nursery).
# - Flask server (flask_server.py) provides wireless connectivity but uses VLC; align with mpv.
# - Cleanup script (cleanup_videos.py) runs daily to manage disk space.
#
# Recent Fixes (as of April 2025):
# - Fixed AuthDialog visibility: Standalone, QTimer delay, screen-centered, Qt.FramelessWindowHint.
# - Hid main window until authentication by removing kiosk.show() from main block.
# - Added show_source_screen to resolve AttributeError in interface.py.
# - Added input_map to fix AttributeError in playback.py.
# - Mitigated GLib-GObject-CRITICAL errors with disconnect() and deleteLater().
# - Fixed schedule import in utilities.py.
#
# Known Considerations:
# - Network share sync (utilities.py) takes ~45 seconds for large files due to SD card writes; acceptable performance.
# - Flask server uses VLC; modify to use mpv for consistency (see flask_server.py).
# - Default to Fellowship 1 (output 1) if no outputs selected (implement in playback.py).
# - SourceScreen implementation in output_dialog.py may replace source_screen.py; confirm.
# - PIN is hardcoded (1234); consider secure storage for production.
#
# Dependencies:
# - PyQt5: GUI framework.
# - schedule: Task scheduling.
# - mpv: Media playback (external binary).
# - Files: auth_dialog.py, interface.py, playback.py, output_dialog.py, source_screen.py,
#   utilities.py, schedule_dialog.py.

import sys
import os
import signal
import hashlib
import threading
import logging
import schedule
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QWidget, QDialog, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QRect, QtMsgType, QMetaObject, Q_ARG, pyqtSlot, QTimer
from PyQt5.QtGui import QScreen
from auth_dialog import AuthDialog
from interface import Interface
from playback import Playback
from utilities import signal_handler, run_scheduler, load_schedule, SyncNetworkShare

# Custom Qt message handler to log Qt messages (e.g., warnings, errors) to kiosk.log and console
def qt_message_handler(msg_type, context, msg):
    log_levels = {
        QtMsgType.QtDebugMsg: logging.DEBUG,
        QtMsgType.QtInfoMsg: logging.INFO,
        QtMsgType.QtWarningMsg: logging.WARNING,
        QtMsgType.QtCriticalMsg: logging.ERROR,
        QtMsgType.QtFatalMsg: logging.CRITICAL
    }
    logging.log(log_levels.get(msg_type, logging.INFO), f"Qt: {msg}")
    print(f"Qt: {msg}")

# Set up logging to /home/admin/gui/logs/kiosk.log with detailed timestamps
logging.basicConfig(
    filename="/home/admin/gui/logs/kiosk.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s: %(message)s"
)

# Ensure required directories exist for logs, videos, and icons
try:
    os.makedirs("/home/admin/gui/logs", exist_ok=True)
    os.makedirs("/home/admin/videos", exist_ok=True)
    os.makedirs("/home/admin/gui/icons", exist_ok=True)
except Exception as e:
    logging.error(f"Failed to create directories: {e}")
    print(f"Error creating directories: {e}")
    sys.exit(1)

# Set up signal handling for graceful shutdown (SIGINT, SIGTERM)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

class KioskGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        logging.debug("Initializing KioskGUI")
        try:
            # Set window title and fixed size (787x492px to mimic 10" touchscreen)
            self.setWindowTitle("Media Kiosk")
            self.setFixedSize(787, 492)
            self.setStyleSheet("""
                QMainWindow {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                                stop:0 #2c3e50, stop:1 #34495e);
                }
                QLabel {
                    color: white;
                }
            """)
            # Initialize QStackedWidget for screen navigation
            self.stack = QStackedWidget()
            self.setCentralWidget(self.stack)
            self.source_screens = []

            # Initialize state variables
            self.input_map = {
                "Local Files": 2,
                "Audio": 1,
                "DVD": 3,
                "Web": 4
            }  # Maps source names to input numbers for playback
            self.input_paths = {}  # Maps input numbers to video file paths (set by source_screen.py)
            self.input_output_map = {}  # Maps input numbers to output lists (set by OutputDialog)
            self.active_inputs = {}  # Tracks active playback inputs
            self.selected_source = None  # Currently selected source
            self.media_processes = {}  # Tracks mpv subprocesses
            self.authenticated = False  # Authentication status
            logging.debug(f"Initialized input_map: {self.input_map}")

            # Initialize playback and interface
            logging.debug("Initializing Playback")
            self.playback = Playback(self)
            logging.debug("Initializing Interface")
            self.interface = Interface(self)
            self.stack.addWidget(self.interface.main_widget)

            # Initialize network sync (SyncNetworkShare from utilities.py)
            self.sync_manager = SyncNetworkShare()
            self.sync_manager.progress.connect(self.interface.update_sync_status)
            self.sync_manager.progress.connect(self.update_source_sync_status)

            # Start scheduler thread for daily tasks (uses schedule library)
            logging.debug("Starting scheduler thread")
            self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
            self.scheduler_thread.start()
            self.load_and_apply_schedule()

            # Delay AuthDialog display until event loop starts
            QTimer.singleShot(0, self.show_auth_dialog)
        except Exception as e:
            logging.error(f"Initialization failed: {e}")
            print(f"Initialization failed: {e}")
            sys.exit(1)

    def show_auth_dialog(self):
        # Displays AuthDialog (no parent, 245x184px, frameless) for PIN entry
        try:
            logging.debug("Creating AuthDialog")
            dialog = AuthDialog()  # No parent to ensure independent display
            dialog.setFixedSize(245, 184)
            dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            # Center dialog on screen
            screen = QApplication.primaryScreen().geometry()
            dialog_rect = QRect(0, 0, 245, 184)
            dialog_rect.moveCenter(screen.center())
            dialog.setGeometry(dialog_rect)
            logging.debug(f"AuthDialog geometry: {dialog_rect.getRect()}")
            logging.debug(f"AuthDialog visible before show: {dialog.isVisible()}")
            dialog.setVisible(True)
            dialog.show()
            dialog.raise_()
            dialog.activateWindow()
            dialog.repaint()
            logging.debug(f"AuthDialog visible after show: {dialog.isVisible()}")
            logging.debug("Executing AuthDialog")
            result = dialog.exec_()
            logging.debug(f"AuthDialog returned: {result}")
            if result == QDialog.Accepted:
                pin = dialog.get_pin()
                logging.debug(f"PIN entered: {pin}")
                expected_pin = hashlib.sha256("1234".encode()).hexdigest()
                logging.debug(f"Expected PIN hash: {expected_pin}")
                if pin == expected_pin:
                    self.authenticated = True
                    logging.debug("Authentication successful, starting network share sync in thread")
                    sync_thread = threading.Thread(target=self.sync_manager.sync, daemon=True)
                    sync_thread.start()
                    logging.debug("Calling show_controls")
                    self.show_controls()
                else:
                    logging.warning("Incorrect PIN entered")
                    self.show_auth_dialog()
            else:
                logging.info("Auth dialog closed without accepting")
                sys.exit(0)
        except Exception as e:
            logging.error(f"Auth dialog error: {e}")
            print(f"Auth dialog error: {e}")
            sys.exit(1)

    def show_controls(self):
        # Shows the main interface (tile buttons) after authentication
        try:
            logging.debug("Checking stack and main_widget")
            logging.debug(f"main_widget exists: {self.interface.main_widget is not None}")
            logging.debug(f"main_widget visible: {self.interface.main_widget.isVisible() if self.interface.main_widget else False}")
            logging.debug(f"main_widget geometry: {self.interface.main_widget.geometry().getRect() if self.interface.main_widget else None}")
            logging.debug(f"main_widget parent: {self.interface.main_widget.parent() if self.interface.main_widget else None}")
            logging.debug(f"Removing {len(self.source_screens)} source screen widgets")
            for widget in self.source_screens:
                try:
                    widget.disconnect()
                except Exception as e:
                    logging.debug(f"No signals to disconnect for widget: {e}")
                self.stack.removeWidget(widget)
                widget.deleteLater()
            self.source_screens.clear()
            self.interface.main_widget.setVisible(True)
            self.interface.main_widget.show()
            self.stack.setCurrentWidget(self.interface.main_widget)
            self.stack.update()
            self.update()
            self.repaint()
            logging.debug(f"Main window visible: {self.isVisible()}, geometry: {self.geometry().getRect()}")
            self.show()  # Ensure main window is shown
        except Exception as e:
            logging.error(f"Failed to show controls: {e}")
            print(f"Failed to show controls: {e}")
            sys.exit(1)

    def show_source_screen(self, source_name):
        # Displays a SourceScreen (e.g., Local Files) when a source is selected
        try:
            from source_screen import SourceScreen
            source_screen = SourceScreen(self, source_name)
            self.source_screens.append(source_screen.widget)
            self.stack.addWidget(source_screen.widget)
            self.stack.setCurrentWidget(source_screen.widget)
            logging.debug(f"Displayed source screen for {source_name}")
        except Exception as e:
            logging.error(f"Failed to show source screen for {source_name}: {e}")
            print(f"Failed to show source screen: {e}")
            sys.exit(1)

    @pyqtSlot(str)
    def update_source_sync_status(self, status):
        # Updates sync status on Local Files screen
        try:
            current_widget = self.stack.currentWidget()
            if hasattr(current_widget, 'source_screen') and current_widget.source_screen.source_name == "Local Files":
                current_widget.source_screen.update_sync_status(status)
        except Exception as e:
            logging.error(f"Failed to update source sync status: {e}")

    def load_and_apply_schedule(self):
        # Loads and applies scheduled playback tasks from /home/admin/gui/schedule.json
        try:
            sched = load_schedule()
            for task in sched:
                if task["repeat"] == "Daily":
                    schedule.every().day.at(task["time"]).do(
                        self.playback.execute_scheduled_task,
                        input_num=task["input"],
                        outputs=task["outputs"],
                        path=task.get("path")
                    )
            logging.debug("Schedule loaded and applied")
        except Exception as e:
            logging.error(f"Failed to load schedule: {e}")
            print(f"Failed to load schedule: {e}")

if __name__ == '__main__':
    try:
        logging.debug("Starting application")
        os.environ["QT_QPA_PLATFORM"] = "xcb"
        app = QApplication(sys.argv)
        from PyQt5.QtCore import qInstallMessageHandler
        qInstallMessageHandler(qt_message_handler)
        kiosk = KioskGUI()
        logging.debug(f"Main window visible at startup: {kiosk.isVisible()}, geometry: {kiosk.geometry().getRect()}")
        sys.exit(app.exec_())
    except Exception as e:
        logging.error(f"Application failed: {e}")
        print(f"Application failed: {e}")
        sys.exit(1)