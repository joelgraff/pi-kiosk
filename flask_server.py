from flask import Flask, request, render_template_string, redirect, url_for
from werkzeug.utils import secure_filename
import os
import subprocess

app = Flask(__name__)
UPLOAD_FOLDER = '/home/pi/uploads'
ALLOWED_EXTENSIONS = {'mp4', 'mkv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def check_auth(username, password):
    return username == 'admin' and password == 'password'

@app.route('/')
def index():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return 'Unauthorized', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'}
    return render_template_string('''
        <h1>Stream to Media Kiosk</h1>
        <form method="post" action="/upload" enctype="multipart/form-data">
            <p>Upload Video File (.mp4, .mkv):</p>
            <input type="file" name="file">
            <input type="submit" value="Upload">
        </form>
        <form method="post" action="/stream">
            <p>Stream URL (e.g., YouTube):</p>
            <input type="text" name="url">
            <input type="submit" value="Stream">
        </form>
    ''')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return 'Unauthorized', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'}
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        subprocess.run(["pkill", "-f", "vlc.*uploads"])
        try:
            subprocess.Popen(["vlc", "--fullscreen", "--no-video-title-show", file_path])
            subprocess.run(["wlrctl", "window", "vlc", "move", "output:HDMI-A-1"])
            return redirect(url_for('index'))
        except subprocess.CalledProcessError:
            return 'Failed to play uploaded file', 500
    return 'Invalid file type', 400

@app.route('/stream', methods=['POST'])
def stream_url():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return 'Unauthorized', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'}
    url = request.form.get('url')
    if url:
        subprocess.run(["pkill", "-f", "vlc.*http"])
        try:
            stream_url = subprocess.check_output(["yt-dlp", "-g", url]).decode().strip()
            subprocess.Popen(["vlc", "--fullscreen", "--no-video-title-show", stream_url])
            subprocess.run(["wlrctl", "window", "vlc", "move", "output:HDMI-A-1"])
            return redirect(url_for('index'))
        except subprocess.CalledProcessError:
            return 'Failed to stream URL', 500
    return 'No URL provided', 400

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=False)