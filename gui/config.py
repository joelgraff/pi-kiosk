# config.py: Centralized configuration for the media kiosk
#
# Overview:
# Defines constants for the media kiosk on Raspberry Pi 5 with X11.
# Includes file paths, TV outputs, HDMI mappings, input sources, and UI settings.
#
# Environment:
# - Raspberry Pi 5, X11 (QT_QPA_PLATFORM=xcb), PyQt5, 787x492px main window.
# - Logs: /home/admin/kiosk/logs/kiosk.log.
# - Icons: /home/admin/kiosk/icons (128x128px).
# - Videos: /home/admin/videos.

import os

# Qt Platform
QT_PLATFORM = "xcb"  # X11 platform for Raspberry Pi 5

# Filepaths
PROJECT_ROOT = "/home/admin/kiosk"
VIDEO_DIR = "/home/admin/videos"
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
LOG_FILE = os.path.join(LOG_DIR, "kiosk.log")  # Main application log file
MPV_LOG_FILE = os.path.join(LOG_DIR, "mpv.log")  # mpv log file
SCHEDULE_FILE = os.path.join(PROJECT_ROOT, "schedule.json")
ICON_DIR = os.path.join(PROJECT_ROOT, "icons")

# TV Outputs (key: name, value: index)
TV_OUTPUTS = {
    "Fellowship 1": 0,
    "Fellowship 2": 1,
    "Fellowship 3": 2,
}

# HDMI Outputs (key: HDMI port index, value: list of TV output indices)
HDMI_OUTPUTS = {
    0: [0],  # HDMI-A-1: Fellowship 1
    1: [1],  # HDMI-A-2: Fellowship 2
    2: [2],  # HDMI-A-3: Fellowship 3
}

# Input Sources (key: name, value: input number for matrix routing)
INPUTS = {
    "Local Files": 2,
    "Audio": 3,
    "DVD": 4,
    "Web": 5,
}

# Dynamic Input Number Generator for Multiple Files
NEXT_INPUT_NUM = 100  # Start at 100 to avoid conflicts with INPUTS

def get_next_input_num():
    global NEXT_INPUT_NUM
    input_num = NEXT_INPUT_NUM
    NEXT_INPUT_NUM += 1
    return input_num

# Local Files Input Number (base for single-file mode)
LOCAL_FILES_INPUT_NUM = INPUTS["Local Files"]

# UI Constants
WINDOW_SIZE = (787, 492)
TILE_SIZE = (245, 190)
OUTPUT_BUTTON_SIZE = (245, 184)
SCHEDULE_BUTTON_SIZE = (245, 92)
FILE_LIST_ITEM_HEIGHT = 48
PIN = "1234"  # Default PIN for auth_dialog

# Colors
TILE_COLOR = "#0078D7"
TILE_TEXT_COLOR = "white"
OUTPUT_BUTTON_COLORS = {
    "selected": "#0078D7",  # Blue for current input
    "other": "#D83B01",     # Red for other inputs
    "unselected": "#808080" # Gray for unassigned
}
PLAY_BUTTON_COLOR = "#0078D7"
STOP_BUTTON_COLOR = "#D83B01"
SCHEDULE_BUTTON_COLOR = "#0078D7"
TEXT_COLOR = "white"
BACKGROUND_COLOR = "black"
PLAYBACK_STATUS_COLORS = {
    "playing": "#00FF00",  # Green
    "stopped": "#FF0000"   # Red
}

# Fonts
FONT_FAMILY = "Arial"
FONT_SIZES = {
    "tile": 14,
    "output": 14,
    "schedule": 12,
    "playback_status": 12,
    "file_list": 12
}

# Icon Files (128x128px)
ICON_FILES = {
    "local_files": "local_files.png",
    "audio": "audio.png",
    "dvd": "dvd.png",
    "web": "web.png",
    "stop_all": "stop_all.png",
    "play": "play.png",
    "pause": "pause.png"
}

# Button Padding
BUTTON_PADDING = {
    "tile": 10,
    "play_stop": 10,
    "schedule_output": 8
}

# Border Radius
BORDER_RADIUS = 5