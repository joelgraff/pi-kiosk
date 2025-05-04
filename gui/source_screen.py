# source_screen.py: Main class for the source-specific screen (e.g., Local Files)
#
# Overview:
# Defines the SourceScreen class for the media kiosk on Raspberry Pi 5 with X11.
# Handles initialization, UI setup, and event handling.
#
# Environment:
# - Raspberry Pi 5, X11 (QT_QPA_PLATFORM=xcb), PyQt5, 787x492px window.
# - Logs: /home/admin/kiosk/logs/kiosk.log.
# - Icons: /home/admin/kiosk/icons (128x128px).
# - Videos: /home/admin/videos (Internal), /media/admin/<drive> (USB).
#
# Recent Changes (as of June 2025):
# - Added import os for QT_SCALE_FACTOR logging.
# - Moved setup_ui import to top for early error detection.
# - Enhanced import logging to debug circular imports.
# - Added event handlers (update_playback_state, on_play_clicked, on_stop_clicked,
#   toggle_output, update_output_button_style) to fix AttributeError.
# - Added MPV --fs-screen=n logic for multi-screen playback.
# - Added update_file_list, toggle_source, update_source_button_style for USB/Internal toggles.
# - Refined toggle_source and update_source_button_style for consistent styling and always-selected state.
# - Added gray text (#808080) for disabled USB button when no USB stick is inserted.
#
# Dependencies:
# - PyQt5: GUI framework.
# - source_screen_ui.py: UI setup.
# - utilities.py.

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize
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
        self.source_buttons = {}  # Store USB/Internal toggle buttons
        self.file_list = None  # Set in setup_ui
        self.play_button = None  # Set in setup_ui
        self.stop_button = None  # Set in setup_ui
        self.playback_state_label = None  # Set in setup_ui
        # Initialize USB/Internal state
        self.usb_path = None
        usb_base = "/media/admin/"
        if os.path.exists(usb_base) and os.listdir(usb_base):
            self.usb_path = os.path.join(usb_base, os.listdir(usb_base)[0])
        self.current_source = "Internal" if not self.usb_path else "USB"
        self.source_paths = {"Internal": "/home/admin/videos", "USB": self.usb_path}
        self.setup_ui()
        logging.debug(f"SourceScreen: Initialized for {self.source_name}")
        logging.debug(f"SourceScreen: QT_SCALE_FACTOR={os.environ.get('QT_SCALE_FACTOR', 'Not set')}")

    def setup_ui(self):
        try:
            setup_ui(self)
        except Exception as e:
            logging.error(f"SourceScreen: Failed to execute setup_ui: {e}")
            raise

    def update_playback_state(self):
        from config import ICON_DIR, ICON_FILES, PLAYBACK_STATUS_COLORS, PLAY_BUTTON_COLOR, TEXT_COLOR, ICON_SIZE, BORDER_RADIUS, BUTTON_PADDING
        from PyQt5.QtWidgets import QStyle
        logging.debug(f"SourceScreen: Updating playback state for {self.source_name}")
        is_playing = self.parent.interface.source_states.get(self.source_name, False)
        state = "Playing" if is_playing else "Stopped"
        self.playback_state_label.setText(f"Playback: {state}")
        self.playback_state_label.setStyleSheet(f"color: {PLAYBACK_STATUS_COLORS[state.lower()]}; background: transparent;")
        icon_file = ICON_FILES["pause"] if is_playing else ICON_FILES["play"]
        icon_path = os.path.join(ICON_DIR, icon_file)
        qt_icon = QStyle.SP_MediaPause if is_playing else QStyle.SP_MediaPlay
        if os.path.exists(icon_path):
            self.play_button.setIcon(QIcon(icon_path))
            self.play_button.setIconSize(QSize(*ICON_SIZE))
            logging.debug(f"SourceScreen: Updated play button with custom icon: {icon_path}")
        else:
            self.play_button.setIcon(self.widget.style().standardIcon(qt_icon))
            logging.warning(f"SourceScreen: Play/Pause custom icon not found: {icon_path}")
        self.play_button.setStyleSheet(f"""
            QPushButton {{
                background: {PLAY_BUTTON_COLOR};
                color: {TEXT_COLOR};
                border-radius: {BORDER_RADIUS}px;
                padding: {BUTTON_PADDING['play_stop']}px;
                icon-size: {ICON_SIZE[0]}px;
            }}
        """)
        self.playback_state_label.update()

    def on_play_clicked(self):
        from config import LOCAL_FILES_INPUT_NUM, HDMI_OUTPUTS, VIDEO_DIR
        logging.debug("SourceScreen: Play button clicked")
        if self.file_list.currentItem():
            # Update source_states for Local Files
            self.parent.interface.source_states[self.source_name] = True
            # Map outputs to HDMI ports
            selected_outputs = self.parent.input_output_map.get(LOCAL_FILES_INPUT_NUM, [])
            hdmi_map = {}
            for hdmi_idx, output_indices in HDMI_OUTPUTS.items():
                for output_idx in output_indices:
                    if output_idx in selected_outputs:
                        if hdmi_idx not in hdmi_map:
                            hdmi_map[hdmi_idx] = []
                        hdmi_map[hdmi_idx].append(output_idx)
            logging.debug(f"SourceScreen: Playback HDMI map: {hdmi_map}")
            file_path = os.path.join(self.source_paths[self.current_source], self.file_list.currentItem().text())
            # Pass file path and hdmi_map to toggle_play_pause
            self.parent.playback.toggle_play_pause(self.source_name, file_path, hdmi_map)
            self.update_playback_state()
        else:
            logging.warning("SourceScreen: Play button clicked but no file selected")

    def on_stop_clicked(self):
        logging.debug("SourceScreen: Stop button clicked")
        self.parent.interface.source_states[self.source_name] = False
        self.parent.playback.stop_input(2)
        self.update_playback_state()

    def toggle_output(self, tv_name, checked):
        from config import TV_OUTPUTS, LOCAL_FILES_INPUT_NUM, OUTPUT_BUTTON_COLORS, BORDER_RADIUS, BUTTON_PADDING
        output_idx = TV_OUTPUTS[tv_name]
        input_num = LOCAL_FILES_INPUT_NUM
        if checked:
            if input_num not in self.parent.input_output_map:
                self.parent.input_output_map[input_num] = []
            if output_idx not in self.parent.input_output_map[input_num]:
                self.parent.input_output_map[input_num].append(output_idx)
                logging.debug(f"SourceScreen: Assigned {tv_name} (idx {output_idx}) to input {input_num}")
        else:
            if input_num in self.parent.input_output_map and output_idx in self.parent.input_output_map[input_num]:
                self.parent.input_output_map[input_num].remove(output_idx)
                logging.debug(f"SourceScreen: Removed {tv_name} (idx {output_idx}) from input {input_num}")
                if not self.parent.input_output_map[input_num]:
                    del self.parent.input_output_map[input_num]
        is_current = input_num in self.parent.input_output_map and output_idx in self.parent.input_output_map.get(input_num, [])
        is_other = any(other_input != input_num and output_idx in self.parent.input_output_map.get(other_input, []) and self.parent.active_inputs.get(other_input, False) for other_input in self.parent.input_output_map)
        self.update_output_button_style(tv_name, is_current, is_other)
        logging.debug(f"SourceScreen: Toggled output {tv_name}: checked={checked}, map={self.parent.input_output_map}")

    def update_output_button_style(self, name, is_current, is_other):
        from config import OUTPUT_BUTTON_COLORS, BORDER_RADIUS, BUTTON_PADDING
        button = self.output_buttons[name]
        button.setText(name)  # Static text
        if is_current:
            color = OUTPUT_BUTTON_COLORS["selected"]
        elif is_other:
            color = OUTPUT_BUTTON_COLORS["other"]
        else:
            color = OUTPUT_BUTTON_COLORS["unselected"]
        button.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                color: white;
                border-radius: {BORDER_RADIUS}px;
                padding: {BUTTON_PADDING['schedule_output']}px;
            }}
        """)
        button.setChecked(is_current or is_other)

    def toggle_source(self, source_name, checked):
        from config import OUTPUT_BUTTON_COLORS, BORDER_RADIUS, BUTTON_PADDING
        if checked:
            self.current_source = source_name
            for name, button in self.source_buttons.items():
                button.setChecked(name == source_name)
                self.update_source_button_style(name, name == source_name)
            logging.debug(f"SourceScreen: Switched to source: {source_name}")
            self.update_file_list()
        else:
            # Prevent unchecking the current source
            self.source_buttons[self.current_source].setChecked(True)

    def update_source_button_style(self, name, is_selected):
        from config import OUTPUT_BUTTON_COLORS, BORDER_RADIUS, BUTTON_PADDING
        button = self.source_buttons[name]
        color = OUTPUT_BUTTON_COLORS["selected"] if is_selected else OUTPUT_BUTTON_COLORS["unselected"]
        text_color = "white" if button.isEnabled() else "#808080"  # Gray for disabled
        button.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                color: {text_color};
                border-radius: {BORDER_RADIUS}px;
                padding: {BUTTON_PADDING['schedule_output']}px;
            }}
        """)