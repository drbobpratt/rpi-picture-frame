from pathlib import Path
from PIL import Image, ImageDraw

folder = Path("/tmp/picture-frame-test")
folder.mkdir(exist_ok=True)

colors = [(255, 0, 0), (0, 180, 0), (0, 0, 255), (255, 165, 0)]
for i, color in enumerate(colors, 1):
    img = Image.new("RGB", (1200, 800), color)
    d = ImageDraw.Draw(img)
    d.text((80, 80), f"Test Image {i}", fill=(255, 255, 255))
    img.save(folder / f"test_{i}.png")

print("Created test images in", folder)