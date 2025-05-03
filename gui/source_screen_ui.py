# source_screen_ui.py: UI setup for SourceScreen
#
# Overview:
# Defines the setup_ui function for the Local Files screen.
# Sets up file list, TV output toggles, Play/Stop/Schedule buttons, Back button, and status labels.
#
# Recent Changes (as of June 2025):
# - Fixed 'setAlignment' error on Back button using QHBoxLayout.
# - Extracted hardcoded values to config.py.
# - Updated filepaths to use /home/admin/kiosk/ project root (except VIDEO_DIR).
# - Fixed QFont error by using QFont.Bold in TITLE_FONT.
# - Added file listing for videos directory.
# - Added Back button connection to show_controls.
# - Improved file listing with directory checks and case-insensitive extensions.
# - Disabled Play/Stop buttons until file selected.
# - Moved ScheduleDialog import inside open_schedule_dialog to avoid circular imports.
# - Moved event handlers to source_screen.py to fix AttributeError.
# - Added placeholder QMessageBox and enhanced logging for Schedule dialog.
# - Moved placeholder to except blocks and added window flags logging.
# - Added dialog.show(), raise_(), activateWindow(), and finished signal.
# - Added showEvent/closeEvent logging, focus tracking, test dialog, and centered geometry.
#
# Dependencies:
# - config.py: Filepaths, TV outputs, UI constants.

from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QListWidget, QLabel, QPushButton, QStyle, QMessageBox, QDialog, QVBoxLayout
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon
import logging
import os
from config import (
    VIDEO_DIR, ICON_DIR, ICON_FILES, TV_OUTPUTS, SOURCE_SCREEN_BACKGROUND,
    TITLE_FONT, WIDGET_FONT, BACK_BUTTON_FONT, TEXT_COLOR, FILE_LIST_BORDER_COLOR,
    SCHEDULE_BUTTON_COLOR, PLAY_BUTTON_COLOR, STOP_BUTTON_COLOR, SYNC_STATUS_COLOR,
    PLAYBACK_STATUS_COLORS, BACK_BUTTON_COLOR, FILE_LIST_HEIGHT, FILE_LIST_ITEM_HEIGHT,
    SCHEDULE_BUTTON_SIZE, OUTPUT_BUTTON_SIZE, PLAY_STOP_BUTTON_SIZE, BACK_BUTTON_SIZE,
    ICON_SIZE, MAIN_LAYOUT_SPACING, TOP_LAYOUT_SPACING, OUTPUTS_CONTAINER_SPACING,
    OUTPUT_LAYOUT_SPACING, BUTTONS_LAYOUT_SPACING, RIGHT_LAYOUT_SPACING,
    BUTTON_PADDING, FILE_LIST_PADDING, BORDER_RADIUS, LOCAL_FILES_INPUT_NUM
)

