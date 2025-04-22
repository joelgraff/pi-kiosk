import sys
import os
import subprocess
import hashlib
import json
import schedule
import time
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QComboBox, QLabel, QMessageBox, 
                             QDialog, QTextEdit, QDialogButtonBox, QTreeView, QFileSystemModel)
from PyQt5.QtCore import Qt, QDir

# Stubbed matrix API
def stub_matrix_route(input_num, outputs):
    print(f"Stub: Routing Input {input_num} to Outputs {outputs}")

# Schedule handling
SCHEDULE_FILE = "/home/pi/schedule.json"
def load_schedule():
    try:
        with open(SCHEDULE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_schedule(sched):
    with open(SCHEDULE_FILE, 'w') as f:
        json.dump(sched, f, indent=4)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

def execute_scheduled_task(input_num, outputs, path=None):
    stub_matrix_route(input_num, outputs)
    if input_num == 1:  # Web Stream or Device Stream
        subprocess.run(["pkill", "-f", "vlc.*http"])
        try:
            stream_url = subprocess.check_output(["yt-dlp", "-g", path]).decode().strip()
            subprocess.Popen(["vlc", "--fullscreen", "--no-video-title-show", stream_url])
            subprocess.run(["wlrctl", "window", "vlc", "move", "output:HDMI-A-1"])
        except subprocess.CalledProcessError:
            print(f"Error: Failed to stream {path}")
    elif input_num == 2 and path:  # MP4
        subprocess.run(["pkill", "-f", "vlc.*video.mp4"])
        subprocess.Popen(["vlc", "--fullscreen", "--no-video-title-show", path])
        subprocess.run(["wlrctl", "window", "vlc", "move", "output:HDMI-A-2"])

# Find MP4 file
def find_mp4():
    paths = ["/home/pi/videos", "/mnt/share", "/mnt/usb"]
    for path in paths:
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(('.mp4', '.mkv')):
                    return os.path.join(root, file)
    return None

# Schedule dialog
class ScheduleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Schedule")
        layout = QVBoxLayout()
        
        self.time_label = QLabel("Time (HH:MM, 24-hour):")
        self.time_input = QLineEdit("09:00")
        self.source_label = QLabel("Source:")
        self.source_combo = QComboBox()
        self.source_combo.addItems(["Web Stream", "MP4", "External HDMI", "Audio-Only"])
        self.path_label = QLabel("MP4 Path (if MP4):")
        self.path_input = QLineEdit("/home/pi/videos/video.mp4")
        self.tv_label = QLabel("TVs:")
        self.tv_combo = QComboBox()
        self.tv_combo.addItems(["TV 1", "TV 1+2", "TV 1+3", "TV 2", "TV 2+3", "TV 3", "All TVs"])
        self.schedule_text = QTextEdit()
        self.schedule_text.setReadOnly(True)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(self.time_label)
        layout.addWidget(self.time_input)
        layout.addWidget(self.source_label)
        layout.addWidget(self.source_combo)
        layout.addWidget(self.path_label)
        layout.addWidget(self.path_input)
        layout.addWidget(self.tv_label)
        layout.addWidget(self.tv_combo)
        layout.addWidget(QLabel("Current Schedule:"))
        layout.addWidget(self.schedule_text)
        layout.addWidget(button_box)
        self.setLayout(layout)
        
        self.update_schedule_text()

    def update_schedule_text(self):
        sched = load_schedule()
        text = ""
        for task in sched:
            path = task.get('path', '')
            text += f"{task['time']} - Input {task['input']} to Outputs {task['outputs']} {path}\n"
        self.schedule_text.setText(text)

    def get_schedule(self):
        input_map = {"Web Stream": 1, "MP4": 2, "External HDMI": 3, "Audio-Only": 4}
        tv_map = {
            "TV 1": [1], "TV 1+2": [1, 2], "TV 1+3": [1, 3],
            "TV 2": [2], "TV 2+3": [2, 3], "TV 3": [3], "All TVs": [1, 2, 3]
        }
        return {
            "time": self.time_input.text(),
            "input": input_map[self.source_combo.currentText()],
            "outputs": tv_map[self.tv_combo.currentText()],
            "path": self.path_input.text() if self.source_combo.currentText() == "MP4" else ""
        }

class KioskGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Media Kiosk")
        self.setGeometry(100, 100, 1280, 800)  # Simulate 10.1” touchscreen
        self.correct_pin = hashlib.sha256("1234".encode()).hexdigest()
        self.init_ui()
        self.authenticated = False
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        self.load_and_apply_schedule()

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # PIN entry
        self.pin_label = QLabel("Enter PIN:")
        self.pin_input = QLineEdit()
        self.pin_input.setEchoMode(QLineEdit.Password)
        self.auth_button = QPushButton("Authenticate")
        self.auth_button.clicked.connect(self.authenticate)

        # Source selection
        self.source_label = QLabel("Select Source:")
        self.source_combo = QComboBox()
        self.source_combo.addItems(["Web Stream", "MP4", "Device Stream", "External HDMI", "Audio-Only"])
        self.url_label = QLabel("Web/Device URL:")
        self.url_input = QLineEdit("https://www.youtube.com/watch?v=example")
        self.url_input.setVisible(False)
        self.source_combo.currentTextChanged.connect(self.toggle_url_input)

        # File browser for MP4
        self.file_label = QLabel("Select MP4 File:")
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath('/')
        self.file_model.setNameFilters(['*.mp4', '*.mkv'])
        self.file_model.setNameFilterDisables(False)
        self.file_view = QTreeView()
        self.file_view.setModel(self.file_model)
        self.file_view.setRootIndex(self.file_model.index('/home/pi/videos'))
        self.file_view.clicked.connect(self.select_file)
        self.file_view.setVisible(False)

        # TV selection
        self.tv_label = QLabel("Select TVs:")
        self.tv_combo = QComboBox()
        self.tv_combo.addItems(["TV 1", "TV 1+2", "TV 1+3", "TV 2", "TV 2+3", "TV 3", "All TVs"])

        # Buttons
        button_layout = QHBoxLayout()
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.apply_selection)
        self.stop_button = QPushButton("Stop Playback")
        self.stop_button.clicked.connect(self.stop_playback)
        self.schedule_button = QPushButton("Manage Schedule")
        self.schedule_button.clicked.connect(self.manage_schedule)
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.schedule_button)

        self.layout.addWidget(self.pin_label)
        self.layout.addWidget(self.pin_input)
        self.layout.addWidget(self.auth_button)
        self.hide_controls()
        self.button_layout = button_layout

    def toggle_url_input(self, source):
        self.url_label.setVisible(source in ["Web Stream", "Device Stream"])
        self.url_input.setVisible(source in ["Web Stream", "Device Stream"])
        self.file_label.setVisible(source == "MP4")
        self.file_view.setVisible(source == "MP4")

    def select_file(self, index):
        path = self.file_model.filePath(index)
        if path.endswith(('.mp4', '.mkv')):
            self.url_input.setText(path)

    def authenticate(self):
        pin = hashlib.sha256(self.pin_input.text().encode()).hexdigest()
        if pin == self.correct_pin:
            self.authenticated = True
            self.pin_label.hide()
            self.pin_input.hide()
            self.auth_button.hide()
            self.show_controls()
        else:
            QMessageBox.warning(self, "Error", "Incorrect PIN")

    def hide_controls(self):
        self.source_label.hide()
        self.source_combo.hide()
        self.url_label.hide()
        self.url_input.hide()
        self.file_label.hide()
        self.file_view.hide()
        self.tv_label.hide()
        self.tv_combo.hide()
        self.apply_button.hide()
        self.stop_button.hide()
        self.schedule_button.hide()

    def show_controls(self):
        self.layout.addWidget(self.source_label)
        self.layout.addWidget(self.source_combo)
        self.layout.addWidget(self.url_label)
        self.layout.addWidget(self.url_input)
        self.layout.addWidget(self.file_label)
        self.layout.addWidget(self.file_view)
        self.layout.addWidget(self.tv_label)
        self.layout.addWidget(self.tv_combo)
        self.layout.addLayout(self.button_layout)
        self.source_label.show()
        self.source_combo.show()
        self.tv_label.show()
        self.tv_combo.show()
        self.apply_button.show()
        self.stop_button.show()
        self.schedule_button.show()
        self.toggle_url_input(self.source_combo.currentText())

    def apply_selection(self):
        if not self.authenticated:
            return
        source = self.source_combo.currentText()
        tvs = self.tv_combo.currentText()
        path = self.url_input.text()

        input_map = {"Web Stream": 1, "MP4": 2, "Device Stream": 1, "External HDMI": 3, "Audio-Only": 4}
        tv_map = {
            "TV 1": [1], "TV 1+2": [1, 2], "TV 1+3": [1, 3],
            "TV 2": [2], "TV 2+3": [2, 3], "TV 3": [3], "All TVs": [1, 2, 3]
        }
        input_num = input_map[source]
        outputs = tv_map[tvs]

        if source in ["Web Stream", "Device Stream"]:
            subprocess.run(["pkill", "-f", "vlc.*http"])
            try:
                stream_url = subprocess.check_output(["yt-dlp", "-g", path]).decode().strip()
                subprocess.Popen(["vlc", "--fullscreen", "--no-video-title-show", stream_url])
                subprocess.run(["wlrctl", "window", "vlc", "move", "output:HDMI-A-1"])
            except subprocess.CalledProcessError:
                QMessageBox.warning(self, "Error", "Failed to stream URL")
                return
        elif source == "MP4" and path:
            subprocess.run(["pkill", "-f", "vlc.*video.mp4"])
            subprocess.Popen(["vlc", "--fullscreen", "--no-video-title-show", path])
            subprocess.run(["wlrctl", "window", "vlc", "move", "output:HDMI-A-2"])
        stub_matrix_route(input_num, outputs)

    def stop_playback(self):
        if not self.authenticated:
            return
        subprocess.run(["pkill", "-f", "vlc"])
        stub_matrix_route(0, [1, 2, 3])

    def manage_schedule(self):
        if not self.authenticated:
            return
        dialog = ScheduleDialog(self)
        if dialog.exec_():
            new_task = dialog.get_schedule()
            sched = load_schedule()
            sched.append(new_task)
            save_schedule(sched)
            schedule.every().day.at(new_task["time"]).do(
                execute_scheduled_task, input_num=new_task["input"], 
                outputs=new_task["outputs"], path=new_task["path"]
            )

    def load_and_apply_schedule(self):
        schedule.clear()
        for task in load_schedule():
            schedule.every().day.at(task["time"]).do(
                execute_scheduled_task, input_num=task["input"], 
                outputs=task["outputs"], path=task.get("path", "")
            )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = KioskGUI()
    window.show()  # Dialog for development
    sys.exit(app.exec_())