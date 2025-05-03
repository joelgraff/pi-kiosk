# source_screen_outputs.py: Output button styling and toggling for SourceScreen
#
# Overview:
# Defines functions to style and toggle TV output buttons (Fellowship 1, Fellowship 2, Nursery, Sanctuary).
#
# Recent Changes (as of May 2025):
# - Added Sanctuary output, organized in two layouts.

from PyQt5.QtWidgets import QPushButton
import logging

def update_output_button_style(self, name, is_current, is_other):
    button = self.output_buttons[name]
    button.setText(name)  # Static text
    if is_current:
        button.setStyleSheet("""
            QPushButton {
                background: #1f618d;
                color: white;
                border-radius: 8px;
                padding: 10px;
            }
        """)
    elif is_other:
        button.setStyleSheet("""
            QPushButton {
                background: #c0392b;
                color: white;
                border-radius: 8px;
                padding: 10px;
            }
        """)
    else:
        button.setStyleSheet("""
            QPushButton {
                background: #7f8c8d;
                color: white;
                border-radius: 8px;
                padding: 10px;
            }
        """)
    button.setChecked(is_current or is_other)

def toggle_output(self, tv_name, checked):
    output_map = {"Fellowship 1": 1, "Fellowship 2": 2, "Nursery": 3, "Sanctuary": 4}
    output_idx = output_map[tv_name]
    input_num = 2  # Local Files
    if checked:
        if input_num not in self.parent.input_output_map:
            self.parent.input_output_map[input_num] = []
        if output_idx not in self.parent.input_output_map[input_num]:
            self.parent.input_output_map[input_num].append(output_idx)
    else:
        if input_num in self.parent.input_output_map and output_idx in self.parent.input_output_map[input_num]:
            self.parent.input_output_map[input_num].remove(output_idx)
            if not self.parent.input_output_map[input_num]:
                del self.parent.input_output_map[input_num]
    is_current = input_num in self.parent.input_output_map and output_idx in self.parent.input_output_map.get(input_num, [])
    is_other = any(other_input != input_num and output_idx in self.parent.input_output_map.get(other_input, []) and self.parent.active_inputs.get(other_input, False) for other_input in self.parent.input_output_map)
    self.update_output_button_style(tv_name, is_current, is_other)
    logging.debug(f"SourceScreen: Toggled output {tv_name}: checked={checked}, map={self.parent.input_output_map}")