# source_screen.py: Main class for the source-specific screen (e.g., Local Files)
#
# Overview:
# Defines the SourceScreen class for the media kiosk on Raspberry Pi 5 with X11.
# Handles initialization, UI setup, and event handling.
#
# Environment:
# - Raspberry Pi 5, X11 (QT_QPA_PLATFORM=xcb), PyQt5, 787x492px window.
# - Logs: /home/admin/kiosk/logs/kiosk.log.
# - Icons: /home/admin/kiosk/gui/icons (128x128px).
# - Videos: /home/admin/videos (Internal), /media/admin/<drive> (USB).
#
# Dependencies:
# - PyQt5: GUI framework.
# - source_screen_ui.py: UI setup.
# - utilities.py.

from PyQt5.QtWidgets import QWidget, QListWidgetItem, QMenu, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal, QObject
import logging
import os
import sys

try:
    from source_screen_ui import setup_ui
    from output_dialog import OutputDialog
    logging.debug("SourceScreen: Successfully imported setup_ui and OutputDialog")
except ImportError as e:
    logging.error(f"SourceScreen: Failed to import: {e}")
    logging.error(f"SourceScreen: sys.path: {sys.path}")
    logging.error(f"SourceScreen: sys.modules: {list(sys.modules.keys())}")
    raise

