# SPECIMEN_INTERFACE — museum scan specimens, koinobori & paper props

`mv/build/specimens.py` · Blender 4.5.3 LTS / EEVEE-Next · status: **production-ready**
(integrated into the official pipeline by the Lead; hall_test.png is the reference look).

Everything here is procedural, deterministic (no simulation, no external assets), and
built for 17 721 frames of EEVEE-Next at 2560×1440: a specimen is ~4.5–4.9 k evaluated
triangles and builds in 20–120 ms.

---

## 1. Quick start

```python
import sys, bpy
sys.path.insert(0, r"D:\Code\Code MV\new-word.search(you)\mv\build")
import specimens as SP

table = SP.build_table(location=(-2.15, 0, 0))
cat   = SP.build_cat(location=(0, 0, 0), rotation=(0, 0, 0.2))
human = SP.build_human(location=(2.15, 0, 0), pose="sit")

kimi = SP.build_koinobori(color="kimi", label_text="kimi\ntable_2",
                          length=1.6, location=(0, 6, 2.4),
                          rotation=(0, 0, 1.57))
SP.animate_flutter(kimi, amp=0.06, speed=0.5, phase=0.3)

ring = SP.animate_scan(cat, period=4.0)      # travelling scan ring
print(SP.measure(cat))                       # {'base':…, 'wire':…, 'points':…, 'total':…}
```

The module is import-safe: it only defines functions/constants at import time; materials
and fonts are created lazily on first use. Call it from a Blender Python context
(any engine, headless or GUI).

---

## 2. Common builder contract

Every builder has the same trailing signature:

```python
build_xxx(..., location=None, rotation=None, scale=None, style=None,
          collection=None, link=True, **style_overrides)
```

| arg | meaning |
|---|---|
| `location` | world XYZ of the specimen origin (base centre). Default `(0,0,0)`. |
| `rotation` | Euler XYZ radians (or quaternion/tuple). Applied to the root Empty. |
| `scale` | uniform float or XYZ — scales the whole assembly, **height is multiplied**. |
| `style` | dict merged over `DEFAULT_STYLE` (+ the per-specimen preset). |
| `collection` | existing `bpy.types.Collection` to receive the objects; default = a new collection named `SPEC_<name>` / `PROP_<name>`. |
| `link` | link the collection into the current scene collection (default `True`). |
| `**style_overrides` | shorthand: `build_cat(wire_thickness=0.004, plinth_h=0.5)`. |

**Return value: a `bpy.types.Collection`.** Layout contract:

* one root `EMPTY` (`SPEC_table`, `PROP_koinobori`, …) — all objects parented to it;
* the assembly is **centred on the origin in XY**, **base at z = 0**, **total height ≈ `style["height"]`** (default `1.0`, plinth included);
* the scan content floats `plinth_h + plinth_gap` above z=0 when `plinth=True`;
* `style["plinth"]=False` → bare hologram, base at z=0, height 1.0;
* collection custom properties (also mirrored on the root Empty where useful):

| prop | value |
|---|---|
| `specimen` / `kind` | `"table"` … / `"specimen"` or `"prop"` |
| `root` | name of the root Empty (`SP.root_of(coll)` resolves it) |
| `height` | intended height (before object scale) |
| `size` | `[x, y, z]` of the **scan content** (without plinth/label) |
| `tris_base` / `tris_wire` / `tris_total` | evaluated triangle counts at build time |
| `points` | number of point-cloud points |
| `scan_color` | hex string of the scan colour |
| `style_json` | the fully resolved style dict (reproducible) |

Object naming (used by `measure()` and by downstream compositing):

* `<name>_<part>_shell` — translucent fresnel shell (base mesh itself, renamed);
* `<name>_<part>_wire` — decimated copy + **live** `WIREFRAME` modifier named `SCAN_WIRE`
  (retune `modifier.thickness` later; do **not** apply it);
