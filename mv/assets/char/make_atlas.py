"""Build the paper-doll texture atlas from the official galgame art (read-only source).

Writes (all under mv/assets/char/):
  expr_atlas.png   3x3 cells: the 8 expressions + the `maid` lift-skirt pose (cell 9).
                   All cells are pasted 1:1 (never resampled) and aligned on a shared
                   FEET ANCHOR = bottom-centre of the alpha bbox, so hard-cutting
                   between expressions never moves the ground contact point.
  expr_atlas.json  cell rects, alpha bboxes, feet / head / face anchors in cell px and
                   atlas UV, and the exact Mapping-node (scale, location) per expression.
  maid_card.png    the maid pose as a standalone single card (for prop use)
  maid_card.json

Alpha hygiene: every cell is colour-bled 8 px into its transparent margin (the source
matte RGB is dirty: whale images ~0.06-0.21, maid-left is a WHITE matte ~0.96) so
bilinear / mip filtering can never pull a white or dark fringe into the silhouette.

Mapping convention (Blender): Texture Coordinate.UV -> Mapping(scale, location) ->
Image Texture(extension=CLIP). Mesh UV is the plain 0..1 card; per expression we map
that rectangle onto its cell, keeping the feet anchor pinned.

Usage: python mv/assets/char/make_atlas.py
"""
import json
import os
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
GAL = os.path.join(ROOT, "mv", "ref", "art", "galgame")
OUT = os.path.join(ROOT, "mv", "assets", "char")
DIAG = os.path.join(ROOT, "mv", "out", "tests", "char", "_diag")

EXPRESSIONS = ["angry", "cheerful", "confused", "exasperated",
               "frightened", "serious", "shy", "starry"]
MAID = "maid"
CELL_KEYS = EXPRESSIONS + [MAID]
COLS, ROWS = 3, 3
PAD = 8              # px padding inside each cell
BLEED = 8            # px of colour bleed into transparent area
ALPHA_LO = 0.02      # "any ink" threshold for content bbox
ALPHA_SOLID = 0.5    # solid threshold

# The `height` parameter of build_character() maps this many art pixels to 1.75 m.
# 1653 px = alpha-bbox height of the neutral standing expression (`serious`): her
# head-top-to-feet height. Every expression keeps its NATIVE scale (no per-cell
# rescaling => zero distortion of the official art); only the maid pose, which was
# drawn on a 1.2x larger canvas, is normalised so her body reads the same size.
HEIGHT_REF_PX = 1653.0


# ----------------------------------------------------------------------------- helpers
def load_rgba(path):
    im = Image.open(path)
    im.load()
    return im.convert("RGBA")


def analyze(rgba, band_rows=60):
    """Content bbox, shared feet anchor (bottom-centre of the alpha bbox), head & face anchors."""
    a = np.asarray(rgba)
    h, w = a.shape[:2]
    al = a[..., 3].astype(np.float32) / 255.0
    any_ink = al > ALPHA_LO
    solid = al > ALPHA_SOLID
    ys, xs = np.nonzero(any_ink)
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    rows_cnt = solid.sum(axis=1)
    solid_bottom = int(np.nonzero(rows_cnt >= 8)[0].max())
    # feet anchor (spec): bottom-centre of the alpha bbox. Much more stable across poses
    # than a shoe-span midpoint (measured x spread 29 px vs 57 px over the 8 expressions).
    feet_cx = (float(x0) + float(x1)) / 2.0
    feet_y = float(y1)
    band = solid[max(0, solid_bottom - band_rows): solid_bottom + 1]
    cols = np.nonzero(band.any(axis=0))[0]
    if len(cols) == 0:
        cols = np.nonzero(solid[h - band_rows:].any(axis=0))[0]
    # head anchor: alpha centroid of the top 18 % of the content bbox
    top_band = max(2, int(round((y1 - y0 + 1) * 0.18)))
    tb = al[y0:y0 + top_band, :]
    yy, xx = np.nonzero(tb > 0.15)
    if len(yy):
        head_cx, head_cy = float(xx.mean()), float(y0 + yy.mean())
    else:
        head_cx, head_cy = feet_cx, float(y0 + 0.08 * (y1 - y0))
    # face anchor: skin-colour centroid in the top 45 % of the figure (eyes level proxy)
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    skin = (r > 196) & (g > 158) & (b > 140) & (r - b > 14) & (r - g < 34) & solid
    fig_h = y1 - y0 + 1
    skin_top = skin[y0:y0 + int(round(fig_h * 0.45)), :]
    yy2, xx2 = np.nonzero(skin_top)
    if len(yy2) > 1500:
        face_cx, face_cy, face_ok = float(xx2.mean()), float(y0 + yy2.mean()), True
    else:
        face_cx, face_cy, face_ok = head_cx, head_cy, False
    return dict(
        size=[w, h], bbox=[x0, y0, x1, y1],
        content_size=[x1 - x0 + 1, y1 - y0 + 1],
        feet_anchor=[feet_cx, feet_y],
        shoe_span=[int(cols.min()), int(cols.max())],
        solid_bottom=solid_bottom,
        head_anchor=[head_cx, head_cy],
        face_anchor=[face_cx, face_cy], face_ok=face_ok,
    )