def setup_ui(self):
    logging.debug(f"SourceScreen: Setting up UI for {self.source_name}")
    main_layout = QVBoxLayout(self.widget)
    main_layout.setContentsMargins(MAIN_LAYOUT_SPACING, MAIN_LAYOUT_SPACING, MAIN_LAYOUT_SPACING, MAIN_LAYOUT_SPACING)
    main_layout.setSpacing(MAIN_LAYOUT_SPACING)
    
    # Top layout: File list and outputs/buttons (1/2 vs. 1/2)
    top_layout = QHBoxLayout()
    top_layout.setSpacing(TOP_LAYOUT_SPACING)
    
    # Left side: File list and Schedule button
    left_layout = QVBoxLayout()
    title = QLabel(self.source_name)
    title.setFont(QFont(*TITLE_FONT))
    title.setStyleSheet(f"color: {TEXT_COLOR}; background: transparent;")
    left_layout.addWidget(title)
    
    self.file_list = QListWidget()
    self.file_list.setFont(QFont(*WIDGET_FONT))
    self.file_list.setFixedHeight(FILE_LIST_HEIGHT)
    self.file_list.setStyleSheet(f"""
        QListWidget {{
            color: {TEXT_COLOR};
            background: {SOURCE_SCREEN_BACKGROUND};
            border: 2px solid {FILE_LIST_BORDER_COLOR};
            border-radius: {BORDER_RADIUS}px;
        }}
        QListWidget::item {{ height: {FILE_LIST_ITEM_HEIGHT}px; padding: {FILE_LIST_PADDING}px; }}
    """)
    # Populate file list
    if self.source_name == "Local Files":
        try:
            logging.debug(f"SourceScreen: Checking video directory: {VIDEO_DIR}")
            if not os.path.exists(VIDEO_DIR):
                logging.error(f"SourceScreen: Video directory does not exist: {VIDEO_DIR}")
                self.file_list.addItem("No video directory found")
            elif not os.access(VIDEO_DIR, os.R_OK):
                logging.error(f"SourceScreen: No read permission for video directory: {VIDEO_DIR}")
                self.file_list.addItem("No permission to access videos")
            else:
                video_extensions = ('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', 
                                  '.MP4', '.MKV', '.AVI', '.MOV', '.WMV', '.FLV')
                files = os.listdir(VIDEO_DIR)
                logging.debug(f"SourceScreen: Files in {VIDEO_DIR}: {files}")
                files_found = False
                for file_name in files:
                    if any(file_name.endswith(ext) for ext in video_extensions):
                        self.file_list.addItem(file_name)
                        logging.debug(f"SourceScreen: Added file to list: {file_name}")
                        files_found = True
                if not files_found:
                    logging.warning(f"SourceScreen: No video files found in {VIDEO_DIR}")
                    self.file_list.addItem("No video files found")
        except Exception as e:
            logging.error(f"SourceScreen: Failed to list files in {VIDEO_DIR}: {e}")
            self.file_list.addItem("Error loading files")
    self.file_list.itemClicked.connect(lambda item: file_selected(self, item))
    left_layout.addWidget(self.file_list)
    
    schedule_button = QPushButton("Schedule...")
    schedule_button.setFont(QFont(*WIDGET_FONT))
    schedule_button.setFixedSize(*SCHEDULE_BUTTON_SIZE)
    schedule_button.setStyleSheet(f"""
        QPushButton {{
            background: {SCHEDULE_BUTTON_COLOR};
            color: {TEXT_COLOR};
            border-radius: {BORDER_RADIUS}px;
            padding: {BUTTON_PADDING['schedule_output']}px;
        }}
    """)
    schedule_button.clicked.connect(lambda: open_schedule_dialog(self))
    left_layout.addWidget(schedule_button)
    left_layout.addStretch()
    
    top_layout.addLayout(left_layout, 1)
    
    # Right side: Back button, TV label, outputs, and buttons
    right_layout = QVBoxLayout()
    back_button = QPushButton("Back")
    back_button.setFont(QFont(*BACK_BUTTON_FONT))
    back_button.setFixedSize(*BACK_BUTTON_SIZE)
    back_button.setStyleSheet(f"""
        QPushButton {{
            background: {BACK_BUTTON_COLOR};
            color: {TEXT_COLOR};
            border-radius: {BORDER_RADIUS}px;
            padding: {BUTTON_PADDING['back']}px;
        }}
    """)
    back_button.clicked.connect(self.parent.show_controls)
    back_button_layout = QHBoxLayout()
    back_button_layout.addStretch()
    back_button_layout.addWidget(back_button)
    right_layout.addLayout(back_button_layout)
    
    outputs_label = QLabel("TV")
    outputs_label.setFont(QFont(*TITLE_FONT))
    outputs_label.setStyleSheet(f"color: {TEXT_COLOR}; background: transparent;")
    outputs_label.setAlignment(Qt.AlignCenter)
    right_layout.addWidget(outputs_label)
    
    # Outputs: Two columns (Fellowship 1/Nursery, Fellowship 2/Sanctuary)
    outputs_container = QHBoxLayout()
    outputs_container.setSpacing(OUTPUTS_CONTAINER_SPACING)
    
    outputs_left_layout = QVBoxLayout()
    outputs_left_layout.setSpacing(OUTPUT_LAYOUT_SPACING)
    outputs_right_layout = QVBoxLayout()
    outputs_right_layout.setSpacing(OUTPUT_LAYOUT_SPACING)
    
    self.output_buttons = {name: QPushButton(name) for name in TV_OUTPUTS}
    for name, button in self.output_buttons.items():
        button.setFont(QFont(*WIDGET_FONT))
        button.setFixedSize(*OUTPUT_BUTTON_SIZE)
        button.setCheckable(True)
        output_idx = TV_OUTPUTS[name]
        is_current = 2 in self.parent.input_output_map and output_idx in self.parent.input_output_map.get(2, [])
        is_other = any(other_input != 2 and output_idx in self.parent.input_output_map.get(other_input, []) and self.parent.active_inputs.get(other_input, False) for other_input in self.parent.input_output_map)
        self.update_output_button_style(name, is_current, is_other)
        button.clicked.connect(lambda checked, n=name: self.toggle_output(n, checked))
        if name in ["Fellowship 1", "Nursery"]:
            outputs_left_layout.addWidget(button)
        else:
            outputs_right_layout.addWidget(button)
    
    outputs_container.addLayout(outputs_left_layout)
    outputs_container.addLayout(outputs_right_layout)
    right_layout.addLayout(outputs_container)
    right_layout.addSpacing(RIGHT_LAYOUT_SPACING)
    
    # Play/Stop buttons (horizontal)
    buttons_layout = QHBoxLayout()
    buttons_layout.setSpacing(BUTTONS_LAYOUT_SPACING)
    self.play_button = None
    self.stop_button = None
    for action, icon, color, qt_icon in [
        ("Play", ICON_FILES["play"], PLAY_BUTTON_COLOR, QStyle.SP_MediaPlay),
        ("Stop", ICON_FILES["stop"], STOP_BUTTON_COLOR, QStyle.SP_MediaStop)
    ]:
        button = QPushButton()
        button.setFixedSize(*PLAY_STOP_BUTTON_SIZE)
        button.setFont(QFont(*WIDGET_FONT))
        icon_path = os.path.join(ICON_DIR, icon)
        if os.path.exists(icon_path):
            button.setIcon(QIcon(icon_path))
            button.setIconSize(QSize(*ICON_SIZE))
            logging.debug(f"SourceScreen: Loaded custom icon for {action}: {icon_path}")
        else:
            button.setIcon(self.widget.style().standardIcon(qt_icon))
            logging.warning(f"SourceScreen: Custom icon not found for {action}: {icon_path}")
        button.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                color: {TEXT_COLOR};
                border-radius: {BORDER_RADIUS}px;
                padding: {BUTTON_PADDING['play_stop']}px;
                icon-size: {ICON_SIZE[0]}px;
            }}
        """)
        button.setEnabled(False)  # Disable until file selected
        if action == "Play":
            self.play_button = button
            button.clicked.connect(self.on_play_clicked)
        elif action == "Stop":
            self.stop_button = button
            button.clicked.connect(self.on_stop_clicked)
        buttons_layout.addWidget(button)
    
    right_layout.addLayout(buttons_layout)
    right_layout.addStretch()
    top_layout.addLayout(right_layout, 1)
    
    main_layout.addLayout(top_layout)
    
    # Bottom layout: Status messages
    bottom_layout = QHBoxLayout()
    self.sync_status_label = QLabel("Sync: Idle")
    self.sync_status_label.setFont(QFont(*WIDGET_FONT))
    self.sync_status_label.setStyleSheet(f"color: {SYNC_STATUS_COLOR}; background: transparent;")
    bottom_layout.addWidget(self.sync_status_label)
    
    bottom_layout.addStretch()
    
    self.playback_state_label = QLabel("Playback: Stopped")
    self.playback_state_label.setFont(QFont(*WIDGET_FONT))
    self.playback_state_label.setStyleSheet(f"color: {PLAYBACK_STATUS_COLORS['stopped']};")
    bottom_layout.addWidget(self.playback_state_label)
    
    main_layout.addLayout(bottom_layout)
    
    self.widget.setStyleSheet(f"QWidget {{ background: {SOURCE_SCREEN_BACKGROUND}; }}")
    logging.debug("SourceScreen: UI setup completed")

def file_selected(self, item):
    logging.debug(f"SourceScreen: File selected: {item.text()}")
    if self.source_name == "Local Files":
        file_path = os.path.join(VIDEO_DIR, item.text())
        self.parent.input_paths[LOCAL_FILES_INPUT_NUM] = file_path
        logging.debug(f"SourceScreen: Selected file path: {file_path}")
        if self.play_button and self.stop_button:
            self.play_button.setEnabled(True)
            self.stop_button.setEnabled(True)
    else:
        # Disable Play/Stop for non-video items (e.g., placeholder messages)
        if self.play_button and self.stop_button:
            self.play_button.setEnabled(False)
            self.stop_button.setEnabled(False)

def open_schedule_dialog(self):
    logging.debug("SourceScreen: Schedule button clicked")
    # Test dialog to verify Qt rendering
    test_dialog = QDialog(self.widget)
    test_dialog.setWindowTitle("Test Dialog")
    test_dialog.setFixedSize(200, 100)
    layout = QVBoxLayout(test_dialog)
    label = QLabel("Testing Qt dialog rendering")
    label.setFont(QFont(*WIDGET_FONT))
    layout.addWidget(label)
    test_dialog.setModal(True)
    logging.debug("SourceScreen: Showing test dialog")
    test_dialog.show()
    test_dialog.raise_()
    test_dialog.activateWindow()
    test_result = test_dialog.exec_()
    logging.debug(f"SourceScreen: Test dialog closed with result: {test_result}")
    
    try:
        from schedule_dialog import ScheduleDialog
        logging.debug("SourceScreen: Successfully imported ScheduleDialog")
        
        # Extend ScheduleDialog to log events
        class DebugScheduleDialog(ScheduleDialog):
            def showEvent(self, event):
                logging.debug(f"ScheduleDialog: Show event triggered, visible={self.isVisible()}")
                super().showEvent(event)
            
            def closeEvent(self, event):
                logging.debug(f"ScheduleDialog: Close event triggered, result={self.result()}")
                super().closeEvent(event)
        
        dialog = DebugScheduleDialog(self.parent, LOCAL_FILES_INPUT_NUM)
        dialog.setModal(True)
        dialog.setFixedSize(300, 200)
        dialog.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        # Center dialog relative to parent
        parent_geo = self.parent.geometry()
        dialog.move(parent_geo.center() - dialog.rect().center())
        dialog.setVisible(True)
        logging.debug(f"SourceScreen: Schedule dialog initialized for Input {LOCAL_FILES_INPUT_NUM}, modal={dialog.isModal()}, visible={dialog.isVisible()}, flags={dialog.windowFlags()}, parent={dialog.parent()}, geometry={dialog.geometry()}, hasFocus={dialog.hasFocus()}")
        dialog.finished.connect(lambda result: logging.debug(f"SourceScreen: Schedule dialog finished with result: {result}"))
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        result = dialog.exec_()
        logging.debug(f"SourceScreen: Schedule dialog closed with result: {result}")
    except ImportError as e:
        logging.error(f"SourceScreen: Failed to import ScheduleDialog: {e}")
        self.sync_status_label.setText("Schedule unavailable")
        placeholder = QMessageBox(self.widget)
        placeholder.setWindowTitle("Schedule Error")
        placeholder.setText("Scheduling is unavailable: Module not found")
        placeholder.setStandardButtons(QMessageBox.Ok)
        placeholder.setFixedSize(300, 200)
        placeholder.exec_()
        logging.debug("SourceScreen: Placeholder dialog displayed for ImportError")
    except Exception as e:
        logging.error(f"SourceScreen: Failed to open ScheduleDialog: {e}")
        self.sync_status_label.setText("Schedule error")
        # Fallback QDialog
        fallback_dialog = QDialog(self.widget)
        fallback_dialog.setWindowTitle("Schedule Fallback")
        fallback_dialog.setFixedSize(300, 200)
        layout = QVBoxLayout(fallback_dialog)
        label = QLabel("Scheduling failed. Please check logs.")
        label.setFont(QFont(*WIDGET_FONT))
        layout.addWidget(label)
        fallback_dialog.setModal(True)
        fallback_dialog.exec_()
        logging.debug("SourceScreen: Fallback dialog displayed for Exception")