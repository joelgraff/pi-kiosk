# source_screen_ui.py: UI setup for SourceScreen
#
# Overview:
# Defines the setup_ui function for the Local Files screen.
# Sets up file list, USB/Internal toggles, TV output toggles, Play/Stop/Schedule buttons, Back button, and playback state label.
#
# Recent Changes (as of May 2025):
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
# - Added dialog.show(), raise_(), activateWindow(), and centered geometry.
# - Removed test dialog, DebugScheduleDialog, and excessive logging.
# - Removed "TV" label, changed "Local Files" to "Select File", moved Back button to bottom-left,
#   eliminated Sync notification, moved Play/Stop to top-right, moved Schedule below TV outputs.
# - Moved Schedule to bottom-right, positioned Playback between Schedule/Back, matched Back/Schedule heights,
#   reduced Play/Stop height, widened Play/Stop to match TV buttons, added USB/Internal toggles.
# - Moved update_file_list, toggle_source, update_source_button_style to source_screen.py to fix AttributeError.
# - Styled USB/Internal buttons to match TV buttons, increased Back button font, reduced file list height,
#   aligned file list top with TV buttons.
# - Changed Schedule button background to gray, moved file listbox to top of VBoxLayout,
#   moved Schedule to bottom-left and Back to bottom-right, set Back width to TV buttons.
# - Fixed TV output buttons disappearing due to layout typo, added gray text for disabled USB button.
# - Removed update_file_list call to fix AttributeError, updated ICON_DIR to /home/admin/kiosk/gui/icons.
# - Scaled Play/Stop icons to 24x24px.
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
    TITLE_FONT, WIDGET_FONT, TEXT_COLOR, FILE_LIST_BORDER_COLOR,
    SCHEDULE_BUTTON_COLOR, PLAY_BUTTON_COLOR, STOP_BUTTON_COLOR, PLAYBACK_STATUS_COLORS,
    BACK_BUTTON_COLOR, FILE_LIST_HEIGHT, FILE_LIST_ITEM_HEIGHT,
    SCHEDULE_BUTTON_SIZE, OUTPUT_BUTTON_SIZE, PLAY_STOP_BUTTON_SIZE,
    ICON_SIZE, MAIN_LAYOUT_SPACING, TOP_LAYOUT_SPACING, OUTPUTS_CONTAINER_SPACING,
    OUTPUT_LAYOUT_SPACING, BUTTONS_LAYOUT_SPACING, RIGHT_LAYOUT_SPACING,
    BUTTON_PADDING, FILE_LIST_PADDING, BORDER_RADIUS, LOCAL_FILES_INPUT_NUM,
    OUTPUT_BUTTON_COLORS
)

