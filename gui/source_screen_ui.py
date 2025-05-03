# source_screen_ui.py: UI setup for SourceScreen
#
# Overview:
# Defines the setup_ui function to create the Local Files screen layout.
# Includes file list, TV output toggles, Play/Stop/Schedule buttons, Back button, and status labels.
#
# Recent Changes (as of June 2025):
# - Fixed 'setAlignment' error on Back button using QHBoxLayout.
# - Schedule button: Moved to left layout, text "Schedule...", 180x60px, no icon.
# - TV outputs: Two layouts (Fellowship 1/Nursery, Fellowship 2/Sanctuary), 180x60px.
# - Back button: Upper right, 80x40px, right-aligned via layout.
# - TV label: "TV", 28pt, white, centered.
# - File list: 260px, added 20px spacing to right layout.

from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QListWidget, QLabel, QPushButton, QStyle
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon
import logging
import os

def setup_ui(self):
    logging.debug(f"SourceScreen: Setting up UI for {self.source_name}")
    main_layout = QVBoxLayout(self.widget)
    main_layout.setContentsMargins(20, 20, 20, 20)
    main_layout.setSpacing(20)
    
    # Top layout: File list and outputs/buttons (1/2 vs. 1/2)
    top_layout = QHBoxLayout()
    top_layout.setSpacing(20)
    
    # Left side: File list and Schedule button
    left_layout = QVBoxLayout()
    title = QLabel(self.source_name)
    title.setFont(QFont("Arial", 28, QFont.Bold))
    title.setStyleSheet("color: #ffffff; background: transparent;")
    left_layout.addWidget(title)
    
    self.file_list = QListWidget()
    self.file_list.setFont(QFont("Arial", 20))
    self.file_list.setFixedHeight(260)
    self.file_list.setStyleSheet("""
        QListWidget {
            color: #ffffff;
            background: #2a3b5e;
            border: 2px solid #ffffff;
            border-radius: 8px;
        }
        QListWidget::item { height: 60px; padding: 5px; }
    """)
    self.file_list.itemClicked.connect(self.file_selected)
    left_layout.addWidget(self.file_list)
    
    schedule_button = QPushButton("Schedule...")
    schedule_button.setFont(QFont("Arial", 20))
    schedule_button.setFixedSize(180, 60)
    schedule_button.setStyleSheet("""
        QPushButton {
            background: #4caf50;
            color: #ffffff;
            border-radius: 8px;
            padding: 10px;
        }
    """)
    schedule_button.clicked.connect(self.open_schedule_dialog)
    left_layout.addWidget(schedule_button)
    left_layout.addStretch()
    
    top_layout.addLayout(left_layout, 1)
    
    # Right side: Back button, TV label, outputs, and buttons
    right_layout = QVBoxLayout()
    back_button = QPushButton("Back")
    back_button.setFont(QFont("Arial", 16))
    back_button.setFixedSize(80, 40)
    back_button.setStyleSheet("""
        QPushButton {
            background: #7f8c8d;
            color: #ffffff;
            border-radius: 8px;
            padding: 5px;
        }
    """)
    back_button_layout = QHBoxLayout()
    back_button_layout.addStretch()
    back_button_layout.addWidget(back_button)
    right_layout.addLayout(back_button_layout)
    
    outputs_label = QLabel("TV")
    outputs_label.setFont(QFont("Arial", 28, QFont.Bold))
    outputs_label.setStyleSheet("color: #ffffff; background: transparent;")
    outputs_label.setAlignment(Qt.AlignCenter)
    right_layout.addWidget(outputs_label)
    
    # Outputs: Two columns (Fellowship 1/Nursery, Fellowship 2/Sanctuary)
    outputs_container = QHBoxLayout()
    outputs_container.setSpacing(10)
    
    outputs_left_layout = QVBoxLayout()
    outputs_left_layout.setSpacing(5)
    outputs_right_layout = QVBoxLayout()
    outputs_right_layout.setSpacing(5)
    
    self.output_buttons = {
        "Fellowship 1": QPushButton("Fellowship 1"),
        "Nursery": QPushButton("Nursery"),
        "Fellowship 2": QPushButton("Fellowship 2"),
        "Sanctuary": QPushButton("Sanctuary")
    }
    for name, button in self.output_buttons.items():
        button.setFont(QFont("Arial", 20))
        button.setFixedSize(180, 60)
        button.setCheckable(True)
        output_idx = {"Fellowship 1": 1, "Fellowship 2": 2, "Nursery": 3, "Sanctuary": 4}[name]
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
    right_layout.addSpacing(20)
    
    # Play/Stop buttons (horizontal)
    buttons_layout = QHBoxLayout()
    buttons_layout.setSpacing(15)
    for action, icon, color, qt_icon in [
        ("Play", "play.png", "#4caf50", QStyle.SP_MediaPlay),
        ("Stop", "stop.png", "#e53935", QStyle.SP_MediaStop)
    ]:
        button = QPushButton()
        button.setFixedSize(120, 120)
        button.setFont(QFont("Arial", 20))
        icon_path = f"/home/admin/kiosk/gui/icons/{icon}"
        if os.path.exists(icon_path):
            button.setIcon(QIcon(icon_path))
            button.setIconSize(QSize(112, 112))
            logging.debug(f"SourceScreen: Loaded custom icon for {action}: {icon_path}, size: 112x112px")
        else:
            button.setIcon(self.widget.style().standardIcon(qt_icon))
            logging.warning(f"SourceScreen: Custom icon not found for {action}: {icon_path}, using Qt icon")
        button.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                color: #ffffff;
                border-radius: 8px;
                padding: 2px;
                icon-size: 112px;
            }}
        """)
        if action == "Play":
            self.play_button = button
            button.clicked.connect(lambda: self.parent.playback.toggle_play_pause(self.source_name))
        elif action == "Stop":
            button.clicked.connect(lambda: self.parent.playback.stop_input(2))
        buttons_layout.addWidget(button)
    
    right_layout.addLayout(buttons_layout)
    right_layout.addStretch()
    top_layout.addLayout(right_layout, 1)
    
    main_layout.addLayout(top_layout)
    
    # Bottom layout: Status messages
    bottom_layout = QHBoxLayout()
    self.sync_status_label = QLabel("Sync: Idle")
    self.sync_status_label.setFont(QFont("Arial", 20, QFont.Bold))
    self.sync_status_label.setStyleSheet("color: #ffc107; background: transparent;")
    bottom_layout.addWidget(self.sync_status_label)
    
    bottom_layout.addStretch()
    
    self.playback_state_label = QLabel("Playback: Stopped")
    self.playback_state_label.setFont(QFont("Arial", 20, QFont.Bold))
    self.playback_state_label.setStyleSheet("color: #e53935;")
    bottom_layout.addWidget(self.playback_state_label)
    
    main_layout.addLayout(bottom_layout)
    
    self.widget.setStyleSheet("QWidget { background: #2a3b5e; }")
    logging.debug("SourceScreen: UI setup completed")