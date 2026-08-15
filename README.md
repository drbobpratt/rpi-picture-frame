# Raspberry Pi Picture Frame

This project runs a fullscreen slideshow on a Raspberry Pi 5 with a connected 10" touchscreen. It scans a local folder of photos, randomly selects an image, and changes the display every 30 seconds.

## Features

- Full-screen kiosk display
- Random image selection from a local folder
- 30-second slideshow interval by default
- Works well with a Raspberry Pi 5 and 10" touchscreen
- Easy to run from startup on boot

## Requirements

- Raspberry Pi OS (or any Debian-based Linux system with X11)
- Python 3
- Pillow (`pip install -r requirements.txt`)

## Setup

1. Open a terminal in this project directory.
2. Install dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Put your photos in a folder, for example:

   ```bash
   mkdir -p ~/Pictures/frame
   ```

4. Start the app:

   ```bash
   python3 app.py --photo-dir ~/Pictures/frame --interval 30
   ```

5. To stop the app, press `Esc` or close the window.

## Kiosk mode on startup

The easiest Raspberry Pi setup is to auto-launch the app after login using a desktop autostart file.

Create this file:

```bash
mkdir -p ~/.config/autostart
nano ~/.config/autostart/photo-frame.desktop
```

Then add:

```ini
[Desktop Entry]
Type=Application
Name=Photo Frame
Exec=/home/pi/rpi-picture-frame/run.sh
X-GNOME-Autostart-enabled=true
```

Create a helper script:

```bash
nano ~/rpi-picture-frame/run.sh
```

With content:

```bash
#!/bin/bash
cd /home/pi/rpi-picture-frame
source .venv/bin/activate
python3 app.py --photo-dir /home/pi/Pictures/frame --interval 30
```

Then make it executable:

```bash
chmod +x ~/rpi-picture-frame/run.sh
```

## Configuration

You can override the photo directory, interval, and fade timing while launching:

```bash
python3 app.py --photo-dir /path/to/photos --interval 60 --fade-ms 1200
```

The `--fade-ms` option controls how long the crossfade lasts between photos. A value near `1200` is a smooth kiosk-friendly transition.

## Systemd startup service

A ready-to-copy service file is included at `picture-frame.service`.

On the Raspberry Pi, install and enable it with:

```bash
sudo cp ~/rpi-picture-frame/picture-frame.service /etc/systemd/system/picture-frame.service
sudo systemctl daemon-reload
sudo systemctl enable picture-frame.service
```

This only registers the service for boot startup; it does not run it immediately.

## Files in this project

- `app.py`: main slideshow app
- `requirements.txt`: Python dependencies
- `run.sh`: launcher script for kiosk startup
- `picture-frame.service`: systemd unit for boot startup
- `README.md`: setup instructions

## Notes

- The app uses a random image selection and avoids showing the same photo twice back-to-back when possible.
- It runs in fullscreen and hides the cursor for a cleaner kiosk appearance.