* `<name>_points` — sparse point cloud (2 crossed micro-triangles per point, one object);
* `<name>_plinth`, `_cap`, `_gap` — paper plinth / overhanging top board / shadow gap;
* `<name>_halo` — soft transparent glow pad on the plinth top;
* `<name>_label_plate` / `_rule` / `_bar` / `_name` / `_data0..n` — hanging label card;
* `<name>_label_wire0/1` — two suspension filaments.

All scan layers have `visible_shadow = False`; the shell is `surface_render_method =
"BLENDED"` with a fresnel alpha (≈4–6 %) so it stays correct inside the volumetric fog.

---

## 3. Builders

### 3.1 Specimens (shots s06–s12)

```python
build_table  (location=None, rotation=None, scale=None, style=None, collection=None, link=True, **kw)
build_eggplant(...)
build_cat    (...)
build_steak  (...)
build_flower (...)
build_human  (..., pose="stand", **kw)          # pose: "stand" | "sit"
```

`build_human(pose="sit")` is the s12 light-table pose (sitting on the edge, hands on knees);
`pose="stand"` is the s21 walking figure.

Per-specimen presets live in `SPECIMEN_STYLES` (scan colour, plinth height, label text,
wire thickness/strength, point count) — e.g. `SPECIMEN_STYLES["table"]["label_lines"]`.

### 3.2 Koinobori (s17 ring of model kites)

```python
build_koinobori(color=None, label_text="", length=1.4,
                location=None, rotation=None, scale=None, style=None,
                collection=None, link=True, name=None)
```

* `color` — hex string **or** a key of `PEER_COLORS` (`"kimi"`, `"qwen"`, `"mimo"`,
  `"glm"`, `"minimax"`, `"hy4"`, `"ernie"`, `"step"`, `"longcat"`, `"doubao"`,
  `"merged"`). Muted print-ink paper tones, never neon.
* `label_text` — `"kimi / table_2"`, `"kimi\ntable_2"` or `["kimi", "table_2"]`;
  printed on the flank (Georgia for the name, Consolas for the file).
* `length` — nose-to-tail length in metres (default 1.4); the kite is built along **+X**,
  mouth at −X, forked tail at +X, lowest point at z = 0.
* Shape keys `SWAY_A` / `SWAY_B` on the body — driven by `animate_flutter()`.
* Returns Collection, root `PROP_koinobori`; props `length`, `size`, `peer_color`, `label`.

```python
animate_flutter(obj, amp=0.055, speed=0.55, phase=0.0, yaw=7.0, pitch=4.0,
                roll=3.5, tail=1.0, cycles=3, frame_start=1, frame_end=None,
                fps=None, key_step=3)
```

`obj` = Collection or root Empty. Keys root location/rotation (float + yaw/pitch/roll
sway) and the tail shape keys; deterministic from `phase`. Returns
`{"root":…, "body":…, "frames":(start, end)}`. Use a different `phase` per kite
(`i * 0.7`) so a ring never beats in sync. Also works on `build_index_sheet()` sheets
(gentle paper sway).

### 3.3 Props

```python
build_bucket       (..., fill=0.0)                  # s17 paper bucket; fill 0..1 = glowing scraps
build_tomato_paper (...)                            # s21 paper tomato
build_index_sheet  (text=None, ..., height=1.0, width_ratio=0.74, hang=True)
```

`build_index_sheet` accepts a multi-line string or list of lines; scale it 2.5–3× in the
scene for the giant s02 sheet. `hang=True` adds two suspension wires.

### 3.4 Helpers

