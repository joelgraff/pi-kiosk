# source_screen_outputs.py: Output button styling and toggling for SourceScreen
#
# Overview:
# Defines functions to style and toggle TV output buttons.
#
# Recent Changes (as of June 2025):
# - Extracted hardcoded values to config.py.
#
# Dependencies:
# - config.py: TV outputs, colors, UI constants.

from PyQt5.QtWidgets import QPushButton
import logging
from config import TV_OUTPUTS, OUTPUT_BUTTON_COLORS, BORDER_RADIUS, BUTTON_PADDING, LOCAL_FILES_INPUT_NUM

def update_output_button_style(self, name, is_current, is_other):
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

def toggle_output(self, tv_name, checked):
    output_idx = TV_OUTPUTS[tv_name]
    input_num = LOCAL_FILES_INPUT_NUM
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