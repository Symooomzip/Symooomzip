"""Turn a photo into an animated ASCII-art SVG portrait.

Pipeline: rembg cuts the subject out of the background -> crop to the subject
-> CLAHE contrast boost -> sample to a character grid -> map luminance onto a
density ramp. Each row is revealed by a horizontal wipe, top to bottom.

Usage:  python scripts/gen_ascii.py assets/me.jpg
"""

import sys

import numpy as np
from PIL import Image, ImageOps

from theme import MAGENTA, MONO, PANEL, BORDER, STEEL_HI

OUT = "assets/avi-ascii.svg"

W = 370          # must pair with info-card width to total 860
COLS = 92
FS = 6.6         # font-size px
LH = 6.6         # line height px
PAD = 10
CHAR_AR = 0.6    # monospace advance / font-size
TARGET_H = 490   # match the info-card height exactly
TARGET_AR = W / TARGET_H

# dark -> bright
RAMP = " .`:-=+*cs#%@"


def head_crop(img, alpha):
    """Crop to a head-and-shoulders frame at TARGET_AR, centred on the face.

    Without this the torso dominates the character grid and the face loses
    its detail budget. Falls back to the top of the subject if no face is found.
    """
    w, h = img.size
    solid = alpha > 0.5
    widths = solid.sum(axis=1)

    rows = np.where(widths > w * 0.04)[0]
    top = int(rows[0]) if len(rows) else 0

    # head width = widest row in the upper third (skull, below the hair taper)
    upper = widths[top:top + max(1, int(h * 0.33))]
    head_w = float(upper.max()) if upper.size else w

    # shoulders = first row that flares well past the head
    flare = np.where(widths[top:] > head_w * 1.45)[0]
    shoulder = int(top + flare[0]) if len(flare) else h

    # only a sliver of shoulder -- more than this and the torso (and, here,
    # a raised hand) comes back into frame and out-shouts the face
    bottom = min(h, int(shoulder + (shoulder - top) * 0.07))
    ch = max(1, bottom - top)
    cw = min(w, ch * TARGET_AR)

    # centre on the head's horizontal centroid, not the torso's
    band = solid[top:shoulder] if shoulder > top else solid
    cols_on = np.where(band.any(axis=0))[0]
    cx = float(cols_on.mean()) if cols_on.size else w / 2

    x0 = int(max(0, min(w - cw, cx - cw / 2)))
    box = (x0, top, int(x0 + cw), bottom)
    print(f"  head_w={head_w:.0f} shoulder_y={shoulder} -> crop {box}")

    return img.crop(box), alpha[box[1]:box[3], box[0]:box[2]]


def load_cutout(path):
    """Return (gray float array 0..1, alpha mask 0..1) cropped to the subject."""
    img = Image.open(path).convert("RGB")
    img = ImageOps.exif_transpose(img)

    try:
        from rembg import remove
        cut = remove(img)  # RGBA
        alpha = np.asarray(cut.split()[-1], dtype=np.float32) / 255.0
    except Exception as e:  # pragma: no cover - fallback if rembg unavailable
        print(f"  rembg unavailable ({e}); keeping full frame", file=sys.stderr)
        alpha = np.ones((img.height, img.width), dtype=np.float32)

    # crop to subject bounding box with a small margin
    ys, xs = np.where(alpha > 0.35)
    if len(ys):
        m = 8
        y0, y1 = max(0, ys.min() - m), min(alpha.shape[0], ys.max() + m)
        x0, x1 = max(0, xs.min() - m), min(alpha.shape[1], xs.max() + m)
        img = img.crop((x0, y0, x1, y1))
        alpha = alpha[y0:y1, x0:x1]

    img, alpha = head_crop(img, alpha)

    gray = np.asarray(img.convert("L"), dtype=np.uint8)

    try:
        import cv2
        gray = cv2.createCLAHE(clipLimit=2.6, tileGridSize=(8, 8)).apply(gray)
    except Exception:
        gray = np.asarray(ImageOps.autocontrast(Image.fromarray(gray), cutoff=2))

    return gray.astype(np.float32) / 255.0, alpha


def to_grid(gray, alpha):
    h, w = gray.shape
    rows = max(1, int(round(COLS * (h / w) * CHAR_AR * (FS / LH))))

    g = np.asarray(Image.fromarray((gray * 255).astype(np.uint8))
                   .resize((COLS, rows), Image.LANCZOS), dtype=np.float32) / 255.0
    a = np.asarray(Image.fromarray((alpha * 255).astype(np.uint8))
                   .resize((COLS, rows), Image.LANCZOS), dtype=np.float32) / 255.0

    # stretch the subject's own range so the ramp uses every character
    sub = g[a > 0.5]
    if sub.size:
        lo, hi = np.percentile(sub, 2), np.percentile(sub, 98)
        if hi > lo:
            g = np.clip((g - lo) / (hi - lo), 0, 1)

    lines = []
    for r in range(rows):
        line = []
        for c in range(COLS):
            if a[r, c] < 0.45:
                line.append(" ")
            else:
                idx = int(round(g[r, c] * (len(RAMP) - 1)))
                line.append(RAMP[idx])
        lines.append("".join(line).rstrip())
    # drop fully blank leading/trailing rows
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def build(lines):
    # lock the card height and derive the line pitch from the row count, so the
    # portrait always sits flush with the info card beside it
    h = TARGET_H
    lh = (h - PAD * 2) / len(lines)
    inner = W - PAD * 2
    clips, texts = [], []

    for i, line in enumerate(lines):
        y = PAD + (i + 1) * lh
        d = round(0.15 + i * 0.028, 3)
        clips.append(
            f'<clipPath id="r{i}"><rect x="{PAD}" y="{y - lh}" width="0" height="{lh + 1}">'
            f'<animate attributeName="width" from="0" to="{inner}" dur="0.42s" '
            f'begin="{d}s" fill="freeze"/></rect></clipPath>'
        )
        safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        n = len(line)
        tl = f' textLength="{round(inner * n / COLS, 2)}" lengthAdjust="spacing"' if n > 1 else ""
        texts.append(
            f'<text clip-path="url(#r{i})" x="{PAD}" y="{y}" xml:space="preserve"'
            f'{tl}>{safe}</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-label="ASCII portrait">
  <defs>
    <linearGradient id="ink" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="{h}">
      <stop offset="0%" stop-color="{STEEL_HI}"/>
      <stop offset="55%" stop-color="#8f7fb5"/>
      <stop offset="100%" stop-color="{MAGENTA}"/>
    </linearGradient>
    {"".join(clips)}
  </defs>
  <rect width="{W}" height="{h}" rx="14" fill="{PANEL}" stroke="{BORDER}"/>
  <g font-family="{MONO}" font-size="{round(lh, 2)}" fill="url(#ink)">
    {"".join(texts)}
  </g>
</svg>
"""


def main():
    if len(sys.argv) < 2:
        print("usage: python scripts/gen_ascii.py <photo>", file=sys.stderr)
        return 1
    gray, alpha = load_cutout(sys.argv[1])
    lines = to_grid(gray, alpha)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(build(lines))
    print(f"wrote {OUT} ({COLS}x{len(lines)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