| helper | purpose |
|---|---|
| `root_of(coll)` | root Empty of a built collection |
| `measure(coll)` | `{'base','wire','points','other','total','objects'}` evaluated tri counts |
| `set_scan_params(coll, wire_thickness=None, wire_strength=None, point_size=None, shell_alpha=None)` | retune the hologram after the fact (far shots need thicker wire) |
| `animate_scan(coll, period=4.0, frame_start=1, frame_end=None, fps=None, color=None, radius_scale=1.15)` | travelling emissive scan ring, returns the ring object |
| `PEER_COLORS` / `PALETTE` / `SPECIMEN_STYLES` / `DEFAULT_STYLE` | art-direction constants |
| `FONT_GEORGIA` / `FONT_CONSOLAS` | font paths used for labels |

---

## 4. Style keys (`DEFAULT_STYLE`)

| key | default | note |
|---|---|---|
| `height` | `1.0` | total height incl. plinth |
| `fit` | `"height"` | `"height"` / `"max"` / `"width"` normalisation |
| `plinth` / `plinth_h` / `plinth_gap` | `True` / `0.40` / `0.10` | paper plinth + floating gap |
| `label` / `label_side` / `label_lines` | `True` / `"right"` / `None` | hanging card; `label_lines` = `[NAME, data…]` |
| `points` / `point_count` / `point_size` | `True` / `380` / `0.0032` | sparse cloud |
| `shell` / `shell_alpha` | `True` / `0.05` | fresnel shell |
| `wire` / `wire_ratio` / `wire_thickness` / `wire_strength` | `True` / `0.40` / `0.0032` / `1.7` | decimate ratio, then live wireframe |
| `point_strength` | `2.8` | emission of the points |
| `scan_color` | `PALETTE["scan"]` | cyan `#38c9ff` default |
| `paper_color` | `PALETTE["paper"]` | `#ece8de` |
| `halo` | `True` | glow pad under the scan |
| `seed` | `0` | deterministic jitter/sampling |
| `mount` | `None` | `"wedge"` = leaning slab support |
| `triangulate` | `True` | triangulate before the scan layers |

Style can be given as a dict **or** as keyword overrides; precedence:
`DEFAULT_STYLE` → `SPECIMEN_STYLES[name]` → `style=` → `**kw`.

---

## 5. Cost table (measured, `measure()`, evaluated tris)

| item | base | wire | points | other | **total** | points | scan size (m) |
|---|---|---|---|---|---|---|---|
| table | 1787 | 1960 | 760 | 276 | **4783** | 380 | 1.409 × 0.830 × 1.00 |
| eggplant | 1873 | 1792 | 760 | 276 | **4701** | 380 | 0.566 × 0.560 × 1.00 |
| cat | 1538 | 1984 | 760 | 276 | **4558** | 380 | 0.596 × 0.682 × 1.00 |
| steak | 1784 | 2272 | 600 | 276 | **4932** | 300 | 1.514 × 0.727 × 1.00 |
| flower | 1852 | 1976 | 760 | 276 | **4864** | 380 | 0.517 × 0.580 × 1.00 |
| human (stand) | 1724 | 2128 | 760 | 276 | **4888** | 380 | 0.303 × 0.208 × 1.00 |
| human (sit) | 1722 | 2104 | 760 | 276 | **4862** | 380 | 0.342 × 0.539 × 1.00 |
| koinobori (L=1.4) | 143 | — | — | 2763 | **2906** | — | 1.333 × 0.574 × 0.574 |
| bucket | — | — | — | 848 | **848** | — | 0.811 × 0.811 × 1.00 |
| tomato_paper | — | — | — | 630 | **630** | — | 1.015 × 0.976 × 1.00 |
| index_sheet (14 rows) | — | — | — | 9505 | **9505** | — | 0.741 × 0.161 × 1.40 |

* `base` = shell + label typography, `wire` = live wireframe, `points` = 2 tris/point,
  `other` = plinth / halo / label card / props.
* Build time per specimen ≈ 40–120 ms (headless, cold: remesh+decimate dominate).
* Koinobori cost scales with `length` only in point count, not tris (~2.9 k).

Budget rule of thumb: **each specimen stays under 5 000 evaluated tris**, point cloud
380 points (300–800 allowed), no simulation, no per-frame Python.