def bleed_rgb(rgba, radius=BLEED, box=None):
    """Fill the RGB of transparent pixels with the nearest opaque colour (alpha untouched).
    No resampling: only RGB of alpha~0 pixels is written, so the artwork itself is intact."""
    a = np.asarray(rgba).copy()
    h, w = a.shape[:2]
    al = a[..., 3].astype(np.float32) / 255.0
    x0, y0, x1, y1 = box
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(w - 1, x1), min(h - 1, y1)
    sub = a[y0:y1 + 1, x0:x1 + 1]
    known = al[y0:y1 + 1, x0:x1 + 1] > 0.03
    rgb = sub[..., :3].astype(np.float32)
    for _ in range(radius):
        if known.all():
            break
        acc = np.zeros_like(rgb)
        cnt = np.zeros(known.shape, np.float32)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)):
            kk = np.roll(np.roll(known, dy, axis=0), dx, axis=1)
            rr = np.roll(np.roll(rgb, dy, axis=0), dx, axis=1)
            m = kk & (~known)
            acc[m] += rr[m]
            cnt[m] += 1
        new = (~known) & (cnt > 0)
        rgb[new] = acc[new] / cnt[new][:, None]
        known = known | new
    sub[..., :3] = np.clip(rgb + 0.5, 0, 255).astype(np.uint8)
    a[y0:y1 + 1, x0:x1 + 1] = sub
    return Image.fromarray(a, "RGBA")


