# cleanup_videos.py: Script for cleaning up old video files in the media kiosk
#
# Overview:
# This script schedules daily cleanup of video files (.mp4, .mkv) in /home/admin/videos
# that are older than 90 days or when disk space falls below 10% of total capacity. It
# runs on a Raspberry Pi 5 and is launched by autostart.sh as a background process.
#
# Key Functionality:
# - Deletes files in /home/admin/videos older than 90 days or if free disk space <10%.
# - Uses schedule library to run cleanup daily at 02:00.
# - Runs in a daemon thread to avoid blocking the main application.
# - Logs actions to console (not kiosk.log).
#
# Environment:
# - Raspberry Pi 5, X11, launched by autostart.sh.
# - Videos: /home/admin/videos (local storage).
#
# Integration Notes:
# - Launched by autostart.sh alongside flask_server.py and kiosk.py.
# - Independent of PyQt5 GUI; does not interact with KioskGUI state.
# - Consider adding logging to /home/admin/gui/logs/kiosk.log for consistency.
#
# Recent Additions (as of April 2025):
# - Added to resolve missing cleanup functionality.
#
# Known Considerations:
# - Console logging only; integrate with kiosk.log for unified logging.
# - Ensure VIDEO_DIR (/home/admin/videos) is accessible and writable.
# - Verify AGE_THRESHOLD_DAYS (90) and SPACE_THRESHOLD_PERCENT (10%) suit use case.
#
# Dependencies:
# - schedule: Task scheduling.
# - os, shutil, datetime: For file operations and disk usage.
# - threading: For background scheduling.

import os
import time
import shutil
import schedule
import threading
import logging
from datetime import datetime, timedelta
from config import VIDEO_DIR, VIDEO_RETENTION_DAYS, MIN_FREE_SPACE_PERCENT, LOG_FILE, LOG_DIR

AGE_THRESHOLD_DAYS = VIDEO_RETENTION_DAYS
SPACE_THRESHOLD_PERCENT = MIN_FREE_SPACE_PERCENT

os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)

def get_disk_usage():
    stat = shutil.disk_usage(VIDEO_DIR)
    return (stat.free / stat.total) * 100

def cleanup_videos():
    logging.info("Running video cleanup")
    now = datetime.now()
    threshold_date = now - timedelta(days=AGE_THRESHOLD_DAYS)
    free_percent = get_disk_usage()

    for filename in os.listdir(VIDEO_DIR):
        file_path = os.path.join(VIDEO_DIR, filename)
        if not filename.endswith(('.mp4', '.mkv')):
            continue
        file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
        if file_mtime < threshold_date or free_percent < SPACE_THRESHOLD_PERCENT:
            logging.info(f"Deleting {file_path} (mtime: {file_mtime}, free space: {free_percent:.2f}%)")
            os.remove(file_path)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    os.makedirs(VIDEO_DIR, exist_ok=True)
    schedule.every().day.at("02:00").do(cleanup_videos)
    threading.Thread(target=run_scheduler, daemon=True).start()
    logging.info("Video cleanup scheduler started")
    while True:
        time.sleep(3600)  # Keep script running
