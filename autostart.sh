#!/bin/bash
set -euo pipefail

PROJECT_ROOT="/home/admin/kiosk"
LOG_DIR="$PROJECT_ROOT/logs"
VIDEO_DIR="/home/admin/videos"
FLASK_APP="$PROJECT_ROOT/flask_server.py"
KIOSK_APP="$PROJECT_ROOT/gui/kiosk.py"
CLEANUP_APP="$PROJECT_ROOT/gui/cleanup_videos.py"

# Trap termination signals to clean up processes
cleanup() {
    echo "Cleaning up processes..."
    pkill -f "mpv" || true
    pkill -f "python3 $FLASK_APP" || true
    pkill -f "python3 $KIOSK_APP" || true
    pkill -f "python3 $CLEANUP_APP" || true
    exit 0
}
trap cleanup SIGINT SIGTERM

# Ensure directories
mkdir -p "$LOG_DIR" "$VIDEO_DIR"

# Fix runtime directory permissions
echo "Fixing runtime directory permissions..."
chmod 0700 /run/user/1000 || true

# Mount network share
echo "Mounting network share..."
sudo mount -a || true

# Mount USB if present
echo "Checking for USB..."
if [ -b /dev/sda1 ]; then
    sudo mkdir -p /mnt/usb
    if ! mountpoint -q /mnt/usb; then
        if ! sudo mount /dev/sda1 /mnt/usb; then
            echo "Warning: Failed to mount USB device /dev/sda1"
        fi
    fi
fi

# Wait for network and Wayland
echo "Waiting for network and Wayland..."
sleep 10

# Kill existing Flask instances
echo "Killing existing kiosk processes..."
pkill -f "python3 $FLASK_APP" || true
pkill -f "python3 $KIOSK_APP" || true
pkill -f "python3 $CLEANUP_APP" || true

# Start Flask server
echo "Starting Flask server..."
python3 "$FLASK_APP" >> "$LOG_DIR/flask_server.out.log" 2>&1 &

# Start cleanup scheduler
echo "Starting video cleanup scheduler..."
python3 "$CLEANUP_APP" >> "$LOG_DIR/cleanup_videos.out.log" 2>&1 &

# Start kiosk GUI
echo "Starting kiosk GUI..."
python3 "$KIOSK_APP" >> "$LOG_DIR/kiosk.out.log" 2>&1 &

# Keep script running to handle trap
wait