# kiosk.py: Main application file for the media kiosk GUI
#
# Overview:
# This file defines the KioskGUI class, the primary PyQt5 application window for a media kiosk
# running on a Raspberry Pi 5 with X11. The application provides a touchscreen interface
# for managing media playback (via mpv), network share syncing, and scheduling. It handles
# source selection (e.g., Local Files, Web, Cast), and navigation between screens.
#
# Recent Changes (as of June 2025):
# - Temporarily disabled authentication to bypass PIN prompt.
# - Added missing import os.
# - Extracted hardcoded values to config.py.
#
# Dependencies:
# - PyQt5: GUI framework.
# - schedule: Task scheduling.
# - mpv: Media playback (external binary).
# - Files: interface.py, playback.py, output_dialog.py, source_screen.py,
#   utilities.py, schedule_dialog.py, config.py.

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
from config import LOG_DIR, LOG_FILE, VIDEO_DIR, ICON_DIR, INPUTS, WINDOW_SIZE, QT_PLATFORM, MAIN_WINDOW_GRADIENT, LABEL_COLOR

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
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s: %(message)s"
)

# Ensure required directories
try:
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(VIDEO_DIR, exist_ok=True)
    os.makedirs(ICON_DIR, exist_ok=True)
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
            self.setFixedSize(*WINDOW_SIZE)
            self.setStyleSheet(f"""
                QMainWindow {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                                stop:0 {MAIN_WINDOW_GRADIENT[0]}, stop:1 {MAIN_WINDOW_GRADIENT[1]});
                }}
                QLabel {{
                    color: {LABEL_COLOR};
                }}
            """)
            self.stack = QStackedWidget()
            self.setCentralWidget(self.stack)
            self.source_screens = []

            self.input_map = {name: info["input_num"] for name, info in INPUTS.items()}
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
        os.environ["QT_QPA_PLATFORM"] = QT_PLATFORM
        app = QApplication(sys.argv)
        from PyQt5.QtCore import qInstallMessageHandler
        qInstallMessageHandler(qt_message_handler)
        kiosk = KioskGUI()
        sys.exit(app.exec_())
    except Exception as e:
        logging.error(f"Application failed: {e}")
        sys.exit(1)