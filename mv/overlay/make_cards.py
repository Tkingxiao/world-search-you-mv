#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_cards.py — 2560×1440 RGBA 文字卡（片名 / 8 张章卡 / 片尾）

排版与 film.ass 同一套数值（几何/字号/颜色都从 hud_timeline 取），
保证"烧进视频的 HUD"与"独立 PNG 卡"看起来是同一个设计系统。
纸纹用 numpy 现场生成（低频斑块 + 横向纤维 + 细颗粒 + 边缘暗化），不用外部贴图。

用法：
  python mv/overlay/make_cards.py            # 生成 mv/overlay/cards/*.png
  python mv/overlay/make_cards.py --preview  # 另出 mv/out/tests/ui/cards_sheet.png（合成在测试底上目检）
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import hud_timeline as ht  # noqa: E402

ROOT = ht.ROOT
OUT = ROOT / "mv/overlay/cards"
FONTS = ROOT / "mv/overlay/fonts"
TESTS = ROOT / "mv/out/tests/ui"

W, H = ht.W, ht.H
PAPER, INK, GOLD, BLUE, ABYSS = ht.PAPER, ht.INK, ht.GOLD, ht.BLUE, ht.ABYSS

# 章节条几何与 film.ass 完全一致
CX0, CX1, CY0, CY1 = ht.CARD_X0, ht.CARD_X1, ht.CARD_Y0, ht.CARD_Y1
CCY = ht.CARD_CY


# --------------------------------------------------------------------------- #
# 字体
# --------------------------------------------------------------------------- #
def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / name), size)


def f_serif_i(size: int) -> ImageFont.FreeTypeFont:
    return font("georgiai.ttf", size)


def f_serif(size: int) -> ImageFont.FreeTypeFont:
    return font("georgia.ttf", size)


def f_mono(size: int) -> ImageFont.FreeTypeFont:
    return font("consola.ttf", size)


def f_zh(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / "msyhl.ttc"), size, index=0)


# --------------------------------------------------------------------------- #
# 字距排版（PIL 没有 tracking，手动逐字）
# --------------------------------------------------------------------------- #
def tw(fnt: ImageFont.FreeTypeFont, s: str, tracking: float) -> float:
    if not s:
        return 0.0
    return sum(fnt.getlength(ch) for ch in s) + tracking * (len(s) - 1)


def draw_tracked(im: Image.Image, xy: tuple[float, float], s: str,
                 fnt: ImageFont.FreeTypeFont, fill, tracking: float = 0.0,
                 anchor: str = "lm") -> None:
    """anchor: 'l'/'m'/'r' + 'm'(vertical middle)。xy 为锚点。"""
    d = ImageDraw.Draw(im)
    total = tw(fnt, s, tracking)
    x, y = xy
    if anchor[0] == "m":
        x -= total / 2
    elif anchor[0] == "r":
        x -= total
    for ch in s:
        d.text((x, y), ch, font=fnt, fill=fill, anchor="l" + anchor[1:])
        x += fnt.getlength(ch) + tracking


