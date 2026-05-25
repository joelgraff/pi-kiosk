from flask import Flask, request, render_template_string, redirect, url_for
from werkzeug.utils import secure_filename
import logging
import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GUI_DIR = os.path.join(BASE_DIR, "gui")
if GUI_DIR not in sys.path:
    sys.path.insert(0, GUI_DIR)

from config import (
    VIDEO_DIR,
    LOG_FILE,
    LOG_DIR,
    TV_OUTPUTS,
    HDMI_OUTPUTS,
    DEFAULT_OUTPUT_INDEX,
    ADMIN_USERNAME,
    PIN,
    ALLOWED_VIDEO_EXTENSIONS,
    FLASK_HOST,
    FLASK_PORT,
)

YT_DLP_TIMEOUT_SECONDS = 15

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = VIDEO_DIR

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)


def check_auth(username, password):
    return username == ADMIN_USERNAME and password == PIN


def auth_failed_response():
    return "Unauthorized", 401, {"WWW-Authenticate": 'Basic realm="Login Required"'}


def allowed_file(filename):
    return "." in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS


def selected_outputs_from_form():
    values = request.form.getlist("outputs")
    outputs = []
    for value in values:
        try:
            outputs.append(int(value))
        except ValueError:
            continue
    return outputs or [DEFAULT_OUTPUT_INDEX]


def build_hdmi_map(outputs):
    hdmi_map = {}
    for hdmi_idx, output_indices in HDMI_OUTPUTS.items():
        selected = [output_idx for output_idx in output_indices if output_idx in outputs]
        if selected:
            hdmi_map[hdmi_idx] = selected
    return hdmi_map


def stop_ingest_players():
    subprocess.run(["pkill", "-f", "mpv.*--title=pi-kiosk-ingest"], check=False)


def play_with_mpv(path, hdmi_map):
    stop_ingest_players()
    for hdmi_idx in hdmi_map:
        cmd = [
            "mpv",
            "--fs",
            "--vo=gpu",
            "--hwdec=no",
            f"--fs-screen={hdmi_idx}",
            "--title=pi-kiosk-ingest",
            path,
            f"--log-file={os.path.join(LOG_DIR, 'mpv_ingest.log')}",
        ]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


@app.route('/')
def index():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return auth_failed_response()

    output_options = "".join(
        f'<label><input type="checkbox" name="outputs" value="{idx}"> {name}</label><br>'
        for name, idx in TV_OUTPUTS.items()
    )

    return render_template_string(
        """
        <h1>Media Kiosk Wireless Ingest</h1>
        <p>Auth uses the kiosk admin PIN.</p>
        <form method="post" action="/upload" enctype="multipart/form-data">
            <p>Upload Video File:</p>
            <input type="file" name="file" required>
            <p>Outputs:</p>
            {{ output_options|safe }}
            <input type="submit" value="Upload & Play">
        </form>
        <hr>
        <form method="post" action="/stream">
            <p>Stream URL (YouTube and other yt-dlp sources):</p>
            <input type="text" name="url" required>
            <p>Outputs:</p>
            {{ output_options|safe }}
            <input type="submit" value="Stream">
        </form>
        """,
        output_options=output_options,
    )


@app.route('/upload', methods=['POST'])
def upload_file():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return auth_failed_response()

    if 'file' not in request.files:
        return 'No file part', 400

    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400

    if not allowed_file(file.filename):
        return 'Invalid file type', 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    outputs = selected_outputs_from_form()
    hdmi_map = build_hdmi_map(outputs)

    try:
        play_with_mpv(file_path, hdmi_map)
        logging.info(f"Started uploaded playback: file={file_path}, outputs={outputs}")
        return redirect(url_for('index'))
    except Exception as exc:
        logging.error(f"Failed to play uploaded file: {exc}")
        return 'Failed to play uploaded file', 500


@app.route('/stream', methods=['POST'])
def stream_url():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return auth_failed_response()

    url = request.form.get('url', '').strip()
    if not url:
        return 'No URL provided', 400

    outputs = selected_outputs_from_form()
    hdmi_map = build_hdmi_map(outputs)

    try:
        result = subprocess.run(
            ["yt-dlp", "-g", url],
            capture_output=True,
            text=True,
            check=True,
            timeout=YT_DLP_TIMEOUT_SECONDS,
        )
        stream_url = result.stdout.strip()
        play_with_mpv(stream_url, hdmi_map)
        logging.info(f"Started URL stream: url={url}, outputs={outputs}")
        return redirect(url_for('index'))
    except subprocess.CalledProcessError as exc:
        stderr_text = (exc.stderr or "").strip()
        logging.error(f"Failed to resolve stream URL: {url}, stderr={stderr_text}")
        return 'Failed to stream URL', 500
    except subprocess.TimeoutExpired:
        logging.error(f"Timed out resolving stream URL after {YT_DLP_TIMEOUT_SECONDS}s: {url}")
        return 'Stream resolution timed out', 504
    except Exception as exc:
        logging.error(f"Failed to stream URL: {exc}")
        return 'Failed to stream URL', 500


if __name__ == '__main__':
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False)
