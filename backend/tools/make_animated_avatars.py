"""Generate the bundled animated GIF avatar presets.

Procedural, looping 128x128 GIFs written to frontend/public/avatars so they
are served as static assets next to the PNG presets. Run from the backend
venv:

    python tools/make_animated_avatars.py
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 128
CENTER = SIZE // 2
FRAMES = 24
FRAME_MS = 50  # 20 fps

OUT_DIR = (
    Path(__file__).resolve().parents[2] / 'frontend' / 'public' / 'avatars'
)


def _save(frames, name):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / name
    frames[0].save(
        str(path),
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_MS,
        loop=0,
        optimize=True,
    )
    print(f'wrote {path.name}: {len(frames)} frames')


def _base_disc(img, color=(16, 22, 44)):
    d = ImageDraw.Draw(img)
    d.ellipse([6, 6, SIZE - 6, SIZE - 6], fill=color)
    return d


def orbit_frames():
    """A bright orb circling a glowing core."""
    frames = []
    for i in range(FRAMES):
        t = 2 * math.pi * i / FRAMES
        img = Image.new('RGB', (SIZE, SIZE), (5, 6, 15))
        d = _base_disc(img)
        # core halo + core
        d.ellipse(
            [CENTER - 24, CENTER - 24, CENTER + 24, CENTER + 24],
            fill=(40, 70, 160),
        )
        d.ellipse(
            [CENTER - 15, CENTER - 15, CENTER + 15, CENTER + 15],
            fill=(110, 160, 255),
        )
        # orbiter: dim halo dot then bright dot
        x = CENTER + int(38 * math.cos(t))
        y = CENTER + int(38 * math.sin(t))
        d.ellipse([x - 13, y - 13, x + 13, y + 13], fill=(140, 110, 40))
        d.ellipse([x - 8, y - 8, x + 8, y + 8], fill=(255, 214, 110))
        frames.append(img)
    return frames


def pulse_frames():
    """A disc that breathes in size and brightness."""
    frames = []
    for i in range(FRAMES):
        t = (math.sin(2 * math.pi * i / FRAMES) + 1) / 2  # 0..1
        r = int(30 + 16 * t)
        img = Image.new('RGB', (SIZE, SIZE), (8, 8, 20))
        d = _base_disc(img, (14, 16, 36))
        glow = (int(60 + 60 * t), int(120 + 60 * t), 235)
        core = (int(120 + 80 * t), int(180 + 60 * t), 255)
        d.ellipse(
            [CENTER - r - 8, CENTER - r - 8, CENTER + r + 8, CENTER + r + 8],
            fill=glow,
        )
        d.ellipse(
            [CENTER - r, CENTER - r, CENTER + r, CENTER + r], fill=core
        )
        frames.append(img)
    return frames


def spin_frames():
    """A comet arc sweeping around a ring."""
    frames = []
    ring = [CENTER - 42, CENTER - 42, CENTER + 42, CENTER + 42]
    for i in range(FRAMES):
        start = 360 * i / FRAMES
        img = Image.new('RGB', (SIZE, SIZE), (10, 8, 24))
        d = _base_disc(img, (24, 16, 48))
        d.arc(ring, start, start + 360, fill=(90, 60, 140), width=10)
        # bright comet head on the leading edge
        t = math.radians(start)
        x = CENTER + int(42 * math.cos(t))
        y = CENTER + int(42 * math.sin(t))
        d.ellipse([x - 11, y - 11, x + 11, y + 11], fill=(220, 120, 255))
        d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=(255, 220, 255))
        d.ellipse(
            [CENTER - 10, CENTER - 10, CENTER + 10, CENTER + 10],
            fill=(200, 160, 255),
        )
        frames.append(img)
    return frames


def main():
    _save(orbit_frames(), 'animated-orbit.gif')
    _save(pulse_frames(), 'animated-pulse.gif')
    _save(spin_frames(), 'animated-spin.gif')


if __name__ == '__main__':
    main()
