#!/bin/bash
set -e

cd "$(dirname "$0")"
export TK_SILENCE_DEPRECATION=1

mkdir -p /tmp/picture-frame-test

python3 - <<'PY'
from pathlib import Path
from PIL import Image, ImageDraw

folder = Path('/tmp/picture-frame-test')
folder.mkdir(exist_ok=True)

colors = [
    (255, 90, 90),
    (90, 180, 255),
    (90, 220, 120),
    (255, 180, 90),
    (200, 120, 255),
    (255, 255, 120),
]

for i, color in enumerate(colors, 1):
    img = Image.new('RGB', (1600, 900), color)
    draw = ImageDraw.Draw(img)
    draw.rectangle((80, 80, 1520, 820), outline=(255, 255, 255), width=8)
    draw.text((220, 360), f'Test Photo {i}', fill=(255, 255, 255), size=120)
    img.save(folder / f'test_{i}.png')

print(f'Created {len(colors)} sample images in {folder}')
PY

source .venv/bin/activate
python3 app.py --photo-dir /tmp/picture-frame-test --interval 5 --fade-ms 800
