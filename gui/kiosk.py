# kiosk.py: Main application file for the media kiosk GUI
#
# Overview:
# This file defines the KioskGUI class, the primary PyQt5 application window for a media kiosk
# running on a Raspberry Pi 5 with X11 (QT_QPA_PLATFORM=xcb). The application provides a
# touchscreen interface (787x492px window, mimicking a 10" display on a 24" 1920x1080 monitor)
# for managing media playback (via mpv), network share syncing, and scheduling. It handles
# source selection (e.g., Local Files, Web, Cast), and navigation between screens.
#
# Key Functionality:
# - Initializes a fixed-size main window (787x492px, gradient background) with a QStackedWidget
#   for screen navigation.
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
# Recent Changes (as of June 2025):
# - Temporarily disabled authentication to bypass PIN prompt, directly showing controls.
#
# Dependencies:
# - PyQt5: GUI framework.
# - schedule: Task scheduling.
# - mpv: Media playback (external binary).
# - Files: interface.py, playback.py, output_dialog.py, source_screen.py,
#   utilities.py, schedule_dialog.py.

import sys
import os
import signal
import threading
import logging
import schedule
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QWidget
from PyQt5.QtCore import Qt, QtMsgType, QTimer
from interface import Interface
from playback import Playback
from utilities import signal_handler, run_scheduler, load_schedule, SyncNetworkShare

# Custom Qt message handler to log Qt messages
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

# Set up logging
logging.basicConfig(
    filename="/home/admin/gui/logs/kiosk.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s: %(message)s"
)

# Ensure required directories
try:
    os.makedirs("/home/admin/gui/logs", exist_ok=True)
    os.makedirs("/home/admin/videos", exist_ok=True)
    os.makedirs("/home/admin/gui/icons", exist_ok=True)
except Exception as e:
    logging.error(f"Failed to create directories: {e}")
    sys.exit(1)

# Set up signal handling
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

class KioskGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        logging.debug("Initializing KioskGUI")
        try:
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
            self.stack = QStackedWidget()
            self.setCentralWidget(self.stack)
            self.source_screens = []

            self.input_map = {
                "Local Files": 2,
                "Audio": 1,
                "DVD": 3,
                "Web": 4
            }
            self.input_paths = {}
            self.input_output_map = {}
            self.active_inputs = {}
            self.selected_source = None
            self.media_processes = {}
            self.authenticated = True  # Bypass authentication
            logging.debug(f"Initialized input_map: {self.input_map}")

            logging.debug("Initializing Playback")
            self.playback = Playback(self)
            logging.debug("Initializing Interface")
            self.interface = Interface(self)
            self.stack.addWidget(self.interface.main_widget)

            self.sync_manager = SyncNetworkShare()
            self.sync_manager.progress.connect(self.interface.update_sync_status)
            self.sync_manager.progress.connect(self.update_source_sync_status)

            logging.debug("Starting scheduler thread")
            self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
            self.scheduler_thread.start()
            self.load_and_apply_schedule()

            # Directly show controls, bypassing auth_dialog
            QTimer.singleShot(0, self.show_controls)
        except Exception as e:
            logging.error(f"Initialization failed: {e}")
            sys.exit(1)

    def show_controls(self):
        try:
            logging.debug("Showing controls")
            for widget in self.source_screens:
                try:
                    widget.disconnect()
                except Exception:
                    pass
                self.stack.removeWidget(widget)
                widget.deleteLater()
            self.source_screens.clear()
            self.interface.main_widget.setVisible(True)
            self.interface.main_widget.show()
            self.stack.setCurrentWidget(self.interface.main_widget)
            self.show()
            logging.debug("Controls displayed")
            # Start network share sync
            sync_thread = threading.Thread(target=self.sync_manager.sync, daemon=True)
            sync_thread.start()
        except Exception as e:
            logging.error(f"Failed to show controls: {e}")
            sys.exit(1)

    def show_source_screen(self, source_name):
        try:
            from source_screen import SourceScreen
            source_screen = SourceScreen(self, source_name)
            self.source_screens.append(source_screen.widget)
            self.stack.addWidget(source_screen.widget)
            self.stack.setCurrentWidget(source_screen.widget)
            logging.debug(f"Displayed source screen for {source_name}")
        except Exception as e:
            logging.error(f"Failed to show source screen for {source_name}: {e}")
            sys.exit(1)

    def update_source_sync_status(self, status):
        try:
            current_widget = self.stack.currentWidget()
            if hasattr(current_widget, 'source_screen') and current_widget.source_screen.source_name == "Local Files":
                current_widget.source_screen.update_sync_status(status)
        except Exception as e:
            logging.error(f"Failed to update source sync status: {e}")

    def load_and_apply_schedule(self):
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

if __name__ == '__main__':
    try:
        logging.debug("Starting application")
        os.environ["QT_QPA_PLATFORM"] = "xcb"
        app = QApplication(sys.argv)
        from PyQt5.QtCore import qInstallMessageHandler
        qInstallMessageHandler(qt_message_handler)
        kiosk = KioskGUI()
        sys.exit(app.exec_())
    except Exception as e:
        logging.error(f"Application failed: {e}")
        sys.exit(1)