# --------------------------------------------------------------------------- #
# 纸纹 / 底纹
# --------------------------------------------------------------------------- #
def _noise(h: int, w: int, seed: int, stretch_x: int = 1) -> np.ndarray:
    rng = np.random.default_rng(seed)
    small = rng.normal(0, 1, (max(2, h // 8 + 2), max(2, w // (8 * stretch_x) + 2))).astype(np.float32)
    im = Image.fromarray(((small - small.min()) / (np.ptp(small) + 1e-6) * 255).astype(np.uint8))
    im = im.resize((w, h), Image.BICUBIC)
    return np.asarray(im, np.float32) / 255.0 - 0.5


def paper_rgba(w: int, h: int, seed: int = 7, base=PAPER, alpha: int = 235,
               edge: float = 0.10) -> Image.Image:
    """一张有纤维感的纸（RGBA）。"""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u, v = xx / max(1, w - 1), yy / max(1, h - 1)

    blot = _noise(h, w, seed, stretch_x=2)            # 低频斑块
    fib = _noise(h, w, seed + 1, stretch_x=8)         # 横向纤维（纸的丝缕）
    grain = _noise(h, w, seed + 2, stretch_x=1)       # 细颗粒
    # 再加一层很细的斜向纤维
    diag = _noise(h, w, seed + 3, stretch_x=1)

    lum = 1.0 + blot * 0.035 + fib * 0.030 + grain * 0.012 + diag * 0.008
    # 边缘轻微压暗（纸标签被翻动过的磨损感）
    d = np.minimum(np.minimum(u, 1 - u) * w, np.minimum(v, 1 - v) * h)
    lum *= 1.0 - edge * np.exp(-d / 10.0)

    arr = np.array(base, np.float32) / 255.0
    rgb = np.clip(arr[None, None, :] * lum[..., None], 0, 1)
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = (rgb * 255).astype(np.uint8)
    out[..., 3] = alpha
    return Image.fromarray(out, "RGBA")


def abyss_bg(seed: int = 2026, dark: float = 1.0) -> Image.Image:
    """片名/片尾卡的底：深水色渐变 + 两团微光 + 纤维噪声 + 暗角。"""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    u, v = xx / (W - 1), yy / (H - 1)

    top = np.array([0.043, 0.106, 0.137])
    mid = np.array([0.020, 0.060, 0.082])
    bot = np.array([0.012, 0.024, 0.034])
    t = v[..., None]
    lo = top + (mid - top) * np.clip(t / 0.55, 0, 1)
    hi = mid + (bot - mid) * np.clip((t - 0.55) / 0.45, 0, 1)
    img = np.where(t < 0.55, lo, hi)

    def glow(cx, cy, r, color, s):
        d = np.sqrt(((u - cx) * W / H) ** 2 + (v - cy) ** 2)
        return (np.exp(-(d / r) ** 2) * s)[..., None] * np.array(color, np.float32)

    img += glow(0.72, 0.16, 0.40, (0.10, 0.30, 0.42), 0.50)
    img += glow(0.28, 0.86, 0.34, (0.26, 0.18, 0.09), 0.26)

    d = np.sqrt((u - 0.5) ** 2 + (v - 0.5) ** 2) / 0.7071
    img *= (1.0 - 0.50 * d ** 2.2)[..., None]

    rng = np.random.default_rng(seed)
    n1 = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
    n1 = np.kron(n1, np.ones((2, 2), np.float32))
    n2 = rng.normal(0, 1, (H, W)).astype(np.float32)
    img += (n1 * 0.006 + n2 * 0.004)[..., None]
    img *= dark

    arr = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    return Image.fromarray(arr, "RGB").convert("RGBA")


def shadow_of(shape: Image.Image, blur: int = 22, alpha: int = 90) -> Image.Image:
    a = shape.split()[3].filter(ImageFilter.GaussianBlur(blur))
    a = a.point(lambda x: int(x * alpha / 255))
    sh = Image.new("RGBA", shape.size, (0, 0, 0, 0))
    sh.putalpha(a)
    return sh


# --------------------------------------------------------------------------- #
# 卡 1：片名
# --------------------------------------------------------------------------- #
def card_title() -> Image.Image:
    # 独立片名卡没有下方署名，整体光心下移 ~110px（片尾卡因为要留署名区，锁版偏上）
    im = abyss_bg()
    draw_tracked(im, (W / 2, 562), "MILI", f_mono(20), GOLD + (255,), tracking=8, anchor="mm")
    draw_tracked(im, (W / 2, 670), "world.search(you);", f_serif_i(112), PAPER + (255,),
                 tracking=2, anchor="mm")
    d = ImageDraw.Draw(im)
    d.rectangle([900, 750, 1660, 752], fill=GOLD + (115,))
    draw_tracked(im, (W / 2, 810), "from the album Hue", f_serif_i(38), PAPER + (185,),
                 tracking=1, anchor="mm")
    return im


# --------------------------------------------------------------------------- #
# 卡 2：章节条（透明底，只有纸标签本身）
# --------------------------------------------------------------------------- #
def card_chapter(num: str, name: str, data: str, seed: int) -> Image.Image:
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cw, ch = CX1 - CX0, CY1 - CY0

    # 纸标签（带纤维）+ 轻投影
    strip = paper_rgba(cw, ch, seed=seed, alpha=238, edge=0.12)
    shadow = shadow_of(strip, blur=26, alpha=70)
    im.alpha_composite(shadow, (CX0, CY0 + 12))
    im.alpha_composite(strip, (CX0, CY0))

    # 内衬细线（ink，45%）
    d = ImageDraw.Draw(im)
    inset = 14
    x0, y0, x1, y1 = CX0 + inset, CY0 + inset, CX1 - inset, CY1 - inset
    ink45 = INK + (115,)
    d.rectangle([x0, y0, x1, y1], outline=ink45, width=2)

    # 编号 / 章名 / 数据（与 ASS 同位）
    draw_tracked(im, (348, CCY), num, f_serif_i(150), INK + (255,), tracking=0, anchor="lm")
    draw_tracked(im, (604, CCY), name, f_serif(76), INK + (255,), tracking=14, anchor="lm")
    draw_tracked(im, (CX1 - 40, CCY), data, f_mono(21), INK + (168,), tracking=1.2, anchor="rm")
    return im


# --------------------------------------------------------------------------- #
# 卡 3：片尾
# --------------------------------------------------------------------------- #
def card_end() -> Image.Image:
    im = abyss_bg(dark=0.82)
    draw_tracked(im, (W / 2, 452), "MILI", f_mono(20), GOLD + (185,), tracking=8, anchor="mm")
    draw_tracked(im, (W / 2, 560), "world.search(you);", f_serif_i(112), PAPER + (230,),
                 tracking=2, anchor="mm")
    d = ImageDraw.Draw(im)
    d.rectangle([900, 640, 1660, 642], fill=GOLD + (115,))
    draw_tracked(im, (W / 2, 700), "from the album Hue", f_serif_i(38), PAPER + (185,),
                 tracking=1, anchor="mm")

    draw_tracked(im, (W / 2, 852), "CHARACTER ART", f_mono(20), PAPER + (185,),
                 tracking=8, anchor="mm")

    # 混合字体的署名行：中文 YaHei Light / 拉丁 Georgia italic / 金色 ·
    segs = [
        ("角色美术：溟月 \u00a9 上善无形", f_zh(25), PAPER + (185,), 0.5),
        ("  \u00b7  ", f_mono(19), GOLD + (140,), 0.0),
        ("女仆版 ", f_zh(25), PAPER + (185,), 0.5),
        ("ZipZipPipe", f_serif_i(26), PAPER + (185,), 0.5),
        ("  \u00b7  ", f_mono(19), GOLD + (140,), 0.0),
        ("立绘 ", f_zh(25), PAPER + (185,), 0.5),
        ("Small-tailqwq", f_serif_i(26), PAPER + (185,), 0.5),
        ("  \u00b7  ", f_mono(19), GOLD + (140,), 0.0),
        ("表情 ", f_zh(25), PAPER + (185,), 0.5),
        ("JAdpp", f_serif_i(26), PAPER + (185,), 0.5),
    ]
    total = sum(tw(f, s, tr) for s, f, _, tr in segs)
    x = W / 2 - total / 2
    for s, f, col, tr in segs:
        draw_tracked(im, (x, 898), s, f, col, tracking=tr, anchor="lm")
        x += tw(f, s, tr)

    draw_tracked(im, (W / 2, 952), "licensed under CC BY-NC-SA 4.0", f_mono(20),
                 PAPER + (185,), tracking=2, anchor="mm")
    draw_tracked(im, (W / 2, 1320), "THE MUSEUM OF APPROXIMATIONS", f_mono(20),
                 PAPER + (140,), tracking=8, anchor="mm")
    return im


# --------------------------------------------------------------------------- #
def make_all() -> list[Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    made: list[Path] = []

    p = OUT / "card_title.png"
    card_title().save(p)
    made.append(p)

    for sec in ht.chapter_sections(ht.load_timeline()):
        num, name = sec["stage"].split(" ", 1)
        p = OUT / f"card_chapter_{num}_{name.lower()}.png"
        card_chapter(num, name, ht.CARD_DATA.get(num, ""), seed=100 + int(num)).save(p)
        made.append(p)

    p = OUT / "card_end.png"
    card_end().save(p)
    made.append(p)

    for p in made:
        im = Image.open(p)
        print(f"  {p.relative_to(ROOT)}  {im.size[0]}×{im.size[1]} {im.mode}")
    print(f"共 {len(made)} 张 → {OUT.relative_to(ROOT)}")
    return made


def preview(made: list[Path]) -> None:
    """把卡合成到测试底上目检（章卡是透明底，必须垫图才看得出效果）。"""
    TESTS.mkdir(parents=True, exist_ok=True)
    plate = Image.open(TESTS / "qc_plate.png").convert("RGBA") if (TESTS / "qc_plate.png").exists() else None
    if plate is None:
        from render_overlay import make_test_plate  # 兜底
        tmp = TESTS / "qc_plate.png"
        make_test_plate(tmp)
        plate = Image.open(tmp).convert("RGBA")

    tw_, th_ = 640, 360
    items = [(p, "title/end" if "chapter" not in p.name else "chapter") for p in made]
    cols = 2
    rows = (len(items) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw_, rows * th_), (6, 8, 10))
    for i, (p, _) in enumerate(items):
        card = Image.open(p).convert("RGBA").resize((W, H), Image.LANCZOS)
        comp = plate.copy()
        comp.alpha_composite(card)
        thumb = comp.convert("RGB").resize((tw_, th_), Image.LANCZOS)
        sheet.paste(thumb, ((i % cols) * tw_, (i // cols) * th_))
    out = TESTS / "cards_sheet.png"
    sheet.save(out)
    print(f"  preview → {out.relative_to(ROOT)}")


def main() -> None:
    ap = argparse.ArgumentParser(description="生成 2560×1440 RGBA 文字卡")
    ap.add_argument("--preview", action="store_true", help="另出合成目检图")
    args = ap.parse_args()
    made = make_all()
    if args.preview:
        preview(made)


if __name__ == "__main__":
    main()