class SyncWorker(QObject):
    finished = pyqtSignal(bool, str)  # Success, error message (if any)

    def __init__(self, share_path, local_path, parent):
        super().__init__()
        self.share_path = share_path
        self.local_path = local_path
        self.parent = parent

    def run(self):
        logging.debug("SyncWorker: Starting network share sync")
        if not os.path.exists(self.share_path):
            self.finished.emit(False, f"Network share not mounted: {self.share_path}")
            return
        if not os.access(self.share_path, os.R_OK):
            self.finished.emit(False, f"No read permission for network share: {self.share_path}")
            return
        share_files = set()
        try:
            share_files = set(os.listdir(self.share_path))
            logging.debug(f"SyncWorker: Network share files: {share_files}")
        except Exception as e:
            self.finished.emit(False, f"Failed to list network share files: {e}")
            return
        local_files = set()
        try:
            local_files = set(os.listdir(self.local_path))
            logging.debug(f"SyncWorker: Local video files: {local_files}")
        except Exception as e:
            self.finished.emit(False, f"Failed to list local video files: {e}")
            return
        if share_files and not share_files.issubset(local_files):
            logging.info(f"SyncWorker: Network share files not synced: {share_files - local_files}")
            try:
                logging.debug("SyncWorker: Initiating sync via sync_manager")
                self.parent.sync_manager.sync()
                logging.debug("SyncWorker: Completed network share sync")
                self.finished.emit(True, "")
            except Exception as e:
                logging.error(f"SyncWorker: Sync failed: {e}")
                self.finished.emit(False, f"Failed to trigger sync: {e}")
        else:
            logging.debug("SyncWorker: Network share appears synced")
            self.finished.emit(True, "")

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
        self.active_files = {}  # Track playing files: {filename: input_num}
        self.input_output_map = {}  # Track file-specific outputs: {input_num: [output_indices]}
        # Initialize USB/Internal state
        self.usb_path = None
        usb_base = "/media/admin/"
        if os.path.exists(usb_base) and os.listdir(usb_base):
            self.usb_path = os.path.join(usb_base, os.listdir(usb_base)[0])
        self.current_source = "Internal" if not self.usb_path else "USB"
        self.source_paths = {"Internal": "/home/admin/videos", "USB": self.usb_path}
        self.setup_ui()
        self.check_sync_status()  # Check sync status on init
        logging.debug(f"SourceScreen: Initialized for {self.source_name}")
        logging.debug(f"SourceScreen: QT_SCALE_FACTOR={os.environ.get('QT_SCALE_FACTOR', 'Not set')}")

    def setup_ui(self):
        try:
            setup_ui(self)
            self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
            self.file_list.customContextMenuRequested.connect(self.show_context_menu)
            self.update_file_list()  # Populate file list after UI setup
        except Exception as e:
            logging.error(f"SourceScreen: Failed to execute setup_ui: {e}")
            raise

    def show_context_menu(self, position):
        if not self.file_list.itemAt(position):
            return
        item = self.file_list.itemAt(position)
        filename = item.text()
        menu = QMenu()
        stop_action = QAction("Stop Playback", self.widget)
        stop_action.triggered.connect(lambda: self.stop_file(filename))
        menu.addAction(stop_action)
        menu.exec_(self.file_list.mapToGlobal(position))

    def check_sync_status(self):
        logging.debug("SourceScreen: Initiating network share sync check")
        self.file_list.clear()
        self.file_list.addItem("Syncing...")
        share_path = "/mnt/share"  # Assumed network share path
        local_path = "/home/admin/videos"
        self.sync_thread = QThread()
        self.sync_worker = SyncWorker(share_path, local_path, self.parent)
        self.sync_worker.moveToThread(self.sync_thread)
        self.sync_thread.started.connect(self.sync_worker.run)
        self.sync_worker.finished.connect(self.on_sync_finished)
        self.sync_worker.finished.connect(self.sync_thread.quit)
        self.sync_worker.finished.connect(self.sync_worker.deleteLater)
        self.sync_thread.finished.connect(self.sync_thread.deleteLater)
        self.sync_thread.start()

    def on_sync_finished(self, success, error_message):
        logging.debug(f"SourceScreen: Sync finished, success={success}, error={error_message}")
        if not success:
            self.file_list.clear()
            self.file_list.addItem("Sync failed")
            logging.error(f"SourceScreen: Sync error: {error_message}")
        self.update_file_list()

    def update_playback_state(self):
        from config import PLAYBACK_STATUS_COLORS, PLAY_BUTTON_COLOR, TEXT_COLOR, BORDER_RADIUS, BUTTON_PADDING
        logging.debug(f"SourceScreen: Updating playback state for {self.source_name}")
        is_playing = bool(self.active_files)  # Playing if any files are active
        state = "Playing" if is_playing else "Stopped"
        self.playback_state_label.setText(f"Playback: {state}")
        self.playback_state_label.setStyleSheet(f"color: {PLAYBACK_STATUS_COLORS[state.lower()]}; background: transparent;")
        self.playback_state_label.update()
        self.update_file_list()  # Refresh file list to show/hide play icons

    def on_play_clicked(self):
        from config import TV_OUTPUTS, VIDEO_DIR
        logging.debug("SourceScreen: Play button clicked")
        if not self.file_list.currentItem():
            logging.warning("SourceScreen: Play button clicked but no file selected")
            return
        selected_file = self.file_list.currentItem().text()
        if selected_file in self.active_files:
            logging.warning(f"SourceScreen: File already playing: {selected_file}")
            return
        # Show OutputDialog to select outputs
        dialog = OutputDialog(self.parent, self.source_name, TV_OUTPUTS)
        if dialog.exec_():
            selected_outputs = dialog.get_selected_outputs()
            if not selected_outputs:
                logging.warning("SourceScreen: No outputs selected for playback")
                return
            from config import get_next_input_num
            input_num = get_next_input_num()
            self.input_output_map[input_num] = selected_outputs
            self.active_files[selected_file] = input_num
            # Map outputs to HDMI ports
            from config import HDMI_OUTPUTS
            hdmi_map = {}
            for hdmi_idx, output_indices in HDMI_OUTPUTS.items():
                for output_idx in output_indices:
                    if output_idx in selected_outputs:
                        if hdmi_idx not in hdmi_map:
                            hdmi_map[hdmi_idx] = []
                        hdmi_map[hdmi_idx].append(output_idx)
            logging.debug(f"SourceScreen: Playback HDMI map for {selected_file}: {hdmi_map}")
            file_path = os.path.join(self.source_paths[self.current_source], selected_file)
            # Start playback for this file
            self.parent.playback.start_playback(self.source_name, file_path, hdmi_map, input_num)
            logging.debug(f"SourceScreen: Started playback for {selected_file} with input {input_num}")
            self.update_playback_state()

    def on_stop_clicked(self):
        logging.debug("SourceScreen: Stop button clicked")
        for filename, input_num in list(self.active_files.items()):
            self.stop_file(filename)
        self.update_playback_state()

    def stop_file(self, filename):
        if filename not in self.active_files:
            logging.warning(f"SourceScreen: Attempted to stop non-playing file: {filename}")
            return
        input_num = self.active_files[filename]
        self.parent.playback.stop_input(input_num)
        del self.active_files[filename]
        if input_num in self.input_output_map:
            del self.input_output_map[input_num]
        logging.debug(f"SourceScreen: Stopped playback for {filename} with input {input_num}")
        self.update_playback_state()

    def toggle_output(self, tv_name, checked):
        from config import TV_OUTPUTS, LOCAL_FILES_INPUT_NUM, OUTPUT_BUTTON_COLORS, BORDER_RADIUS, BUTTON_PADDING
        output_idx = TV_OUTPUTS[tv_name]
        input_num = LOCAL_FILES_INPUT_NUM  # Used for global source output display
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
        is_other = any(other_input != input_num and output_idx in self.input_output_map.get(other_input, []) for other_input in self.input_output_map)
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
            color = OUTPUT_BUTTON_COLORS["unassigned"]
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
            self.update_file_list()
            for name, button in self.source_buttons.items():
                button.setChecked(name == source_name)
                self.update_source_button_style(name, name == source_name)
            logging.debug(f"SourceScreen: Switched to source: {source_name}")
        else:
            self.source_buttons[self.current_source].setChecked(True)

    def update_source_button_style(self, name, is_selected):
        from config import OUTPUT_BUTTON_COLORS, BORDER_RADIUS, BUTTON_PADDING
        button = self.source_buttons[name]
        color = OUTPUT_BUTTON_COLORS["selected"] if is_selected else OUTPUT_BUTTON_COLORS["unselected"]
        text_color = "white" if button.isEnabled() else "#A0A0A0"
        button.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                color: {text_color};
                border-radius: {BORDER_RADIUS}px;
                padding: {BUTTON_PADDING['schedule_output']}px;
            }}
        """)

    def update_file_list(self):
        from config import ICON_FILES, FILE_LIST_ITEM_HEIGHT
        self.file_list.clear()
        source_path = self.source_paths[self.current_source]
        if not source_path or not os.path.exists(source_path):
            logging.error(f"SourceScreen: Source directory does not exist: {source_path}")
            self.file_list.addItem("No directory found")
            return
        if not os.access(source_path, os.R_OK):
            logging.error(f"SourceScreen: No read permission for directory: {source_path}")
            self.file_list.addItem("No permission to access directory")
            return
        try:
            video_extensions = ('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv',
                                '.MP4', '.MKV', '.AVI', '.MOV', '.WMV', '. moulv', '.FLV')
            files = sorted(os.listdir(source_path))
            logging.debug(f"SourceScreen: Files in {source_path}: {files}")
            files_found = False
            for file_name in files:
                if any(file_name.endswith(ext) for ext in video_extensions):
                    item = QListWidgetItem(file_name)
                    if file_name in self.active_files:
                        icon_path = os.path.join("/home/admin/kiosk/gui/icons", ICON_FILES["play"])
                        if os.path.exists(icon_path):
                            item.setIcon(QIcon(icon_path))
                            item.setSizeHint(QSize(0, FILE_LIST_ITEM_HEIGHT))
                            logging.debug(f"SourceScreen: Added play arrow icon for active file: {file_name}")
                        else:
                            logging.warning(f"SourceScreen: Play icon not found: {icon_path}")
                            item.setIcon(self.widget.style().standardIcon(QStyle.SP_MediaPlay))
                    self.file_list.addItem(item)
                    logging.debug(f"SourceScreen: Added file to list: {file_name}")
                    files_found = True
            if not files_found:
                logging.warning(f"SourceScreen: No video files found in {source_path}")
                self.file_list.addItem("No video files found")
        except Exception as e:
            logging.error(f"SourceScreen: Failed to list files in {source_path}: {e}")
            self.file_list.addItem("Error loading files")