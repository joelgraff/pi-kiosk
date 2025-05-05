# output_dialog.py: Dialog for selecting TV outputs in the media kiosk
#
# Overview:
# This file defines the OutputDialog class, a PyQt5 QDialog for selecting TV outputs
# for a given input in the media kiosk application running on a Raspberry Pi 5 with X11.
# The dialog (245x184px, frameless) updates the KioskGUI.input_output_map and provides
# visual feedback on output assignment.
#
# Key Functionality:
# - Displays toggleable buttons for all TV outputs (from config.TV_OUTPUTS).
# - Styles buttons based on assignment: blue for current input, red for other active inputs,
#   gray for unassigned.
# - Updates input_output_map when outputs are toggled, ensuring no empty lists.
# - Includes a 'Done' button to confirm selections.
#
# Environment:
# - Raspberry Pi 5, X11 (QT_QPA_PLATFORM=xcb), PyQt5, 787x492px main window.
# - Logs: /home/admin/kiosk/logs/kiosk.log (app logs, including output selection).
# - Called by: SourceScreen.open_output_dialog (source_screen.py).
#
# Recent Changes (as of June 2025):
# - Updated to use config.TV_OUTPUTS for all outputs (Fellowship 1, Fellowship 2, Nursery, Sanctuary).
# - Fixed output indices to match config.py (1-based).
#
# Known Considerations:
# - Ensure output indices align with physical HDMI outputs (HDMI-A-1, HDMI-A-2).
# - Dialog size (245x184px) is small; verify touchscreen usability.
#
# Dependencies:
# - PyQt5: GUI framework.
# - config.py: TV_OUTPUTS, styling constants.

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import logging
from config import TV_OUTPUTS, OUTPUT_BUTTON_COLORS

class OutputDialog(QDialog):
    def __init__(self, parent, input_num, input_output_map, active_inputs):
        super().__init__(parent)
        self.input_num = input_num
        self.input_output_map = input_output_map
        self.active_inputs = active_inputs
        self.setWindowTitle("Select TV Outputs")
        self.setFixedSize(245, 184)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setup_ui()
        logging.debug(f"OutputDialog: Initialized for input {input_num}")

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.buttons = {name: QPushButton(name) for name in TV_OUTPUTS}
        for name, button in self.buttons.items():
            button.setFont(QFont("Arial", 16))
            button.setCheckable(True)
            button.setFixedHeight(40)
            output_idx = TV_OUTPUTS[name]
            is_current = self.input_num in self.input_output_map and output_idx in self.input_output_map.get(self.input_num, [])
            is_other = any(other_input != self.input_num and output_idx in self.input_output_map.get(other_input, []) and self.active_inputs.get(other_input, False) for other_input in self.input_output_map)
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
        logging.debug("OutputDialog: UI setup completed")

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
        output_idx = TV_OUTPUTS[tv_name]
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
        is_current = self.input_num in self.input_output_map and output_idx in self.input_output_map.get(self.input_num, [])
        is_other = any(other_input != self.input_num and output_idx in self.input_output_map.get(other_input, []) and self.active_inputs.get(other_input, False) for other_input in self.input_output_map)
        self.update_button_style(tv_name, is_current, is_other)
        logging.debug(f"OutputDialog: Updated output {tv_name}: checked={checked}, map={self.input_output_map}")