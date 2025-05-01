# utilities.py: Utility functions for the media kiosk
#
# Overview:
# This file provides utility functions for the media kiosk application on a Raspberry Pi 5
# with X11, including signal handling, scheduling, network share syncing, and output routing.
# It supports the main application (kiosk.py) by managing background tasks and system integration.
#
# Key Functionality:
# - signal_handler: Gracefully shuts down the application on SIGINT/SIGTERM.
# - run_scheduler: Runs the schedule loop for daily playback tasks.
# - load_schedule: Loads schedule.json for task scheduling.
# - SyncNetworkShare: Syncs files from /mnt/share to /home/admin/videos.
# - stub_matrix_route: Simulates routing inputs to outputs (placeholder for hardware integration).
#
# Environment:
# - Raspberry Pi 5, X11 (QT_QPA_PLATFORM=xcb), PyQt5, 787x492px main window.
# - Logs: /home/admin/gui/logs/kiosk.log (app logs, including sync progress).
# - Videos: /home/admin/videos (local), /mnt/share (network share).
# - Schedule file: /home/admin/gui/schedule.json.
#
# Recent Fixes (as of April 2025):
# - Fixed NameError for schedule by adding import.
# - Added stub_matrix_route for playback routing simulation.
# - Made SyncNetworkShare thread-safe with progress signals.
#
# Known Considerations:
# - Network share sync (~45 seconds for one file) may need optimization (e.g., async copying).
# - stub_matrix_route is a placeholder; replace with actual hardware routing if needed.
# - Ensure /mnt/share is mounted before sync (sudo mount -t cifs).
# - Schedule file format (schedule.json) needs validation.
#
# Dependencies:
# - PyQt5: For Qt signals in SyncNetworkShare.
# - schedule: For task scheduling.
# - json, os, shutil: For file operations.
# - threading, time: For sync and scheduling.

import sys
import os
import signal
import logging
import json
import shutil
import time
import schedule
import threading
from PyQt5.QtCore import QObject, pyqtSignal

def signal_handler(sig, frame):
    # Handles SIGINT/SIGTERM for graceful shutdown
    logging.info(f"Received signal {sig}, shutting down")
    sys.exit(0)

def run_scheduler():
    # Runs the schedule loop for daily playback tasks
    logging.debug("Starting scheduler")
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            logging.error(f"Scheduler error: {e}")

def load_schedule():
    # Loads schedule tasks from schedule.json
    schedule_file = "/home/admin/gui/schedule.json"
    try:
        if os.path.exists(schedule_file):
            with open(schedule_file, "r") as f:
                return json.load(f)
        return []
    except Exception as e:
        logging.error(f"Failed to load schedule: {e}")
        return []

class SyncNetworkShare(QObject):
    progress = pyqtSignal(str)  # Signal for sync progress updates

    def __init__(self):
        super().__init__()
        logging.debug("Initializing SyncNetworkShare")

    def sync(self):
        # Syncs files from /mnt/share to /home/admin/videos
        try:
            source_dir = "/mnt/share"
            dest_dir = "/home/admin/videos"
            if not os.path.exists(source_dir):
                logging.error(f"Source directory {source_dir} does not exist")
                self.progress.emit("Sync failed: Source not mounted")
                return
            
            files = [f for f in os.listdir(source_dir) if f.endswith((".mp4", ".mkv"))]
            total = len(files)
            if total == 0:
                logging.info("No files to sync")
                self.progress.emit("No files to sync")
                return
            
            for i, file in enumerate(files):
                src_path = os.path.join(source_dir, file)
                dst_path = os.path.join(dest_dir, file)
                try:
                    shutil.copy2(src_path, dst_path)
                    progress = f"Sync progress: {(i + 1) / total * 100:.0f}%"
                    logging.debug(progress)
                    self.progress.emit(progress)
                    time.sleep(0.1)  # Simulate delay for testing
                except Exception as e:
                    logging.error(f"Failed to sync {file}: {e}")
                    self.progress.emit(f"Failed to sync {file}")
            
            logging.info("Sync completed")
            self.progress.emit("Sync completed")
        except Exception as e:
            logging.error(f"Sync failed: {e}")
            self.progress.emit("Sync failed")

def stub_matrix_route(input_num, outputs):
    # Simulates routing an input to outputs (placeholder)
    try:
        logging.debug(f"Routing input {input_num} to outputs {outputs}")
        return True  # Simulate successful routing
    except Exception as e:
        logging.error(f"Routing failed for input {input_num} to outputs {outputs}: {e}")
        return False