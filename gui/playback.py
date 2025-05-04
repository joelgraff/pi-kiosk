# playback.py: Media playback management for the media kiosk
#
# Overview:
# Defines the Playback class for managing media playback on a Raspberry Pi 5 with X11,
# using mpv for video playback on specified HDMI outputs. Supports multiple simultaneous
# playbacks for different files on different outputs.
#
# Environment:
# - Raspberry Pi 5, X11 (QT_QPA_PLATFORM=xcb), PyQt5.
# - Logs: /home/admin/kiosk/logs/mpv.log (mpv output), /home/admin/kiosk/logs/kiosk.log (app logs).
# - Videos: /home/admin/videos.
#
# Dependencies:
# - mpv: Media player for playback.
# - subprocess: For running mpv processes.
# - utilities.py: For stub_matrix_route.
# - config.py: For input/output mappings.

import logging
import subprocess
import os
from utilities import stub_matrix_route
from config import MPV_LOG_FILE

class Playback:
    def __init__(self):
        self.processes = {}  # Track mpv processes: {input_num: subprocess.Popen}
        self.active_inputs = {}  # Track active inputs: {input_num: (source_name, file_path)}
        logging.debug("Playback: Initialized")

    def start_playback(self, source_name, file_path, hdmi_map, input_num):
        logging.debug(f"Playback: Starting playback for {source_name}, file: {file_path}, input: {input_num}")
        if input_num in self.processes:
            logging.warning(f"Playback: Input {input_num} already in use, stopping existing playback")
            self.stop_input(input_num)
        if not os.path.exists(file_path):
            logging.error(f"Playback: File not found: {file_path}")
            return
        mpv_args = ["mpv", "--no-osc", "--fs"]
        for hdmi_idx, output_indices in hdmi_map.items():
            mpv_args.extend([f"--fs-screen={hdmi_idx}"])
            if not stub_matrix_route(input_num, output_indices):
                logging.error(f"Playback: Failed to route input {input_num} to outputs {output_indices}")
                return
        mpv_args.append(file_path)
        log_file = open(MPV_LOG_FILE, "a")
        try:
            process = subprocess.Popen(
                mpv_args,
                stdout=log_file,
                stderr=log_file,
                stdin=subprocess.PIPE
            )
            self.processes[input_num] = process
            self.active_inputs[input_num] = (source_name, file_path)
            logging.debug(f"Playback: Started mpv process for input {input_num}, PID: {process.pid}")
        except Exception as e:
            logging.error(f"Playback: Failed to start playback for {file_path}: {e}")
            log_file.close()

    def stop_input(self, input_num):
        logging.debug(f"Playback: Stopping playback for input {input_num}")
        if input_num in self.processes:
            process = self.processes[input_num]
            process.terminate()
            try:
                process.wait(timeout=5)
                logging.debug(f"Playback: Process for input {input_num} terminated")
            except subprocess.TimeoutExpired:
                process.kill()
                logging.warning(f"Playback: Process for input {input_num} killed after timeout")
            del self.processes[input_num]
            del self.active_inputs[input_num]
        else:
            logging.warning(f"Playback: No process found for input {input_num}")

    def stop_all_playback(self):
        logging.debug("Playback: Stopping all playbacks")
        for input_num in list(self.processes.keys()):
            self.stop_input(input_num)

    def execute_scheduled_task(self, source_name, file_path, outputs, input_num):
        logging.debug(f"Playback: Executing scheduled task for {source_name}, file: {file_path}, input: {input_num}")
        from config import HDMI_OUTPUTS
        hdmi_map = {}
        for hdmi_idx, output_indices in HDMI_OUTPUTS.items():
            for output_idx in output_indices:
                if output_idx in outputs:
                    if hdmi_idx not in hdmi_map:
                        hdmi_map[hdmi_idx] = []
                    hdmi_map[hdmi_idx].append(output_idx)
        self.start_playback(source_name, file_path, hdmi_map, input_num)