# config.py: Centralized configuration for the media kiosk project
#
# Overview:
# Defines hardcoded values that may need to be changed, such as filepaths, TV outputs,
# input sources, and UI constants. Used by kiosk.py, source_screen.py, and related files.
#
# Categories:
# - Filepaths: Directories and files for logs, videos, icons, etc., all under /home/admin/kiosk/.
# - TV Outputs: Names and mappings for TV outputs.
# - Inputs: Source names, input numbers, and types.
# - UI: Window sizes, colors, fonts, button sizes, spacing, etc.
# - Other: PIN, input numbers, etc.
#
# Recent Changes (as of June 2025):
# - Updated filepaths to use /home/admin/kiosk/ as project root.

# Filepaths (all project files under /home/admin/kiosk/)
PROJECT_ROOT = "/home/admin/kiosk"
LOG_DIR = f"{PROJECT_ROOT}/logs"
LOG_FILE = f"{LOG_DIR}/kiosk.log"
VIDEO_DIR = f"{PROJECT_ROOT}/videos"
ICON_DIR = f"{PROJECT_ROOT}/icons"
SCHEDULE_FILE = f"{PROJECT_ROOT}/schedule.json"
NETWORK_SHARE_DIR = "/mnt/share"  # External mount
USB_STORAGE_DIR = "/mnt/usb"      # External mount
ICON_FILES = {
    "play": "play.png",
    "stop": "stop.png",
    "pause": "pause.png"
}

# TV Outputs
TV_OUTPUTS = {
    "Fellowship 1": 1,
    "Fellowship 2": 2,
    "Nursery": 3,
    "Sanctuary": 4
}
TOTAL_TV_OUTPUTS = len(TV_OUTPUTS)

# Inputs
INPUTS = {
    "Local Files": {"input_num": 2, "type": "video"},
    "Audio": {"input_num": 1, "type": "audio"},
    "DVD": {"input_num": 3, "type": "dvd"},
    "Web": {"input_num": 4, "type": "web"}
}
TOTAL_INPUTS = len(INPUTS)

# UI Constants
WINDOW_SIZE = (787, 492)  # Main window (width, height)
AUTH_DIALOG_SIZE = (245, 184)
QT_PLATFORM = "xcb"
MAIN_WINDOW_GRADIENT = ("#2c3e50", "#34495e")  # Start, end colors
LABEL_COLOR = "white"
SOURCE_SCREEN_BACKGROUND = "#2a3b5e"

# Fonts
TITLE_FONT = ("Arial", 28, "Bold")
WIDGET_FONT = ("Arial", 20)
BACK_BUTTON_FONT = ("Arial", 16)

# Colors
SCHEDULE_BUTTON_COLOR = "#4caf50"  # Green
PLAY_BUTTON_COLOR = "#4caf50"  # Green
STOP_BUTTON_COLOR = "#e53935"  # Red
SYNC_STATUS_COLOR = "#ffc107"  # Yellow
PLAYBACK_STATUS_COLORS = {"playing": "#4caf50", "stopped": "#e53935"}  # Green, red
OUTPUT_BUTTON_COLORS = {
    "selected": "#1f618d",  # Blue
    "other": "#c0392b",     # Red
    "unselected": "#7f8c8d" # Gray
}
BACK_BUTTON_COLOR = "#7f8c8d"  # Gray
TEXT_COLOR = "#ffffff"  # White
FILE_LIST_BORDER_COLOR = "#ffffff"  # White

# Sizes
FILE_LIST_HEIGHT = 260  # px
FILE_LIST_ITEM_HEIGHT = 60  # px
SCHEDULE_BUTTON_SIZE = (180, 60)  # width, height
OUTPUT_BUTTON_SIZE = (180, 60)
PLAY_STOP_BUTTON_SIZE = (120, 120)
BACK_BUTTON_SIZE = (80, 40)
ICON_SIZE = (112, 112)

# Spacing and Padding
MAIN_LAYOUT_SPACING = 20  # px
TOP_LAYOUT_SPACING = 20
OUTPUTS_CONTAINER_SPACING = 10
OUTPUT_LAYOUT_SPACING = 5
BUTTONS_LAYOUT_SPACING = 15
RIGHT_LAYOUT_SPACING = 20
BUTTON_PADDING = {"schedule_output": 10, "back": 5, "play_stop": 2}
FILE_LIST_PADDING = 5
BORDER_RADIUS = 8  # px

# Other
PIN = "1234"  # Hardcoded PIN (bypassed)
LOCAL_FILES_INPUT_NUM = 2