# utilities.py: Utility functions for the media kiosk
#
# Overview:
# This file provides utility functions for the media kiosk application on a Raspberry Pi 5
# with X11, including signal handling, scheduling, network share syncing, output routing,
# and file/schedule management. It supports the main application (kiosk.py) by managing
# background tasks and system integration.
#
# Key Functionality:
# - signal_handler: Gracefully shuts down the application on SIGINT/SIGTERM.
# - run_scheduler: Runs the schedule loop for daily playback tasks.
# - load_schedule: Loads schedule.json for task scheduling.
# - save_schedule: Saves schedule data to schedule.json.
# - list_files: Lists .mp4/.mkv files in a directory.
# - SyncNetworkShare: Syncs files from /mnt/share to /home/admin/videos.
# - stub_matrix_route: Simulates routing inputs to outputs (placeholder).
#
# Environment:
# - Raspberry Pi 5, X11 (QT_QPA_PLATFORM=xcb), PyQt5, 787x492px main window.
# - Logs: /home/admin/gui/logs/kiosk.log (app logs, including sync progress).
# - Videos: /home/admin/videos (local), /mnt/share (network share).
# - Schedule file: /home/admin/gui/schedule.json.
#
# Integration Notes:
# - Used by kiosk.py, source_screen.py, and other components for scheduling and file operations.
# - list_files and save_schedule added for SourceScreen/OutputDialog compatibility.
#
# Recent Changes (as of May 2025):
# - Added list_files and save_schedule to resolve ImportError in source_screen.py.
# - Fixed NameError for schedule import.
# - Added stub_matrix_route for playback routing simulation.
# - Made SyncNetworkShare thread-safe with progress signals.
#
# Known Considerations:
# - Network share sync (~45 seconds for large files) is acceptable due to SD card writes.
# - stub_matrix_route is a placeholder; replace with hardware routing if needed.
# - Ensure /mnt/share is mounted before sync (sudo mount -t cifs).
# - Schedule file (/home/admin/gui/schedule.json) needs validation.
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
    logging.info(f"Received signal {sig}, shutting down")
    sys.exit(0)

def run_scheduler():
    logging.debug("Starting scheduler")
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            logging.error(f"Scheduler error: {e}")

def load_schedule():
    schedule_file = "/home/admin/gui/schedule.json"
    try:
        if os.path.exists(schedule_file):
            with open(schedule_file, "r") as f:
                return json.load(f)
        return []
    except Exception as e:
        logging.error(f"Failed to load schedule: {e}")
        return []

def save_schedule(schedule_data):
    schedule_file = "/home/admin/gui/schedule.json"
    try:
        os.makedirs(os.path.dirname(schedule_file), exist_ok=True)
        with open(schedule_file, "w") as f:
            json.dump(schedule_data, f, indent=4)
        logging.debug(f"Saved schedule to {schedule_file}")
    except Exception as e:
        logging.error(f"Failed to save schedule: {e}")

def list_files(directory):
    try:
        if not os.path.exists(directory):
            logging.warning(f"Directory does not exist: {directory}")
            return []
        files = [f for f in os.listdir(directory) if f.endswith((".mp4", ".mkv"))]
        logging.debug(f"Listed files in {directory}: {files}")
        return files
    except Exception as e:
        logging.error(f"Failed to list files in {directory}: {e}")
        return []

class SyncNetworkShare(QObject):
    progress = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        logging.debug("Initializing SyncNetworkShare")

    def sync(self):
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
                    time.sleep(0.1)
                except Exception as e:
                    logging.error(f"Failed to sync {file}: {e}")
                    self.progress.emit(f"Failed to sync {file}")
            
            logging.info("Sync completed")
            self.progress.emit("Sync completed")
        except Exception as e:
            logging.error(f"Sync failed: {e}")
            self.progress.emit("Sync failed")

def stub_matrix_route(input_num, outputs):
    try:
        logging.debug(f"Routing input {input_num} to outputs {outputs}")
        return True
    except Exception as e:
        logging.error(f"Routing failed for input {input_num} to outputs {outputs}: {e}")
        return False