---

## 6. Rendering / integration notes

* Engine: **EEVEE-Next** (`BLENDER_EEVEE_NEXT`); Cycles is not used in this film.
* Materials are plain Principled/Emission mixes (no OSL, no volumetrics inside the
  materials) so they are unaffected by the scene volume fog; the shell is `BLENDED`
  with `use_transparent_shadow` on, the wire/points/shell have `visible_shadow=False`.
* Emissive strengths are tuned for AgX + Medium-High Contrast with world strength
  ≈ 0.32 and fog density 0.008–0.012. If the look-dev grade changes, retune with
  `set_scan_params()` rather than editing the module.
* The label card is printed on the **+Y face** (the camera side for every shot in
  this film: cameras sit at +Y and above, so the plate tilts +10° to face them) and
  hangs from two filaments; the name/data typography is rotated (π/2, 0, π) so it
  reads unmirrored from that side. It is offset to `+X` (`label_side="left"` flips
  it). Keep the card inside frame — it extends ~0.30 m beyond the specimen's right
  edge and ~0.44·h upward. (Before 2026-10-19 the text was on the −Y face, which
  rendered as a blank card back in all masters; fixed in `_make_label`.)
* Fonts are loaded from `C:\Windows\Fonts` (Georgia / Consolas). On a machine without
  them the label falls back to Blender's built-in font (still legible, different feel).
* All randomness is seeded (`zlib.crc32(name) ^ seed*7919`), so two runs produce
  byte-identical geometry — safe for re-renders of the 17 721-frame timeline.

---

## 7. Preview harness

`mv/build/specimen_preview.py` renders everything in one Blender session (one shader
compile ≈ 35 s, then ≈ 0.9 s per 2560×1440 frame):

```
blender_rt_headless(script_file="D:\Code\Code MV\new-word.search(you)\mv\build\specimen_preview.py",
                    outdir="D:\Code\Code MV\new-word.search(you)\mv\out\tests\specimens",
                    args="all")      # or: smoke | specimens | labels | props | kites | hall
```

Outputs in `mv/out/tests/specimens/`:

| file | content |
|---|---|
| `contact_<specimen>.png` | front / side / 45° contact sheet, 2563×1440 |
| `labels_sheet.png` | six label close-ups, 3×2 |
| `contact_bucket.png`, `contact_tomato.png`, `contact_index.png` | prop sheets |
| `kites_lineup.png` | 10-peer koinobori queue, 2560×1440 |
| `hall_test.png` | table + cat + human in the hall with spot lights and fog — **the integration reference** |
| `measurements*.json` | evaluated tri counts + bbox per build |

---

## 8. Known limits / notes for downstream

1. `index_sheet` is the only object above 5 k tris (9 505, dominated by 14 rows of real
   typewritten text). It is a one-shot prop; if a shot ever instances it many times,
   drop rows or use `text` with fewer lines.
2. `build_steak` uses 300 points (not 380) to stay under 5 k tris; its wire ratio is
   higher because the slab is a single dense surface.
3. The point cloud is 2 crossed triangles per point — it disappears below ~6 px; for
   wide shots use `set_scan_params(coll, point_size=0.006, wire_thickness=0.005)`.
4. `animate_scan` returns a ring that is *parented to the root*; if the root is moved
   after the call, keyframes stay relative — fine, but re-run if you re-parent.
5. The label typography is real text (FONT objects, converted to mesh for the props):
   at 2560×1440 it is crisp down to ~0.6 m camera distance; at 1440p the smallest data
   line is ~7 px tall — intended to be read as texture, not copy.
6. `PEER_COLORS` holds 11 names (10 peer models + `merged`); `doubao` is included even
   though it has no memory event, for crowd variety.
7. Nothing in this module touches `mv/data/`, `mv/overlay/`, `char_paper.py`, or the
   shot modules — it is a pure library.
