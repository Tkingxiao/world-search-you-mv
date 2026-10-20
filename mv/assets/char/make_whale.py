"""make_whale.py - build the "merged paper whale" cutout used by shot s13.

The whale is *not* modelled geometry: it is a single paper cut-out (PNG with alpha) printed
with a ghosted, warm-graded crop of the official 大肥鱼 art (memory: merged) on cream paper,
with a cream paper rim.  shot_s13.py feeds it to C.paper_cutout().

Run:  python mv/assets/char/make_whale.py
Out:  mv/assets/char/whale_paper.png       (2000x1200 RGBA)
      mv/assets/char/whale_paper_small.png (0.55x - distant school copy)
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
ART = os.path.join(ROOT, "mv", "ref", "art", "galgame", "whale-starry.webp")
OUT = os.path.dirname(os.path.abspath(__file__))

W, H = 2000, 1200
SS = 3  # supersample for smooth silhouette
CREAM = np.array([236, 232, 222], dtype=np.float32)
INK = (26, 30, 44)


def _bez(pts, p0, p1, p2, p3, n=40):
    for i in range(n):
        t = i / (n - 1.0)
        u = 1.0 - t
        pts.append((u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0],
                    u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1]))


def body_points(w, h):
    """Whale profile facing +X.  Rounded back, forked fluke, belly.  Returns px points."""
    p = []
    _bez(p, (0.985, 0.520), (0.930, 0.645), (0.860, 0.760), (0.740, 0.800))
    _bez(p, (0.740, 0.800), (0.620, 0.835), (0.470, 0.815), (0.360, 0.735))
    _bez(p, (0.360, 0.735), (0.300, 0.690), (0.255, 0.640), (0.225, 0.610))
    _bez(p, (0.225, 0.610), (0.160, 0.700), (0.080, 0.800), (0.020, 0.845))
    _bez(p, (0.020, 0.845), (0.006, 0.855), (0.000, 0.840), (0.008, 0.815))
    _bez(p, (0.008, 0.815), (0.050, 0.700), (0.085, 0.600), (0.108, 0.520))
    _bez(p, (0.108, 0.520), (0.070, 0.430), (0.030, 0.330), (0.010, 0.250))
    _bez(p, (0.010, 0.250), (0.002, 0.225), (0.014, 0.210), (0.030, 0.220))
    _bez(p, (0.030, 0.220), (0.110, 0.290), (0.175, 0.360), (0.225, 0.420))
    _bez(p, (0.225, 0.420), (0.300, 0.360), (0.420, 0.300), (0.560, 0.292))
    _bez(p, (0.560, 0.292), (0.680, 0.285), (0.780, 0.330), (0.860, 0.400))
    _bez(p, (0.860, 0.400), (0.930, 0.455), (0.970, 0.490), (0.985, 0.520))
    return [(x * w, y * h) for (x, y) in p]


def fin_points(w, h):
    """Pectoral fin: a lobe hanging below the belly (its own closed polygon)."""
    p = []
    _bez(p, (0.680, 0.790), (0.660, 0.885), (0.620, 0.950), (0.575, 0.975), 30)
    _bez(p, (0.575, 0.975), (0.585, 0.910), (0.610, 0.845), (0.640, 0.795), 30)
    return [(x * w, y * h) for (x, y) in p]


def whale_mask():
    big = Image.new("L", (W * SS, H * SS), 0)
    d = ImageDraw.Draw(big)
    d.polygon(body_points(W * SS, H * SS), fill=255)
    d.polygon(fin_points(W * SS, H * SS), fill=255)
    return big.resize((W, H), Image.LANCZOS)


def art_fill():
    """Ghost print: her art, cover-scaled, blurred, blended 55/45 with cream paper."""
    art = Image.open(ART).convert("RGB")
    aw, ah = art.size
    s = max(W / aw, H / ah)
    a = art.resize((int(aw * s + 0.5), int(ah * s + 0.5)), Image.LANCZOS)
    x = (a.width - W) // 2
    y = int((a.height - H) * 0.30)          # bias to her head / upper body
    a = a.crop((x, y, x + W, y + H)).filter(ImageFilter.GaussianBlur(2.0))
    arr = np.asarray(a).astype(np.float32)
    arr = arr * 0.55 + CREAM[None, None, :] * 0.45
    arr = arr * np.array([1.03, 0.99, 0.92], dtype=np.float32) + np.array([0.035, 0.026, 0.014])
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def paper_fiber(img):
    rng = np.random.default_rng(7)
    a = np.asarray(img).astype(np.float32)
    h, w = a.shape[:2]
    coarse = rng.normal(0.0, 1.0, (h // 24 + 1, w // 24 + 1)).astype(np.float32)
    span = float(coarse.max() - coarse.min())
    coarse = np.asarray(Image.fromarray(((coarse - coarse.min()) / (span + 1e-6) * 255)
                                        .astype(np.uint8)).resize((w, h), Image.BICUBIC)).astype(np.float32)
    coarse = (coarse / 255.0 - 0.5) * 0.055
    fine = rng.normal(0.0, 0.016, (h, w)).astype(np.float32)
    a = a + (coarse[..., None] + fine[..., None]) * 255.0
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def main():
    mask = whale_mask()
    m = np.asarray(mask).astype(np.float32) / 255.0

    fill = paper_fiber(art_fill())
    a = np.asarray(fill).astype(np.float32)

    # cream wash toward the cut edge so the print fades into the paper (paper vignette)
    er = np.asarray(mask.filter(ImageFilter.MinFilter(31))).astype(np.float32) / 255.0
    edge_fade = np.clip(er * 1.35, 0.0, 1.0)[..., None]       # 0 at edge -> 1 inside
    a = a * edge_fade + CREAM[None, None, :] * (1.0 - edge_fade)

    # eye + mouth: printed in ink on the paper
    eye = Image.new("L", (W, H), 0)
    de = ImageDraw.Draw(eye)
    de.ellipse([0.878 * W, 0.500 * H, 0.912 * W, 0.548 * H], fill=255)
    de.arc([0.845 * W, 0.545 * H, 0.930 * W, 0.640 * H], start=10, end=95, fill=255, width=6)
    eye_a = np.asarray(eye.filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255.0
    ink = np.array(INK, dtype=np.float32)
    a = a * (1.0 - eye_a[..., None] * 0.85) + ink[None, None, :] * (eye_a[..., None] * 0.85)

    # cream paper rim
    rim = np.asarray(mask.filter(ImageFilter.MaxFilter(9))).astype(np.float32) - np.asarray(mask).astype(np.float32)
    rim = np.clip(rim, 0, 255)

    rgba = np.zeros((H, W, 4), dtype=np.uint8)
    rgba[..., :3] = np.clip(a * m[..., None] + CREAM[None, None, :] * (rim / 255.0)[..., None],
                            0, 255).astype(np.uint8)
    rgba[..., 3] = np.clip(np.asarray(mask).astype(np.float32) + rim, 0, 255).astype(np.uint8)
    img = Image.fromarray(rgba, "RGBA")
    p1 = os.path.join(OUT, "whale_paper.png")
    img.save(p1)
    img.resize((int(W * 0.55), int(H * 0.55)), Image.LANCZOS).save(
        os.path.join(OUT, "whale_paper_small.png"))
    print("WROTE", p1, img.size)


if __name__ == "__main__":
    main()
