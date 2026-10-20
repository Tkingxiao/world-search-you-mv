"""make_halo.py - cyan "outline memory" halo card for shot s13 (she dissolves into her outline).

Reads the serious cell of mv/assets/char/expr_atlas.png, builds a soft ring around the art
silhouette (alpha dilate minus alpha, blurred), tints it cyan-white, saves a full-cell PNG so
it can be dropped in as a C.illustration_card() aligned with her card.

Run:  python mv/assets/char/make_halo.py
Out:  mv/assets/char/halo_serious.png   (1124x2022 RGBA)
"""
import json
import os
import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
HERE = os.path.dirname(os.path.abspath(__file__))
ATLAS = os.path.join(HERE, "expr_atlas.png")
META = os.path.join(HERE, "expr_atlas.json")

CYAN = np.array([0.22, 0.79, 1.0], dtype=np.float32)   # #38c9ff
WHITE = np.array([0.95, 0.99, 1.0], dtype=np.float32)


def main():
    meta = json.load(open(META, encoding="utf-8"))
    cell = meta["expressions"]["serious"]
    x0, y0, x1, y1 = cell["rect_px"]
    img = Image.open(ATLAS).convert("RGBA").crop((x0, y0, x1, y1))
    a = np.asarray(img)[..., 3].astype(np.float32) / 255.0
    m = Image.fromarray((a * 255).astype(np.uint8))

    ring = np.asarray(m.filter(ImageFilter.MaxFilter(13))).astype(np.float32) / 255.0 - a
    ring = np.clip(ring, 0.0, 1.0)
    ring_img = Image.fromarray((ring * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3.0))
    ring = np.asarray(ring_img).astype(np.float32) / 255.0

    # soft outer halo only: blur the *ring* (dilated alpha minus alpha), never the filled body,
    # otherwise the whole silhouette glows as a solid ghost instead of an outline.
    outer = np.clip(np.asarray(m.filter(ImageFilter.MaxFilter(41))).astype(np.float32) / 255.0 - a, 0.0, 1.0)
    glow = np.asarray(Image.fromarray((outer * 255).astype(np.uint8))
                      .filter(ImageFilter.GaussianBlur(22))).astype(np.float32) / 255.0
    glow = np.clip(glow, 0.0, 1.0) * 0.60

    alpha = np.clip(ring + glow, 0.0, 1.0)
    # pure cyan, slightly desaturated at the hottest part of the ring
    col = np.clip(CYAN[None, None, :] * (0.72 + 0.28 * np.clip(ring * 2.4, 0, 1))[..., None], 0.0, 1.0)

    rgba = np.zeros((*alpha.shape, 4), dtype=np.uint8)
    rgba[..., :3] = (col * 255).astype(np.uint8)
    rgba[..., 3] = (alpha * 255).astype(np.uint8)
    out = os.path.join(HERE, "halo_serious.png")
    Image.fromarray(rgba, "RGBA").save(out)
    print("WROTE", out, img.size, "max alpha", float(alpha.max()))


if __name__ == "__main__":
    main()
