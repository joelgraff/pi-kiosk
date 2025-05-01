#!/bin/bash
# Trap termination signals to clean up processes
cleanup() {
    echo "Cleaning up processes..."
    pkill -f "vlc"
    pkill -f "python3 /home/admin/flask_server.py"
    pkill -f "python3 /home/admin/kiosk.py"
    pkill -f "python3 /home/admin/cleanup_videos.py"
    exit 0
}
trap cleanup SIGINT SIGTERM

# Fix runtime directory permissions
echo "Fixing runtime directory permissions..."
chmod 0700 /run/user/1000

# Mount network share
echo "Mounting network share..."
sudo mount -a

# Mount USB if present
echo "Checking for USB..."
if [ -b /dev/sda1 ]; then
    sudo mkdir -p /mnt/usb
    sudo mount /dev/sda1 /mnt/usb
fi

# Wait for network and Wayland
echo "Waiting for network and Wayland..."
sleep 10

# Kill existing Flask instances
echo "Killing existing Flask instances..."
pkill -f "python3 /home/admin/flask_server.py"

# Start Flask server
echo "Starting Flask server..."
python3 /home/admin/flask_server.py &

# Start cleanup scheduler
echo "Starting video cleanup scheduler..."
python3 /home/admin/cleanup_videos.py &

# Start kiosk GUI
echo "Starting kiosk GUI..."
python3 /home/admin/kiosk.py &

# Keep script running to handle trap
wait