def setup_ui(self):
    logging.debug(f"SourceScreen: Setting up UI for {self.source_name}")
    main_layout = QVBoxLayout(self.widget)
    main_layout.setContentsMargins(MAIN_LAYOUT_SPACING, MAIN_LAYOUT_SPACING, MAIN_LAYOUT_SPACING, MAIN_LAYOUT_SPACING)
    main_layout.setSpacing(MAIN_LAYOUT_SPACING)
    
    # Top layout: File list and outputs/buttons (1/2 vs. 1/2)
    top_layout = QHBoxLayout()
    top_layout.setSpacing(TOP_LAYOUT_SPACING)
    
    # Left side: File list, USB/Internal toggles
    left_layout = QVBoxLayout()
    title = QLabel("Select File")
    title.setFont(QFont(*TITLE_FONT))
    title.setStyleSheet(f"color: {TEXT_COLOR}; background: transparent;")
    left_layout.addWidget(title)
    
    self.file_list = QListWidget()
    self.file_list.setFont(QFont(*WIDGET_FONT))
    self.file_list.setFixedHeight(FILE_LIST_HEIGHT - 50)  # Reduced to avoid overlap
    self.file_list.setStyleSheet(f"""
        QListWidget {{
            color: {TEXT_COLOR};
            background: {SOURCE_SCREEN_BACKGROUND};
            border: 2px solid {FILE_LIST_BORDER_COLOR};
            border-radius: {BORDER_RADIUS}px;
        }}
        QListWidget::item {{ height: {FILE_LIST_ITEM_HEIGHT}px; padding: {FILE_LIST_PADDING}px; }}
    """)
    self.file_list.itemClicked.connect(lambda item: file_selected(self, item))
    left_layout.addWidget(self.file_list)
    
    # USB/Internal toggles
    source_layout = QHBoxLayout()
    source_layout.setSpacing(BUTTONS_LAYOUT_SPACING)
    self.source_buttons = {"USB": QPushButton("USB"), "Internal": QPushButton("Internal")}
    for name, button in self.source_buttons.items():
        button.setFont(QFont(*WIDGET_FONT))
        button.setFixedSize(OUTPUT_BUTTON_SIZE[0], SCHEDULE_BUTTON_SIZE[1])
        button.setCheckable(True)
        button.setChecked(name == self.current_source)
        button.setEnabled(name != "USB" or self.usb_path is not None)
        self.update_source_button_style(name, name == self.current_source)
        button.clicked.connect(lambda checked, n=name: self.toggle_source(n, checked))
        source_layout.addWidget(button)
    left_layout.addLayout(source_layout)
    left_layout.addStretch()
    
    top_layout.addLayout(left_layout, 1)
    
    # Right side: Play/Stop buttons, TV outputs
    right_layout = QVBoxLayout()
    
    # Play/Stop buttons (horizontal)
    buttons_layout = QHBoxLayout()
    buttons_layout.setSpacing(BUTTONS_LAYOUT_SPACING)
    self.play_button = None
    self.stop_button = None
    new_play_stop_size = (OUTPUT_BUTTON_SIZE[0], SCHEDULE_BUTTON_SIZE[1])  # Match TV width, Schedule height
    for action, icon, color, qt_icon in [
        ("Play", ICON_FILES["play"], PLAY_BUTTON_COLOR, QStyle.SP_MediaPlay),
        ("Stop", ICON_FILES["stop"], STOP_BUTTON_COLOR, QStyle.SP_MediaStop)
    ]:
        button = QPushButton()
        button.setFixedSize(*new_play_stop_size)
        button.setFont(QFont(*WIDGET_FONT))
        icon_path = os.path.join("/home/admin/kiosk/gui/icons", icon)  # Updated ICON_DIR
        if os.path.exists(icon_path):
            button.setIcon(QIcon(icon_path))
            button.setIconSize(QSize(24, 24))  # Scale to 24x24px
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
    
    # TV Outputs: Two columns (Fellowship 1/Nursery, Fellowship 2/Sanctuary)
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
    right_layout.addStretch()
    
    top_layout.addLayout(right_layout, 1)
    
    main_layout.addLayout(top_layout)
    
    # Bottom layout: Schedule button (left), Playback state (center), Back button (right)
    bottom_layout = QHBoxLayout()
    schedule_button = QPushButton("Schedule...")
    schedule_button.setFont(QFont(*WIDGET_FONT))
    schedule_button.setFixedSize(*SCHEDULE_BUTTON_SIZE)
    schedule_button.setStyleSheet(f"""
        QPushButton {{
            background: {OUTPUT_BUTTON_COLORS['unselected']};
            color: white;
            border-radius: {BORDER_RADIUS}px;
            padding: {BUTTON_PADDING['schedule_output']}px;
        }}
    """)
    schedule_button.clicked.connect(lambda: open_schedule_dialog(self))
    bottom_layout.addWidget(schedule_button)
    
    self.playback_state_label = QLabel("Playback: Stopped")
    self.playback_state_label.setFont(QFont(*WIDGET_FONT))
    self.playback_state_label.setStyleSheet(f"color: {PLAYBACK_STATUS_COLORS['stopped']};")
    bottom_layout.addWidget(self.playback_state_label)
    
    back_button = QPushButton("Back")
    back_button.setFont(QFont(*WIDGET_FONT))
    back_button.setFixedSize(OUTPUT_BUTTON_SIZE[0], SCHEDULE_BUTTON_SIZE[1])  # Match TV width, Schedule height
    back_button.setStyleSheet(f"""
        QPushButton {{
            background: {BACK_BUTTON_COLOR};
            color: {TEXT_COLOR};
            border-radius: {BORDER_RADIUS}px;
            padding: {BUTTON_PADDING['back']}px;
        }}
    """)
    back_button.clicked.connect(self.parent.show_controls)
    bottom_layout.addWidget(back_button)
    
    main_layout.addLayout(bottom_layout)
    
    self.widget.setStyleSheet(f"QWidget {{ background: {SOURCE_SCREEN_BACKGROUND}; }}")
    logging.debug("SourceScreen: UI setup completed")

def file_selected(self, item):
    logging.debug(f"SourceScreen: File selected: {item.text()}")
    if self.source_name == "Local Files":
        file_path = os.path.join(self.source_paths[self.current_source], item.text())
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
    try:
        from schedule_dialog import ScheduleDialog
        logging.debug("SourceScreen: Successfully imported ScheduleDialog")
        dialog = ScheduleDialog(self.parent, LOCAL_FILES_INPUT_NUM)
        dialog.setModal(True)
        dialog.setFixedSize(300, 200)
        dialog.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        # Center dialog relative to parent
        parent_geo = self.parent.geometry()
        dialog.move(parent_geo.center() - dialog.rect().center())
        dialog.setVisible(True)
        logging.debug(f"SourceScreen: Schedule dialog initialized for Input {LOCAL_FILES_INPUT_NUM}")
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        result = dialog.exec_()
        logging.debug(f"SourceScreen: Schedule dialog closed with result: {result}")
    except ImportError as e:
        logging.error(f"SourceScreen: Failed to import ScheduleDialog: {e}")
        self.playback_state_label.setText("Schedule unavailable")
        placeholder = QMessageBox(self.widget)
        placeholder.setWindowTitle("Schedule Error")
        placeholder.setText("Scheduling is unavailable: Module not found")
        placeholder.setStandardButtons(QMessageBox.Ok)
        placeholder.setFixedSize(300, 200)
        placeholder.exec_()
        logging.debug("SourceScreen: Placeholder dialog displayed for ImportError")
    except Exception as e:
        logging.error(f"SourceScreen: Failed to open ScheduleDialog: {e}")
        self.playback_state_label.setText("Schedule error")
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