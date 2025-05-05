# playback.py: Handles media playback for the media kiosk using mpv
#
# Overview:
# This file defines the Playback class, responsible for starting, stopping, and scheduling
# media playback in the media kiosk application running on a Raspberry Pi 5 with X11.
# It uses mpv to play videos from /home/admin/videos on selected HDMI outputs (e.g., HDMI-A-1,
# HDMI-A-2) based on user selections in the Local Files screen (via source_screen.py).
#
# Key Functionality:
# - toggle_play_pause: Starts or stops playback for a source with specified HDMI outputs.
# - start_playback: Launches mpv with specified video path and HDMI screens, logs to mpv.log.
# - stop_input/stop_all_playback: Terminates mpv processes.
# - execute_scheduled_task: Runs scheduled playback tasks (from schedule.json).
# - Uses stub_matrix_route (utilities.py) to simulate routing inputs to outputs.
#
# Environment:
# - Raspberry Pi 5, X11 (QT_QPA_PLATFORM=xcb), PyQt5, 787x492px window.
# - Logs: /home/admin/kiosk/logs/kiosk.log (app), /home/admin/kiosk/logs/mpv.log (mpv output).
# - Videos: /home/admin/videos (local storage).
# - Outputs: HDMI-A-1, HDMI-A-2 (targeted via --fs-screen={0,1}).
#
# Recent Fixes (as of May 2025):
# - Fixed invalid --no-video-title-show (VLC-specific) causing mpv crashes.
# - Replaced --o/--oerr with --log-file for correct mpv logging.
# - Added os.path.exists to validate video paths.
# - Enhanced subprocess error capture to log immediate mpv failures.
# - Added logging for mpv command, PID, and playback status.
# - Integrated stub_matrix_route for output routing simulation.
# - Added multi-screen support using --fs-screen=n based on hdmi_map.
#
# Known Considerations:
# - Ensure /home/admin/videos files are valid (.mp4, .mkv) and accessible.
# - MPV must be installed (sudo apt install mpv) and in PATH.
# - Monitor mpv.log for playback issues (e.g., codec errors, display issues).
# - input_paths and input_output_map must be set by source_screen.py.
#
# Dependencies:
# - mpv: External binary for media playback.
# - subprocess: Runs mpv processes.
# - utilities.py: Provides stub_matrix_route for output routing.

import os
import subprocess
import logging
from utilities import stub_matrix_route

class Playback:
    def __init__(self, parent):
        # Initialize Playback with KioskGUI parent for state access
        self.parent = parent
        logging.debug("Initializing Playback")
        self.media_processes = {}  # Store (input_num, hdmi_idx): process

    def toggle_play_pause(self, source_name, file_path, hdmi_map):
        # Starts or stops playback for a source on specified HDMI outputs
        try:
            logging.debug(f"Attempting toggle play/pause for source: {source_name}, path: {file_path}, hdmi_map: {hdmi_map}")
            input_num = self.parent.input_map.get(source_name, 2)  # Default to 2 for Local Files
            outputs = self.parent.input_output_map.get(input_num, [])
            
            if not os.path.exists(file_path):
                logging.error(f"Video file does not exist: {file_path}")
                return
            
            if not outputs or not hdmi_map:
                logging.warning(f"No outputs or HDMI map specified for input {input_num}")
                return
            
            if self.parent.active_inputs.get(input_num, False):
                self.stop_input(input_num)
            else:
                # Route input to outputs
                if stub_matrix_route(input_num, outputs):
                    self.start_playback(input_num, file_path, outputs, hdmi_map)
                else:
                    logging.error(f"Failed to route input {input_num} to outputs {outputs}")
        except Exception as e:
            logging.error(f"Toggle play/pause failed for {source_name}: {e}")
            raise

    def start_playback(self, input_num, path, outputs, hdmi_map):
        # Starts mpv playback for a video on specified HDMI outputs
        try:
            logging.debug(f"Starting playback for input {input_num}, path {path}, outputs {outputs}, hdmi_map {hdmi_map}")
            for hdmi_idx in hdmi_map:
                cmd = [
                    "mpv",
                    "--fs",
                    "--vo=gpu",
                    "--hwdec=no",
                    f"--fs-screen={hdmi_idx}",
                    path,
                    "--log-file=/home/admin/kiosk/logs/mpv.log"
                ]
                logging.debug(f"Executing MPV command: {' '.join(cmd)}")
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                # Check if process started
                if process.poll() is not None:
                    stdout, stderr = process.communicate()
                    logging.error(f"MPV failed immediately on HDMI {hdmi_idx}: stdout={stdout}, stderr={stderr}")
                    raise RuntimeError(f"MPV process exited: {stderr}")
                self.media_processes[(input_num, hdmi_idx)] = process
                logging.debug(f"Started playback for input {input_num} on HDMI {hdmi_idx}, PID: {process.pid}")
            self.parent.active_inputs[input_num] = True
            self.parent.interface.source_states[self.parent.selected_source] = True
        except Exception as e:
            logging.error(f"Start playback failed for input {input_num}: {e}")
            raise

    def stop_input(self, input_num):
        # Stops playback for a specific input
        try:
            logging.debug(f"Stopping playback for input {input_num}")
            for key, process in list(self.media_processes.items()):
                if key[0] == input_num:
                    try:
                        process.terminate()
                        process.wait(timeout=5)
                        logging.debug(f"Stopped playback for input {input_num} on HDMI {key[1]}")
                        del self.media_processes[key]
                    except Exception as e:
                        logging.error(f"Failed to stop playback for input {input_num} on HDMI {key[1]}: {e}")
            self.parent.active_inputs[input_num] = False
            self.parent.interface.source_states[self.parent.selected_source] = False
            logging.debug(f"Stopped playback for input {input_num}")
        except Exception as e:
            logging.error(f"Stop playback failed for input {input_num}: {e}")
            raise

    def stop_all_playback(self):
        # Stops all active playback processes
        try:
            logging.debug("Stopping all playback")
            for input_num in set(key[0] for key in self.media_processes.keys()):
                self.stop_input(input_num)
            logging.debug("Stopped all playback")
        except Exception as e:
            logging.error(f"Stop all playback failed: {e}")
            raise

    def execute_scheduled_task(self, input_num, outputs, path):
        # Executes a scheduled playback task
        try:
            logging.debug(f"Executing scheduled task for input {input_num}, outputs {outputs}")
            if not os.path.exists(path):
                logging.error(f"Scheduled video file does not exist: {path}")
                return
            if stub_matrix_route(input_num, outputs):
                # For scheduled tasks, assume single HDMI output (adjust if needed)
                self.start_playback(input_num, path, outputs, {0: outputs})
                logging.debug(f"Scheduled playback executed for input {input_num} on outputs {outputs}")
            else:
                logging.error(f"Scheduled routing failed for input {input_num} to outputs {outputs}")
        except Exception as e:
            logging.error(f"Scheduled task failed for input {input_num}: {e}")
            raise