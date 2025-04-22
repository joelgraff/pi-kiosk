#!/bin/bash
# Fix runtime directory permissions
chmod 0700 /run/user/1000

# Mount network share
sudo mount -a

# Mount USB if present
if [ -b /dev/sda1 ]; then
    sudo mkdir -p /mnt/usb
    sudo mount /dev/sda1 /mnt/usb
fi

# Wait for network and Wayland
sleep 10

# Start Flask server
python3 /home/pi/flask_server.py &

# Start VLC: Web stream to HDMI 0 (matrix Input 1)
vlc --fullscreen --no-video-title-show "$(yt-dlp -g https://www.youtube.com/watch?v=example)" &
sleep 2
wlrctl window vlc move output:HDMI-A-1

# Start VLC: MP4 to HDMI 1 (matrix Input 2)
MP4_PATH=$(find /home/pi/videos /mnt/share /mnt/usb -name "*.mp4" -print -quit 2>/dev/null)
if [ -n "$MP4_PATH" ]; then
    vlc --fullscreen --no-video-title-show "$MP4_PATH" &
    sleep 2
    wlrctl window vlc move output:HDMI-A-2
fi

# Wait for players
sleep 5

# Route Source 1 (web stream) to TVs 1 and 2 (matrix Outputs 1 and 2)
# Stubbed: curl -X POST http://192.168.10.12/api/route -d '{"input":1,"outputs":[1,2]}'
echo "Stub: Routing Input 1 to Outputs [1,2]"

# Start kiosk GUI
python3 /home/pi/kiosk.py &