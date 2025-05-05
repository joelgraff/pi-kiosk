# output_dialog.py: Dialog for selecting TV outputs in the media kiosk
#
# Overview:
# This file defines the OutputDialog class, a PyQt5 QDialog for selecting TV outputs
# (Fellowship 1, Fellowship 2, Nursery) for a given input in the media kiosk application
# running on a Raspberry Pi 5 with X11. The dialog (245x184px, frameless) updates the
# KioskGUI.input_output_map and provides visual feedback on output assignment.
#
# Key Functionality:
# - Displays toggleable buttons for Fellowship 1 (output 1), Fellowship 2 (output 2), and
#   Nursery (output 3).
# - Styles buttons based on assignment: blue for current input, red for other active inputs,
#   gray for unassigned.
# - Updates input_output_map when outputs are toggled, ensuring no empty lists.
# - Includes a 'Done' button to confirm selections.
#
# Environment:
# - Raspberry Pi 5, X11 (QT_QPA_PLATFORM=xcb), PyQt5, 787x492px main window.
# - Logs: /home/admin/gui/logs/kiosk.log (app logs, including output selection).
# - Called by: SourceScreen.open_output_dialog (output_dialog.py or source_screen.py).
#
# Integration Notes:
# - Used by SourceScreen for Local Files (input 2) to configure HDMI outputs.
# - Maps outputs to indices (1: Fellowship 1, 2: Fellowship 2, 3: Nursery) for playback.py.
# - Default to Fellowship 1 if no outputs selected (implement in playback.py).
# - Includes an updated SourceScreen class supporting Web, Cast, and USB; may replace
#   source_screen.py.
#
# Recent Additions (as of April 2025):
# - Added to resolve missing output selection functionality.
# - Dynamic button styling for clear output status.
#
# Known Considerations:
# - Ensure output indices align with physical HDMI outputs (HDMI-A-1, HDMI-A-2).
# - Confirm if SourceScreen in this file replaces source_screen.py.
# - Dialog size (245x184px) is small; verify touchscreen usability.
#
# Dependencies:
# - PyQt5: GUI framework.
# - utilities.py: For list_files, load_schedule, save_schedule.
# - schedule_dialog.py: For scheduling integration.
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QListWidget, QCheckBox, QDialog, QGridLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from schedule_dialog import ScheduleDialog
from utilities import list_files, load_schedule, save_schedule, schedule
import os
import logging