def place_anchored(canvas, img, info, dst_anchor, bleed=BLEED):
    """Paste `img` into `canvas` so its feet anchor lands on `dst_anchor` (canvas px).

    Raw RGBA paste (NOT alpha_composite) so the colour-bled RGB survives under alpha=0.
    The pasted crop is the alpha bbox expanded by `bleed` px (edge-replicated if the
    source canvas is tighter than that) so the padding around the art carries art
    colour instead of the dirty/white matte.
    Returns (off_x, off_y): source px + off -> canvas px."""
    w, h = info["size"]
    x0, y0, x1, y1 = info["bbox"]
    bx0, by0, bx1, by1 = x0 - bleed, y0 - bleed, x1 + 1 + bleed, y1 + 1 + bleed
    pad_l, pad_t = max(0, -bx0), max(0, -by0)
    pad_r, pad_b = max(0, bx1 - w), max(0, by1 - h)
    src = np.asarray(img)
    if pad_l or pad_t or pad_r or pad_b:
        src = np.pad(src, ((pad_t, pad_b), (pad_l, pad_r), (0, 0)), mode="edge")
    bled = bleed_rgb(Image.fromarray(src, "RGBA"), bleed,
                     (bx0 + pad_l, by0 + pad_t, bx1 - 1 + pad_l, by1 - 1 + pad_t))
    crop = bled.crop((bx0 + pad_l, by0 + pad_t, bx1 + pad_l, by1 + pad_t))
    fx, fy = info["feet_anchor"]
    dst_x = int(round(dst_anchor[0] - (fx - bx0)))
    dst_y = int(round(dst_anchor[1] - (fy - by0)))
    canvas.paste(crop, (dst_x, dst_y))
    return dst_x - bx0, dst_y - by0


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(DIAG, exist_ok=True)

    # ---------------------------------------------------------------- analyse sources
    infos = {}
    for e in EXPRESSIONS:
        p = os.path.join(GAL, f"whale-{e}.webp")
        img = load_rgba(p)
        infos[e] = analyze(img)
        infos[e]["image"] = img
        infos[e]["source"] = os.path.relpath(p, ROOT).replace("\\", "/")
    p = os.path.join(GAL, "maid-left.webp")
    maid_img = load_rgba(p)
    infos[MAID] = analyze(maid_img)
    infos[MAID]["image"] = maid_img
    infos[MAID]["source"] = os.path.relpath(p, ROOT).replace("\\", "/")
    for k in CELL_KEYS:
        i = infos[k]
        print(f"{k:12s} canvas={i['size']} bbox={i['bbox']} content={i['content_size']} "
              f"feet={[round(v, 1) for v in i['feet_anchor']]} shoe_span={i['shoe_span']} "
              f"head={[round(v, 1) for v in i['head_anchor']]} face_ok={i['face_ok']}")

    # ---------------------------------------------------------------- grid geometry
    max_left = max(infos[k]["feet_anchor"][0] - infos[k]["bbox"][0] for k in CELL_KEYS)
    max_right = max(infos[k]["bbox"][2] - infos[k]["feet_anchor"][0] for k in CELL_KEYS)
    max_top = max(infos[k]["feet_anchor"][1] - infos[k]["bbox"][1] for k in CELL_KEYS)
    max_bottom = max(infos[k]["bbox"][3] - infos[k]["feet_anchor"][1] for k in CELL_KEYS)
    cell_w = int(np.ceil(max_left + max_right + 2 * PAD))
    cell_h = int(np.ceil(max_top + max_bottom + 2 * PAD))
    if cell_w % 2:
        cell_w += 1
    if cell_h % 2:
        cell_h += 1
    anchor_x = cell_w / 2.0          # feet anchor pixel inside a cell
    anchor_y = max_top + PAD
    AW, AH = cell_w * COLS, cell_h * ROWS
    print(f"\ncell={cell_w}x{cell_h} anchor_in_cell=({anchor_x:.1f},{anchor_y:.1f}) atlas={AW}x{AH}")
    print(f"feet uv in cell = ({anchor_x / cell_w:.6f},{1 - anchor_y / cell_h:.6f})")

    atlas = Image.new("RGBA", (AW, AH), (0, 0, 0, 0))
    cells = {}
    for idx, k in enumerate(CELL_KEYS):
        col, row = idx % COLS, idx // COLS
        cx0, cy0 = col * cell_w, row * cell_h
        info = infos[k]
        off_x, off_y = place_anchored(atlas, info["image"], info, (cx0 + anchor_x, cy0 + anchor_y))
        x0, y0, x1, y1 = info["bbox"]
        cells[k] = dict(
            index=idx, col=col, row=row,
            rect_px=[cx0, cy0, cx0 + cell_w, cy0 + cell_h],
            feet_px_in_cell=[info["feet_anchor"][0] + off_x - cx0, info["feet_anchor"][1] + off_y - cy0],
            head_px_in_cell=[info["head_anchor"][0] + off_x - cx0, info["head_anchor"][1] + off_y - cy0],
            face_px_in_cell=[info["face_anchor"][0] + off_x - cx0, info["face_anchor"][1] + off_y - cy0],
            content_bbox_in_cell=[x0 + off_x - cx0, y0 + off_y - cy0, x1 + off_x - cx0, y1 + off_y - cy0],
            content_w_px=info["content_size"][0],
            content_h_px=info["content_size"][1],
            face_ok=info["face_ok"],
        )
    # global colour bleed: fills cell padding + gutters with art colour (alpha stays 0),
    # so bilinear taps and mip levels never sample the black canvas.
    atlas = bleed_rgb(atlas, BLEED, (0, 0, AW - 1, AH - 1))
    atlas.save(os.path.join(OUT, "expr_atlas.png"), optimize=True)

    # ---------------------------------------------------------------- standalone maid card
    mw, mh = infos[MAID]["content_size"]
    maid_cell_w, maid_cell_h = mw + 2 * PAD, mh + 2 * PAD
    maid_atlas = Image.new("RGBA", (maid_cell_w, maid_cell_h), (0, 0, 0, 0))
    m_off_x, m_off_y = place_anchored(
        maid_atlas, maid_img, infos[MAID],
        (PAD + (infos[MAID]["feet_anchor"][0] - infos[MAID]["bbox"][0]),
         PAD + (infos[MAID]["feet_anchor"][1] - infos[MAID]["bbox"][1])))
    maid_atlas.save(os.path.join(OUT, "maid_card.png"), optimize=True)
    maid_ax = infos[MAID]["feet_anchor"][0] + m_off_x
    maid_ay = infos[MAID]["feet_anchor"][1] + m_off_y

    # ---------------------------------------------------------------- mapping math
    # card mesh: local x in [-anchor_x*s, (cell_w-anchor_x)*s], z in [-(cell_h-anchor_y)*s, anchor_y*s]
    # => feet at local (0,0); mesh uv (0,0) = cell bottom-left, (1,1) = cell top-right.
    # s = m/px of the artwork (height / HEIGHT_REF_PX), so card height = cell_h * s.
    feet_uv_mesh = [anchor_x / cell_w, (cell_h - anchor_y) / cell_h]
    mapping = {}
    for k in CELL_KEYS:
        c = cells[k]
        # px-per-metre reference: native scale for the 8 expressions, normalised for the
        # 1.2x-larger maid canvas (same body scale, denser pixels).
        scale_ref_px = HEIGHT_REF_PX if k != MAID else float(c["content_h_px"])
        # card is cell_h*(height/HEIGHT_REF_PX) metres tall; sampling sc_v of the atlas
        # displays AH*sc_v px over that height => m/px = card_h_m/(AH*sc_v) = height/ref_i
        #   => sc_v = (cell_h/AH) * (ref_i/HEIGHT_REF_PX)
        sc_v = (cell_h / AH) * (scale_ref_px / HEIGHT_REF_PX)
        sc_u = sc_v  # uniform grid => square texels
        u_anchor = (c["col"] * cell_w + anchor_x) / AW
        v_anchor = 1.0 - (c["row"] * cell_h + anchor_y) / AH
        loc_u = u_anchor - sc_u * feet_uv_mesh[0]
        loc_v = v_anchor - sc_v * feet_uv_mesh[1]
        mapping[k] = dict(scale=[round(sc_u, 8), round(sc_v, 8)],
                          location=[round(loc_u, 8), round(loc_v, 8)],
                          anchor_uv=[round(u_anchor, 8), round(v_anchor, 8)],
                          scale_ref_px=round(scale_ref_px, 3))

    # ---------------------------------------------------------------- JSON
    def uv(px, py, w, h):
        return [round(px / w, 6), round(1.0 - py / h, 6)]

    atlas_json = {
        "generated_by": "mv/assets/char/make_atlas.py",
        "purpose": "2.5D paper-doll texture atlas. Official illustration only - no Blender modelling.",
        "license": "source art CC BY-NC-SA 4.0 (see mv/ref/art/galgame/NOTICE.md); this atlas is an adaptation under the same license",
        "image": {"file": "expr_atlas.png", "width": AW, "height": AH, "mode": "RGBA", "colorspace": "sRGB"},
        "grid": {"cols": COLS, "rows": ROWS, "cell_w": cell_w, "cell_h": cell_h, "padding_px": PAD},
        "height_ref_px": HEIGHT_REF_PX,
        "anchor_convention": {
            "aligned_on": "feet anchor = bottom-centre of the alpha bbox (alpha > 0.02); identical pixel in every cell",
            "cell_px_origin": "top-left of the cell",
            "uv_origin": "bottom-left (Blender UV): u = x/width, v = 1 - y/height",
            "note": "source canvases have different bottom padding (up to 46 px) and the maid canvas is "
                    "1.2x larger; cells are aligned on the feet anchor so expression cuts never shift the "
                    "ground contact point",
            "mesh_uv": "card mesh UV is plain 0..1; feet at mesh uv (%.6f, %.6f)"
                       % (feet_uv_mesh[0], feet_uv_mesh[1]),
        },
        "mapping": {
            "description": "Texture Coordinate.UV -> Mapping(scale, location) -> Image Texture(extension=CLIP). "
                           "scale/location are per expression (hard-cut them with CONSTANT interpolation).",
            "formula": "atlas_uv = mesh_uv * scale + location",
            "feet_uv_mesh": [round(feet_uv_mesh[0], 8), round(feet_uv_mesh[1], 8)],
            "per_expression": mapping,
        },
        "order": CELL_KEYS,
        "expressions": {},
        "extras": {},
    }
    for k in CELL_KEYS:
        c = cells[k]
        ax, ay = c["feet_px_in_cell"]
        hx, hy = c["head_px_in_cell"]
        fx, fy = c["face_px_in_cell"]
        entry = {
            "cell": [c["col"], c["row"]],
            "index": c["index"],
            "rect_px": c["rect_px"],
            "rect_uv": [round(c["rect_px"][0] / AW, 6), round(1 - c["rect_px"][3] / AH, 6),
                        round(c["rect_px"][2] / AW, 6), round(1 - c["rect_px"][1] / AH, 6)],
            "alpha_bbox_in_cell_px": c["content_bbox_in_cell"],
            "content_size_px": [c["content_w_px"], c["content_h_px"]],
            "feet_anchor_px_in_cell": [round(ax, 2), round(ay, 2)],
            "feet_anchor_px_atlas": [round(ax + c["rect_px"][0], 2),
                                     round(ay + c["rect_px"][1], 2)],
            "feet_anchor_uv": uv(ax + c["rect_px"][0], ay + c["rect_px"][1], AW, AH),
            "head_anchor_px_in_cell": [round(hx, 2), round(hy, 2)],
            "head_anchor_px_atlas": [round(hx + c["rect_px"][0], 2),
                                     round(hy + c["rect_px"][1], 2)],
            "head_anchor_uv": uv(hx + c["rect_px"][0], hy + c["rect_px"][1], AW, AH),
            "face_anchor_px_in_cell": [round(fx, 2), round(fy, 2)],
            "face_anchor_px_atlas": [round(fx + c["rect_px"][0], 2),
                                     round(fy + c["rect_px"][1], 2)],
            "face_anchor_uv": uv(fx + c["rect_px"][0], fy + c["rect_px"][1], AW, AH),
            "face_anchor_detected": bool(c["face_ok"]),
            "mapping": mapping[k],
            "source": infos[k]["source"],
        }
        if k in EXPRESSIONS:
            atlas_json["expressions"][k] = entry
        else:
            atlas_json["extras"][k] = entry
    with open(os.path.join(OUT, "expr_atlas.json"), "w", encoding="utf-8") as f:
        json.dump(atlas_json, f, ensure_ascii=False, indent=1)

    maid_json = {
        "generated_by": "mv/assets/char/make_atlas.py",
        "purpose": "the maid lift-skirt pose as a standalone single card (same art as atlas cell 9)",
        "license": "source art CC BY-NC-SA 4.0 (see mv/ref/art/galgame/NOTICE.md)",
        "image": {"file": "maid_card.png", "width": maid_cell_w, "height": maid_cell_h,
                  "mode": "RGBA", "colorspace": "sRGB"},
        "source": infos[MAID]["source"],
        "rect_px": [0, 0, maid_cell_w, maid_cell_h],
        "alpha_bbox_in_cell_px": [PAD, PAD, PAD + mw - 1, PAD + mh - 1],
        "content_size_px": [mw, mh],
        "feet_anchor_px_in_cell": [round(maid_ax, 2), round(maid_ay, 2)],
        "feet_anchor_uv": uv(maid_ax, maid_ay, maid_cell_w, maid_cell_h),
    }
    with open(os.path.join(OUT, "maid_card.json"), "w", encoding="utf-8") as f:
        json.dump(maid_json, f, ensure_ascii=False, indent=1)

    # ---------------------------------------------------------------- diagnostics
    dbg = atlas.copy()
    d = ImageDraw.Draw(dbg)
    for k in CELL_KEYS:
        c = cells[k]
        r = c["rect_px"]
        d.rectangle(r, outline=(255, 220, 130, 255), width=3)
        ax, ay = c["feet_px_in_cell"]
        ax += r[0]; ay += r[1]
        hx, hy = c["head_px_in_cell"]; hx += r[0]; hy += r[1]
        fx, fy = c["face_px_in_cell"]; fx += r[0]; fy += r[1]
        d.line([(ax - 30, ay), (ax + 30, ay)], fill=(255, 60, 60, 255), width=5)
        d.line([(ax, ay - 30), (ax, ay + 30)], fill=(255, 60, 60, 255), width=5)
        d.line([(hx - 18, hy), (hx + 18, hy)], fill=(80, 200, 255, 255), width=3)
        d.line([(hx, hy - 18), (hx, hy + 18)], fill=(80, 200, 255, 255), width=3)
        d.line([(fx - 14, fy), (fx + 14, fy)], fill=(120, 255, 140, 255), width=3)
        d.line([(fx, fy - 14), (fx, fy + 14)], fill=(120, 255, 140, 255), width=3)
        d.text((r[0] + 10, r[1] + 10), f"{k}", fill=(255, 255, 255, 255))
    bg = Image.new("RGBA", dbg.size, (14, 20, 28, 255))
    bg.alpha_composite(dbg)
    bg.convert("RGB").resize((dbg.width // 5, dbg.height // 5), Image.LANCZOS).save(
        os.path.join(DIAG, "F_atlas_debug.png"))

    print(f"\nwrote expr_atlas.png {AW}x{AH}  maid_card.png {maid_cell_w}x{maid_cell_h}")
    for k in CELL_KEYS:
        m = mapping[k]
        print(f"  {k:12s} cell={cells[k]['col']},{cells[k]['row']} scale={m['scale']} loc={m['location']}")


if __name__ == "__main__":
    main()
