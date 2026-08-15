#!/usr/bin/env python3

import argparse
import random
import signal
import sys
import time
from pathlib import Path

import tkinter as tk
from PIL import Image, ImageOps, ImageTk

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}
DEFAULT_FADE_MS = 1200


def parse_args():
    parser = argparse.ArgumentParser(description="Random photo slideshow for a Raspberry Pi kiosk")
    parser.add_argument(
        "--photo-dir",
        type=str,
        default="/media",
        help="Folder or mount root containing photos. Defaults to /media so USB drives are detected reliably.",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Seconds between image changes. Default: 30",
    )
    parser.add_argument(
        "--background",
        type=str,
        default="black",
        help="Background colour shown behind images. Default: black",
    )
    parser.add_argument(
        "--fade-ms",
        type=int,
        default=DEFAULT_FADE_MS,
        help=f"Milliseconds for the crossfade between images. Default: {DEFAULT_FADE_MS}",
    )
    return parser.parse_args()


def _collect_supported_photos(root: Path):
    photos = []
    if not root.exists() or not root.is_dir():
        return photos

    for item in sorted(root.rglob("*")):
        if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS:
            photos.append(item)

    return photos


def find_photos(photo_dir: Path):
    photo_dir = photo_dir.expanduser().resolve()
    candidates = []

    if photo_dir.exists():
        candidates.append(photo_dir)

    if photo_dir == Path("/media") or photo_dir.parent == Path("/media") or str(photo_dir).startswith("/media/"):
        media_root = Path("/media")
        if media_root.exists():
            for mount in sorted(media_root.iterdir()):
                if mount.is_dir():
                    candidates.append(mount)

    for mount in sorted(Path("/mnt").glob("*")):
        if mount.is_dir():
            candidates.append(mount)

    seen = set()
    photos = []
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        for image in _collect_supported_photos(candidate):
            photos.append(image)

    if not photos:
        raise FileNotFoundError(f"No supported image files found in: {photo_dir} or mounted media folders")

    return photos


class PhotoFrameApp:
    def __init__(self, root, photo_dir: Path, interval: int, background: str, fade_ms: int):
        self.root = root
        self.photo_dir = photo_dir
        self.interval = max(5, interval)
        self.background = background
        self.fade_ms = max(200, fade_ms)
        self.photos = find_photos(photo_dir)
        self.current_photo = None
        self.current_image = None
        self.canvas = None
        self.image_item = None
        self.fade_job = None
        self.refresh_job = None
        self.transitioning = False
        self._build_ui()
        self.refresh_photo()

    def _build_ui(self):
        self.root.title("Raspberry Pi Photo Frame")
        self.root.configure(bg=self.background)
        self.root.config(cursor="none")

        try:
            self.root.attributes("-fullscreen", 1)
            self.fullscreen_enabled = True
        except tk.TclError:
            self.fullscreen_enabled = False
            width = self.root.winfo_screenwidth()
            height = self.root.winfo_screenheight()
            self.root.geometry(f"{width}x{height}+0+0")

        self.root.bind("<Escape>", lambda event: self.root.destroy())
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Button-1>", lambda event: self.refresh_photo())
        self.root.bind("<space>", lambda event: self.refresh_photo())

        self.canvas = tk.Canvas(self.root, bg=self.background, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.image_item = self.canvas.create_image(0, 0, anchor="nw")

    def toggle_fullscreen(self, event=None):
        try:
            current = self.root.attributes("-fullscreen")
            self.root.attributes("-fullscreen", 0 if current else 1)
            self.fullscreen_enabled = not self.fullscreen_enabled
        except tk.TclError:
            self.fullscreen_enabled = not getattr(self, "fullscreen_enabled", False)
            if self.fullscreen_enabled:
                width = self.root.winfo_screenwidth()
                height = self.root.winfo_screenheight()
                self.root.geometry(f"{width}x{height}+0+0")
            else:
                self.root.geometry("")

    def _schedule_next_refresh(self):
        if self.refresh_job is not None:
            self.root.after_cancel(self.refresh_job)
        self.refresh_job = self.root.after(self.interval * 1000, self.refresh_photo)

    def _load_display_image(self, image_path: Path):
        self.root.update_idletasks()
        width = self.root.winfo_width() or self.root.winfo_screenwidth() or 1920
        height = self.root.winfo_height() or self.root.winfo_screenheight() or 1080

        width = max(int(width), 1)
        height = max(int(height), 1)

        with Image.open(image_path) as img:
            img = ImageOps.exif_transpose(img)
            img.thumbnail((width, height), Image.Resampling.LANCZOS)
            background = Image.new("RGBA", (width, height), (0, 0, 0, 255))
            x = max((width - img.width) // 2, 0)
            y = max((height - img.height) // 2, 0)
            background.paste(img.convert("RGBA"), (x, y))
            return background

    def _show_image(self, image):
        photo = ImageTk.PhotoImage(image)
        self.canvas.itemconfig(self.image_item, image=photo)
        self.canvas.image = photo
        self.root.update_idletasks()

    def _animate_fade(self, old_image, new_image, started_at):
        elapsed = time.monotonic() - started_at
        progress = min(elapsed / (self.fade_ms / 1000), 1.0)
        blended = Image.blend(old_image, new_image, progress)
        self._show_image(blended)

        if progress < 1.0:
            self.fade_job = self.root.after(20, self._animate_fade, old_image, new_image, started_at)
            return

        self.transitioning = False
        self.current_image = new_image
        self.fade_job = None
        self._schedule_next_refresh()

    def refresh_photo(self):
        if self.transitioning:
            return

        if self.refresh_job is not None:
            self.root.after_cancel(self.refresh_job)
            self.refresh_job = None

        if len(self.photos) == 1:
            selected = self.photos[0]
        else:
            options = [p for p in self.photos if p != self.current_photo]
            selected = random.choice(options or self.photos)

        self.current_photo = selected
        next_image = self._load_display_image(selected)

        if self.current_image is None:
            self.current_image = next_image
            self._show_image(next_image)
            self._schedule_next_refresh()
            return

        self.transitioning = True
        old_image = self.current_image
        self.current_image = next_image
        self.fade_job = self.root.after(0, self._animate_fade, old_image, next_image, time.monotonic())


def main():
    args = parse_args()
    photo_dir = Path(args.photo_dir).expanduser().resolve()

    root = tk.Tk()
    root.minsize(640, 480)

    try:
        app = PhotoFrameApp(root, photo_dir, args.interval, args.background, args.fade_ms)
        signal.signal(signal.SIGINT, lambda *_: root.destroy())
        root.mainloop()
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except tk.TclError as exc:
        print(f"Tkinter setup error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