class OutputDialog(QDialog):
    def __init__(self, parent, input_num, input_output_map, active_inputs):
        super().__init__(parent)
        self.input_num = input_num
        self.input_output_map = input_output_map
        self.active_inputs = active_inputs
        self.setWindowTitle("Select TV Outputs")
        self.setFixedSize(245, 184)
        self.setWindowFlags(Qt.FramelessWindowHint)  # Hide title bar controls
        layout = QVBoxLayout(self)
        
        self.buttons = {
            "Fellowship 1": QPushButton("Fellowship 1"),
            "Fellowship 2": QPushButton("Fellowship 2"),
            "Nursery": QPushButton("Nursery")
        }
        for name, button in self.buttons.items():
            button.setFont(QFont("Arial", 16))  # Increased from 10
            button.setCheckable(True)
            button.setFixedHeight(40)  # Double height
            output_idx = {"Fellowship 1": 1, "Fellowship 2": 2, "Nursery": 3}[name]
            is_current = input_num in input_output_map and output_idx in input_output_map.get(input_num, [])
            is_other = any(other_input != input_num and output_idx in input_output_map.get(other_input, []) and active_inputs.get(other_input, False) for other_input in input_output_map)
            self.update_button_style(name, is_current, is_other)
            button.clicked.connect(lambda checked, n=name: self.update_output(n, checked))
            layout.addWidget(button)
        
        layout.addStretch()
        
        done_button = QPushButton("Done")
        done_button.setFont(QFont("Arial", 16))
        done_button.clicked.connect(self.accept)
        done_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #27ae60, stop:1 #2ecc71);
                color: white;
                border-radius: 6px;
                padding: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6ab7f5, stop:1 #ffffff);
            }
        """)
        layout.addWidget(done_button)

    def update_button_style(self, name, is_current, is_other):
        button = self.buttons[name]
        if is_current:
            button.setText(f"{name} (This Input)")
            button.setStyleSheet("""
                QPushButton {
                    background: #1f618d;
                    color: white;
                    border-radius: 6px;
                    padding: 6px;
                }
                QPushButton:hover {
                    background: #6ab7f5;
                }
            """)
        elif is_other:
            button.setText(f"{name} (Other Input)")
            button.setStyleSheet("""
                QPushButton {
                    background: #c0392b;
                    color: white;
                    border-radius: 6px;
                    padding: 6px;
                }
                QPushButton:hover {
                    background: #e74c3c;
                }
            """)
        else:
            button.setText(name)
            button.setStyleSheet("""
                QPushButton {
                    background: #7f8c8d;
                    color: white;
                    border-radius: 6px;
                    padding: 6px;
                }
                QPushButton:hover {
                    background: #95a5a6;
                }
            """)
        button.setChecked(is_current or is_other)

    def update_output(self, tv_name, checked):
        output_map = {"Fellowship 1": 1, "Fellowship 2": 2, "Nursery": 3}
        output_idx = output_map[tv_name]
        if checked:
            if self.input_num not in self.input_output_map:
                self.input_output_map[self.input_num] = []
            if output_idx not in self.input_output_map[self.input_num]:
                self.input_output_map[self.input_num].append(output_idx)
        else:
            if self.input_num in self.input_output_map and output_idx in self.input_output_map[self.input_num]:
                self.input_output_map[self.input_num].remove(output_idx)
                if not self.input_output_map[self.input_num]:
                    del self.input_output_map[self.input_num]
        # Update button style dynamically
        is_current = self.input_num in self.input_output_map and output_idx in self.input_output_map.get(self.input_num, [])
        is_other = any(other_input != self.input_num and output_idx in self.input_output_map.get(other_input, []) and self.active_inputs.get(other_input, False) for other_input in self.input_output_map)
        self.update_button_style(tv_name, is_current, is_other)

class SourceScreen:
    def __init__(self, parent, source_name):
        self.parent = parent
        self.source_name = source_name
        self.widget = QWidget()
        self.widget.source_screen = self
        self.layout = QVBoxLayout(self.widget)
        self.input_map = {"Audio": 4, "DVD": 3, "Local Files": 2, "Web": 1, "Cast": 1}
        self.input_num = self.input_map[source_name]
        self.selected_storage = "Internal"
        self.setup_ui()

    def setup_ui(self):
        title = QLabel(f"{self.source_name} Configuration")
        title.setFont(QFont("Arial", 30, QFont.Bold))  # Doubled from 15
        title.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(title)

        content_layout = QHBoxLayout()
        content_layout.setStretch(0, 2)  # File list: 2/3
        content_layout.setStretch(1, 1)  # TV outputs: 1/3

        # Left: Input configuration
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        if self.source_name in ["Web", "Cast"]:
            self.url_label = QLabel("URL (e.g., YouTube):")
            self.url_label.setStyleSheet("color: #000000;")
            self.url_label.setFont(QFont("Arial", 20))  # Doubled from 10
            self.url_input = QLineEdit(self.parent.input_paths.get(self.input_num, "https://youtu.be/PWa9yz_U7Q8"))
            self.url_input.setStyleSheet("color: #000000;")
            self.url_input.setFont(QFont("Arial", 20))
            input_layout.addWidget(self.url_label)
            input_layout.addWidget(self.url_input)
        elif self.source_name == "Local Files":
            storage_button_layout = QHBoxLayout()
            self.usb_button = QPushButton("USB")
            self.internal_button = QPushButton("Internal")
            for btn in [self.usb_button, self.internal_button]:
                btn.setFont(QFont("Arial", 20))  # Doubled from 10
                btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #7f8c8d, stop:1 #95a5a6);
                        color: white;
                        border-radius: 6px;
                        padding: 6px;
                    }
                    QPushButton:checked {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1f618d, stop:1 #154360);
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6ab7f5, stop:1 #ffffff);
                    }
                """)
                btn.setCheckable(True)
            self.usb_button.clicked.connect(lambda: self.toggle_storage("USB"))
            self.internal_button.clicked.connect(lambda: self.toggle_storage("Internal"))
            self.internal_button.setChecked(True)
            storage_button_layout.addWidget(self.usb_button)
            storage_button_layout.addWidget(self.internal_button)
            input_layout.addLayout(storage_button_layout)
            
            self.file_list = QListWidget()
            self.file_list.setStyleSheet("color: #000000;")
            self.file_list.setFont(QFont("Arial", 20))  # Doubled from 10
            self.file_list.itemClicked.connect(self.select_file)
            input_layout.addWidget(self.file_list)
            self.update_file_list()
        input_layout.addStretch()
        content_layout.addWidget(input_widget)

        # Right: TV outputs
        tv_widget = QWidget()
        tv_layout = QVBoxLayout(tv_widget)
        tv_label = QLabel("TV Outputs")
        tv_label.setFont(QFont("Arial", 24, QFont.Bold))  # Doubled from 12
        tv_label.setAlignment(Qt.AlignCenter)
        tv_layout.addWidget(tv_label)

        if self.source_name == "Local Files":
            self.outputs_label = QLabel("None")
            self.outputs_label.setFont(QFont("Arial", 20, QFont.Bold))  # Doubled from 10
            self.outputs_label.setStyleSheet("color: #f1c40f;")  # Heavy yellow
            tv_layout.addWidget(self.outputs_label)
            
            tv_layout.addStretch()  # Push Select Outputs to bottom
            select_outputs_button = QPushButton("Select Outputs")
            select_outputs_button.setFont(QFont("Arial", 20))  # Doubled from 10
            select_outputs_button.clicked.connect(self.open_output_dialog)
            select_outputs_button.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #7f8c8d, stop:1 #95a5a6);
                    color: white;
                    border-radius: 6px;
                    padding: 6px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6ab7f5, stop:1 #ffffff);
                }
            """)
            tv_layout.addWidget(select_outputs_button)
            self.update_outputs_label()
        else:
            self.tv_checkboxes = {
                "Fellowship 1": QCheckBox("Fellowship 1"),
                "Fellowship 2": QCheckBox("Fellowship 2"),
                "Nursery": QCheckBox("Nursery")
            }
            for name, checkbox in self.tv_checkboxes.items():
                checkbox.setFont(QFont("Arial", 20))  # Doubled from 10
                checkbox.setStyleSheet("color: white;")
                checkbox.stateChanged.connect(lambda state, n=name: self.update_tv_outputs(n, state))
                tv_layout.addWidget(checkbox)
        content_layout.addWidget(tv_widget)

        self.layout.addLayout(content_layout)

        # Control buttons
        controls_widget = QWidget()
        control_layout = QVBoxLayout(controls_widget)
        
        if self.source_name == "Local Files":
            icon_path = "/home/admin/gui/icons/"
            control_button_layout = QHBoxLayout()
            self.play_pause_button = QPushButton()
            self.play_pause_button.setFixedSize(61, 61)
            play_icon_file = f"{icon_path}play.png"
            if os.path.exists(play_icon_file):
                self.play_pause_button.setIcon(QIcon(play_icon_file))
                self.play_pause_button.setIconSize(self.play_pause_button.size())
                logging.debug(f"Loaded icon for Play: {play_icon_file}")
            else:
                logging.warning(f"Icon file not found for Play: {play_icon_file}")
            self.play_pause_button.clicked.connect(self.toggle_play_pause)
            
            self.stop_button = QPushButton()
            self.stop_button.setFixedSize(61, 61)
            stop_icon_file = f"{icon_path}stop.png"
            if os.path.exists(stop_icon_file):
                self.stop_button.setIcon(QIcon(stop_icon_file))
                self.stop_button.setIconSize(self.stop_button.size())
                logging.debug(f"Loaded icon for Stop: {stop_icon_file}")
            else:
                logging.warning(f"Icon file not found for Stop: {stop_icon_file}")
            self.stop_button.clicked.connect(self.stop_source)
            
            self.schedule_button = QPushButton("Schedule")
            self.schedule_button.setFont(QFont("Arial", 20))  # Doubled from 10
            self.schedule_button.setFixedSize(61, 61)  # Aligned with Play/Stop
            self.schedule_button.clicked.connect(self.schedule_source)
            
            control_button_layout.addWidget(self.play_pause_button)
            control_button_layout.addWidget(self.stop_button)
            control_button_layout.addWidget(self.schedule_button)
            control_layout.addLayout(control_button_layout)
            
            bottom_layout = QHBoxLayout()
            self.back_button = QPushButton()
            self.back_button.setFixedSize(61, 31)
            back_icon_file = f"{icon_path}back.png"
            if os.path.exists(back_icon_file):
                self.back_button.setIcon(QIcon(back_icon_file))
                self.back_button.setIconSize(self.back_button.size())
                logging.debug(f"Loaded icon for Back: {back_icon_file}")
            else:
                logging.warning(f"Icon file not found for Back: {back_icon_file}")
            self.back_button.clicked.connect(self.return_to_main)
            
            self.sync_status_label = QLabel("Network Sync: Idle")
            self.sync_status_label.setFont(QFont("Arial", 20))  # Doubled from 10
            self.sync_status_label.setStyleSheet("color: white;")
            
            self.stop_all_button = QPushButton("Stop All Playback")
            self.stop_all_button.setFont(QFont("Arial", 20))  # Doubled from 12
            self.stop_all_button.setFixedSize(184, 31)
            stop_all_icon_file = f"{icon_path}stop_all.png"
            if os.path.exists(stop_all_icon_file):
                self.stop_all_button.setIcon(QIcon(stop_all_icon_file))
                self.stop_all_button.setIconSize(self.stop_all_button.size() * 0.5)
                logging.debug(f"Loaded icon for Stop All: {stop_all_icon_file}")
            else:
                logging.warning(f"Icon file not found for Stop All: {stop_all_icon_file}")
            self.stop_all_button.clicked.connect(self.parent.playback.stop_all_playback)
            self.stop_all_button.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #c0392b, stop:1 #e74c3c);
                    color: white;
                    border-radius: 6px;
                    padding: 6px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6ab7f5, stop:1 #ffffff);
                }
            """)
            
            bottom_layout.addWidget(self.back_button)
            bottom_layout.addWidget(self.sync_status_label)
            bottom_layout.addWidget(self.stop_all_button)
            bottom_layout.setAlignment(Qt.AlignBottom)
            control_layout.addLayout(bottom_layout)
            
            for btn in [self.play_pause_button, self.stop_button, self.schedule_button, self.back_button]:
                btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #7f8c8d, stop:1 #95a5a6);
                        color: white;
                        border-radius: 6px;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6ab7f5, stop:1 #ffffff);
                    }
                """)
        else:
            control_sub_layout = QHBoxLayout()
            self.play_pause_button = QPushButton("Play")
            self.play_pause_button.setFont(QFont("Arial", 20))  # Doubled from 10
            self.play_pause_button.clicked.connect(self.toggle_play_pause)
            self.stop_button = QPushButton("Stop")
            self.stop_button.setFont(QFont("Arial", 20))
            self.stop_button.clicked.connect(self.stop_source)
            self.schedule_button = QPushButton("Schedule")
            self.schedule_button.setFont(QFont("Arial", 20))
            self.schedule_button.clicked.connect(self.schedule_source)
            self.back_button = QPushButton("Back")
            self.back_button.setFont(QFont("Arial", 20))
            self.back_button.clicked.connect(self.return_to_main)
            self.stop_all_button = QPushButton("Stop All Playback")
            self.stop_all_button.setFont(QFont("Arial", 20))
            self.stop_all_button.clicked.connect(self.parent.playback.stop_all_playback)
            self.stop_all_button.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #c0392b, stop:1 #e74c3c);
                    color: white;
                    border-radius: 6px;
                    padding: 6px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6ab7f5, stop:1 #ffffff);
                }
            """)
            for btn in [self.play_pause_button, self.stop_button, self.schedule_button, self.back_button]:
                btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #7f8c8d, stop:1 #95a5a6);
                        color: white;
                        border-radius: 6px;
                        padding: 6px;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6ab7f5, stop:1 #ffffff);
                    }
                """)
            control_sub_layout.addWidget(self.play_pause_button)
            control_sub_layout.addWidget(self.stop_button)
            control_sub_layout.addWidget(self.schedule_button)
            control_sub_layout.addWidget(self.back_button)
            control_layout.addLayout(control_sub_layout)
            control_layout.addWidget(self.stop_all_button, alignment=Qt.AlignRight)

        self.layout.addWidget(controls_widget)
        self.update_ui_state()

    def toggle_storage(self, storage):
        if storage == self.selected_storage:
            return
        self.selected_storage = storage
        self.usb_button.setChecked(storage == "USB")
        self.internal_button.setChecked(storage == "Internal")
        self.update_file_list()

    def update_file_list(self):
        self.file_list.clear()
        root_path = {"USB": "/mnt/usb", "Internal": "/home/admin/videos"}[self.selected_storage]
        files = list_files(root_path)
        for file in files:
            self.file_list.addItem(file)

    def select_file(self, item):
        root_path = {"USB": "/mnt/usb", "Internal": "/home/admin/videos"}[self.selected_storage]
        self.parent.input_paths[self.input_num] = os.path.join(root_path, item.text())

    def open_output_dialog(self):
        dialog = OutputDialog(self.parent, self.input_num, self.parent.input_output_map, self.parent.active_inputs)
        if dialog.exec_():
            self.update_outputs_label()

    def update_outputs_label(self):
        output_map = {1: "Fellowship 1", 2: "Fellowship 2", 3: "Nursery"}
        outputs = self.parent.input_output_map.get(self.input_num, [])
        if outputs:
            output_names = [output_map[idx] for idx in sorted(outputs)]
            self.outputs_label.setText(", ".join(output_names))
        else:
            self.outputs_label.setText("None")

    def update_tv_outputs(self, tv_name, state):
        output_map = {"Fellowship 1": 1, "Fellowship 2": 2, "Nursery": 3}
        output_idx = output_map[tv_name]
        if state == Qt.Checked:
            if self.input_num not in self.parent.input_output_map:
                self.parent.input_output_map[self.input_num] = []
            if output_idx not in self.parent.input_output_map[self.input_num]:
                self.parent.input_output_map[self.input_num].append(output_idx)
        else:
            if self.input_num in self.parent.input_output_map and output_idx in self.parent.input_output_map[self.input_num]:
                self.parent.input_output_map[self.input_num].remove(output_idx)
                if not self.parent.input_output_map[self.input_num]:
                    del self.parent.input_output_map[self.input_num]

    def toggle_play_pause(self):
        if self.source_name in ["Web", "Cast"]:
            self.parent.input_paths[self.input_num] = self.url_input.text()
        self.parent.playback.toggle_play_pause(self.source_name)
        self.update_ui_state()

    def stop_source(self):
        self.parent.playback.stop_input(self.input_num)
        self.update_ui_state()

    def schedule_source(self):
        path = self.parent.input_paths.get(self.input_num, "")
        if self.source_name in ["Web", "Cast"]:
            path = self.url_input.text()
        dialog = ScheduleDialog(self.input_num, path, self.parent)
        if dialog.exec_():
            new_task = dialog.get_schedule()
            sched = load_schedule()
            sched.append(new_task)
            save_schedule(sched)
            schedule.every().day.at(new_task["time"]).do(
                self.parent.playback.execute_scheduled_task,
                input_num=new_task["input"],
                outputs=new_task["outputs"],
                path=new_task["path"]
            )

    def return_to_main(self):
        self.parent.show_controls()

    def update_ui_state(self):
        is_playing = self.parent.interface.source_states.get(self.source_name, False)
        if self.source_name == "Local Files":
            icon_path = "/home/admin/gui/icons/"
            icon_file = f"{icon_path}{'pause' if is_playing else 'play'}.png"
            if os.path.exists(icon_file):
                self.play_pause_button.setIcon(QIcon(icon_file))
                self.play_pause_button.setIconSize(self.play_pause_button.size())
                logging.debug(f"Loaded icon for Play/Pause: {icon_file}")
            else:
                logging.warning(f"Icon file not found for Play/Pause: {icon_file}")
        else:
            self.play_pause_button.setText("Pause" if is_playing else "Play")

    def update_sync_status(self, status):
        if self.source_name == "Local Files":
            logging.debug(f"Local Files sync status updated: {status}")
            self.sync_status_label.setText(f"Network Sync: {status}")
            self.sync_status_label.update()