#!/bin/bash
set -e

export TK_SILENCE_DEPRECATION=1

cd "$(dirname "$0")"
source .venv/bin/activate

PHOTO_DIR="${1:-${PICTURE_FRAME_DIR:-$HOME/Pictures/frame}}"

echo "Using photo directory: $PHOTO_DIR"
python3 app.py --photo-dir "$PHOTO_DIR" --interval 30 --fade-ms 1200
