# SPECIMEN NOTES — `mv/build/specimens.py`

Interface notes for the museum-specimen / koinobori pipeline. Companion to
`mv/docs/SPECIMEN_INTERFACE.md` (long-form); this file is the short, practical
reference: builder contracts, the scan-layer anatomy, the style dict, the
animation helpers, and exactly how `shot_s05 / s07 / s08` use them.

Author: specimen-lab · Blender 4.5.3 LTS / EEVEE-Next · all units in metres.

---

## 1. Quick import

```python
import sys, os
sys.path.insert(0, os.path.join(WORKSPACE, "mv", "build"))
import specimens as SP

coll = SP.build_table(location=(-3.15, -13.60, -6.0),
                      rotation=(0.0, 0.0, math.radians(-9.0)),
                      style=dict(wire_strength=1.45))
SP.animate_scan(coll, period=3.4, frame_start=1, frame_end=1638)
```

No dependency outside `bpy / bmesh / mathutils` + Python stdlib. Import is
side-effect free (no scene objects created until a builder runs). The module
never changes render settings, world, camera or lights — those belong to the
shot module (`shotkit.begin`) or the preview harness.

---

## 2. Builder contract (identical for every builder)

```python
build_*(location=None, rotation=None, scale=None, style=None,
        collection=None, link=True, **kw) -> bpy.types.Collection
```

| argument | meaning |
|---|---|
| `location` | 3-tuple, where the **base of the plinth** sits (`z` = floor). Root Empty `SPEC_<kind>` is created here. |
| `rotation` | 3-tuple in **radians**, applied to the root (objects stay in the collection's local space). |
| `scale` | float (or 3-tuple) applied to the root. Total height = `scale * style["height"]`. |
| `style` | partial dict merged over `DEFAULT_STYLE` — the tuning surface (see §4). |
| `collection` | existing collection to link into; `None` → the current scene's active collection. |
| `link` | `False` skips scene linking (headless building, then `_finish_collection`). |
| `**kw` | extra style overrides, e.g. `build_human(..., pose="sit")`, `build_bucket(..., fill=0.6)`. |

Every builder returns a **Collection** whose root Empty carries the transform.
Content is centred at the origin in XY, sits with its base at `z = 0`, and is
normalised so the *scan* is `style["height"]` tall (default 1.0). The scan
floats `plinth_gap` above a paper plinth of height `plinth_h`; therefore the
whole assembly is `plinth_h + plinth_gap + height ≈ 1.50 m` tall. With
`style=dict(plinth=False)` the scan itself starts at `z = 0` and is exactly
`height` tall (no plinth, no halo).

### Builders

| builder | subject | tris (evaluated) | points | scan footprint (m) |
|---|---|---|---|---|
| `build_table` | wooden table, 4 legs + apron | **4 783** | 380 | 1.41 × 0.83 |
| `build_eggplant` | aubergine + calyx + stem | **4 701** | 380 | 0.57 × 0.56 |
| `build_cat` | sitting cat, curled tail | **4 558** | 380 | 0.60 × 0.68 |
| `build_steak` | leaning steak slab + fat cap + char | **4 932** | 300 | 1.51 × 0.73 |
| `build_flower` | stem, 2 leaves, 15 petals, centre | **4 864** | 380 | 0.52 × 0.58 |
| `build_human` | light figure (`pose="stand"` / `"sit"`) | **4 888 / 4 862** | 380 | 0.30 × 0.21 |
| `build_koinobori` | paper carp kite, bands + printed text | 2 906 | — | 1.33 × 0.57 × 0.57 |
| `build_bucket` | paper bucket, `fill=0..1` glowing scraps | 848 | — | 0.81 dia |
| `build_tomato_paper` | pleated paper tomato + sepals + stem | 630 | — | 1.02 × 0.98 |
| `build_index_sheet` | suspended typed index sheet (one-shot prop) | 9 505 | — | 0.74 × 1.40 |

Notes:
* Tri counts are *evaluated* (depsgraph) and include the live wireframe
  modifier, the point cloud, plinth, halo and label. Only `build_index_sheet`
  exceeds 5 k (14 rows of Consolas type; it is a one-shot hero prop in s02).
* `build_steak` was trimmed to 300 points to stay under 5 k (5000 budget).
* `build_koinobori(color, label_text, length=1.4, …)` — first argument is the
  paper colour: either a `PEER_COLORS` key (`"kimi"`), a hex string
  (`"#ffcf7a"`), or `None` (= warm `merged` paper). `label_text` accepts
  `"kimi / table_2"` or `"kimi\ntable_2"`; the model name is printed on the
  flank in Georgia and the file name in Consolas. `length` scales the body.
* `build_bucket(..., fill=0.55)` adds a glowing paper-scrap fill disc.
* `build_index_sheet(text=..., height=1.0, width_ratio=0.74, hang=True)`.

---

## 3. Scan-layer anatomy (what one specimen collection contains)

Every part of the subject is built once as a base mesh, then copied into three
render layers. Object names are `<specimen>_<part>_<layer>`:

| object | material | purpose |
|---|---|---|
| `<part>_shell` | `MAT_shell_*` (BLENDED, fresnel alpha ≈ 5 %) | extremely faint volumetric read; `visible_shadow = False` |
| `<part>_wire` | `MAT_wire_*` (emissive) | **live** Wireframe modifier named `SCAN_WIRE` (`wire_thickness`, `wire_strength`) — retunable in-scene, no re-bake |
| `<part>_points` | `MAT_point_*` (emissive micro-triangles) | sparse point cloud, `point_count` area-weighted, deterministic seed (`crc32(name)^seed*7919`) |
| `<specimen>_plinth`, `_cap`, `_gap` | paper | tapered paper plinth + overhanging top board + shadow gap |
| `<specimen>_halo` | emission ramp (BLENDED) | soft cyan pad on the plinth top |
| `<specimen>_label` (empty) | — | rig: `_plate` paper card, `_rule`, `_bar` (cyan scan bar), `_name` (Georgia), `_data0..n` (Consolas), `_label_wire0..1` |

The **label faces −Y** (toward the default camera), hangs at
`x = size.x/2 + 0.30`, `z = base + 0.44 * height`, tilted +10° about X.
`style["label_side"] = "left"` mirrors it to −X (use it when the specimen sits
near the right/left frame edge, as in s05/s07).

Collection custom properties (readable from any shot module):

```python
coll["specimen"]     # "table", "cat", ...
coll["kind"]         # "specimen" | "prop"
coll["root"]         # root Empty object
coll["height"]       # scan height (m)
coll["size"]         # [width, depth, height] of the scan
coll["tris_base"] / coll["tris_wire"] / coll["tris_total"]
coll["points"]       # number of point-cloud points
coll["scan_color"]   # hex
coll["style_json"]   # resolved style dict
```

Helpers: `SP.root_of(coll)`, `SP.measure(coll)` → dict of evaluated tri counts
and bbox (used to produce the table above).

---

## 4. Style dict (the whole tuning surface)

`DEFAULT_STYLE` = every key; pass only the deltas.

```python
height        1.0      # scan height in metres
fit           "height" # "height" | "max" | "width" normalisation
plinth        True     # False = bare hologram, base at z=0
plinth_h      0.40     # paper plinth height
plinth_gap    0.10     # scan float above plinth top
label         True
label_side    "right"  # "right" | "left"
label_lines   None     # [NAME, data1, data2, ...]; Georgia + Consolas
points        True
point_count   380      # 300–800 recommended
point_size    0.0032
shell         True
shell_alpha   0.05
wire          True
wire_ratio    0.40     # decimate ratio before the wireframe modifier
wire_thickness 0.0032
wire_strength 1.7      # emission strength of the wire lines
point_strength 2.8
scan_color    "#38c9ff"
paper_color   "#ece8de"
halo          True
seed          0
mount         None     # None | "wedge" (leaning-slab paper support)
triangulate   True
```

`SPECIMEN_STYLES[key]` holds the per-subject defaults (scan colour, label lines,
plinth height): TABLE `#aee4ff` · EGGPLANT `#b98cff` · CAT `#8fe0ff` ·
STEAK `#ffb066` · FLOWER `#ff9a7a` · HUMAN `#ffd28a`. Label data lines are the
museum wall text: `sim 0.31   mass 0.00 kg` / `function: surface` (the
"mass 0.00 kg" is the joke — it is a scan, not the object).

`SP.set_scan_params(coll, wire_thickness=…, wire_strength=…, point_size=…,
point_strength=…)` changes the live layer settings after the fact (also writes
the SCAN_WIRE modifier keyframes when needed).

---

## 5. Animation helpers

```python
SP.animate_scan(coll, period=4.0, frame_start=1, frame_end=None, fps=None,
                color=None, radius_scale=1.02, z0=None) -> ring object
```
Creates a thin emissive ring **parented to the specimen root** and keyframed to
sweep up and down the scan over `period` seconds (fps defaults to the scene).
Ring radius = `max(0.30 * height, 0.52 * max(size.x, size.y)) * radius_scale`
— bigger than the plinth so the ring reads as a scan plane, not a hula hoop.
Emission 2.2, wire thickness 0.006 (deliberately subtle). Returns the ring.

```python
SP.animate_flutter(obj, amp=0.055, speed=0.55, phase=0.0, yaw=7.0,
                   pitch=4.0, roll=3.5, tail=1.0, cycles=3,
                   frame_start=1, frame_end=None, fps=None, key_step=3)
```
Float + tail-wave motion for koinobori / hanging sheets (shape keys `SWAY_A`,
`SWAY_B` + gentle root rotation). Returns `{"root", "body", "frames"}`.

---

## 6. `PEER_COLORS`

```
kimi    #ffcf7a     qwen    #6fa8ff     mimo    #ff9a6a
glm     #7fd8b0     minimax #b08cff     hy4     #ff7f9e
ernie   #5aa0e8     step    #bfe07a     longcat #ffbe6e
doubao  #8fc8ff     merged  #efe6d6
```

Muted print-ink tones (never neon); `merged` = warm unbleached paper (the
evolved self). Used by `build_koinobori` and by the s06 kite scene.

---

## 7. How `shot_s05 / s07 / s08` use specimens

All three shots live in the same cold archive hall, built once by
`shot_s05._build_hall()` and imported by the other two (`import shot_s05 as H`).
Specimens stand directly on the hall floor (`z = -6.0`, `FLOOR`), each with its
own plinth; a cold spot shaft over each one brightens on its beat. The character
is always `K.char_actor` (2.5D paper puppet). Placements via
`H._place(builder, (x, y), rotz=…, style=…, scale=…, shadow=…)`.

### s05 — 40.86–68.17 s, frames 1‥1638 · table then eggplant · stage 02 RECALL
```
tcoll = _place(build_table,    (-3.15, -13.90), rotz=-9.0,  style=dict(wire_strength=1.45))
ecoll = _place(build_eggplant, ( 2.85, -14.10), rotz=11.0,  style=dict(label_side='left'))
animate_scan(tcoll, period=3.4, frame_start=1,   frame_end=N)
animate_scan(ecoll, period=2.8, frame_start=880, frame_end=N)
```
* f1–880 table beat: scan ring sweeps the table; shaft ramps 700→3300 W and
  fades at ~f860. Her expressions: confused(1) → shy(330) → serious(620).
* f880–N eggplant beat: ring starts at 880, shaft kicks 3000 W at f1030 and
  3300 at f1450. Expressions exasperated(900) → cheerful(1200) → confused(1450).
* Camera: 28 → 30 → 38 → 44 mm across the hall, ending 50 mm on her face; her
  key is a warm 1750 W spot, the specimens are lit by their own cold shafts.

### s07 — 82.89–109.72 s, frames 1‥1610 · cat then steak · stage 03 ROUTE
```
ccoll = _place(build_cat,   (-3.05, -13.75), rotz=8.0,
               style=dict(label_lines=['CAT', 'sim 0.22   mass 0.00 kg', 'purr: 0']))
scoll = _place(build_steak, ( 2.65, -13.95), rotz=-12.0, style=dict(label_side='left'))
animate_scan(ccoll, period=3.0, frame_start=1)
animate_scan(scoll, period=2.6, frame_start=820)
```
* f1–820 cat beat: shaft 2800→3200 W then drops to 900. Expressions
  starry(1) → frightened(340) → confused(620).
* f820–N steak beat: shaft 900→3100→3400 W. Expressions starry(880, the
  "hungry" beat — there is **no `hungry` expression** in the atlas) →
  serious(1180) → cheerful(1420).
* Camera: 50 mm medium-close alternating specimen ↔ her face.

### s08 — 109.72–137.09 s, frames 1‥1642 · flower then human · stage 04 FORGET
```
fcoll = _place(build_flower, (-3.00, -13.50), rotz=6.0)
hcoll = _place(build_human,  ( 0.45, -13.00), rotz=-4.0, scale=1.6, shadow=False,
               style=dict(plinth=False, label_side='left'))
animate_scan(fcoll, period=3.2, frame_start=1)
animate_scan(hcoll, period=8.34, frame_start=900)   # ring crosses her hand at ~f1300
```
* The human is a **bare hologram** (`plinth=False`, `scale=1.6` → 1.6 m scan
  floating 12 cm over the floor on its own soft emission pad); it is the only
  specimen without a paper plinth — she is not an exhibit.
* Hologram stutter at the touch (f1300–1390): root scale keyframed
  `1.0 → 1.014 → 0.992 → 1.010 → 1.0` (a glitch: the scan cannot be held).
* Her choreography: shy(1) → cheerful(420) → shy(780) → exasperated(1080,
  1300 reaching) → frightened(1400, hand passes through) → shy(N).
* Camera: 35 mm wide → 40 → 50 mm on her → 45 mm two-shot at the touch, ending
  50 mm; her card's right edge (x ≈ 0.80 + 0.5·card_w) intersects the human
  scan volume while the scan ring sweeps through her paper.

---

## 8. Known limits / gotchas

1. **Camera must be on +Y** of a specimen, otherwise the hanging label shows
   its back (plate faces −Y). `label_side="left"` for specimens near a frame
   edge.
2. The **scan ring** is parented to the specimen root: keep the root un-scaled
   or animate the ring separately; `animate_scan` keys are shot-global frames
   (`frame_start/frame_end`), so pass the shot's local range.
3. **Wireframe modifier stays live** (`SCAN_WIRE`). If a shot needs a cheaper
   frame, lower `wire_thickness`/`wire_strength` rather than applying it; the
   decimate ratio is already baked into `<part>_wire` data.
4. `shell` is BLENDED with ~5 % alpha and `visible_shadow = False` — in very
   dense fog it disappears first. That is intentional (the wireframe carries
   the silhouette).
5. **Point cloud disappears at wide framings**: at 1440p a specimen occupying
   < ~15 % of frame height loses the points; either accept it (wireframe still
   reads) or `set_scan_params(coll, point_size=0.006)`.
6. `build_index_sheet` is 9.5 k tris (typed text). Fine as a single hero prop,
   not for duplication.
7. The **human hologram** in s08 is intentionally 1.6 m and plinthless; its
   label floats at plinth height — s08 frames the label out.
8. `#no hungry expression`: s07's steak beat uses `starry`.
9. No `maid` pose is used in the three hall shots: the atlas cell for `maid`
   renders with stray top-padding art (shared file `char_paper.py`, reported to
   Lead). Reaching is expressed with `exasperated` + card placement instead.
10. Materials assume EEVEE-Next; the emissive wire/point/ring materials are
    plain emission nodes and survive the shot's volumetric fog untouched.

---

## 9. Regenerating previews (optional)

`mv/build/specimen_preview.py` (single headless session, ~40 s):

```
blender_rt_headless --script_file "...\mv\build\specimen_preview.py" \
  --outdir "...\mv\out\tests\specimens" -- --all
```
Stages: `smoke | specimens | labels | props | kites | hall | all` →
`contact_<name>.png` (3-view contact sheets), `labels_sheet.png`,
`kites_lineup.png`, `props_sheet.png`, `hall_test.png`, `measurements.json`.

---

## 10. Poster (`mv/build/poster.py`, separate deliverable)

Key visual: a **paper-theatre keyframe of the whale girl** — she stands as a
paper cutout on the sunken stage, one hand raised on three marionette threads,
behind her a cool shoji window grid, a large glowing paper-whale silhouette
drifting in at the level of her raised hand, a small gold one upper-right,
typed index cards (`see_you.txt`, `first_hello.txt`, `laugh_0314.txt`) floating
like drifting memory files, blurred paper scraps falling through the light.
Two layouts in one module (`LAYOUTS`):

| layout | size | camera | notes |
|---|---|---|---|
| `landscape` | 2560 × 1440 | 50 mm, eye level, f/2.0 | hero crop, bust to frame bottom, title space at top |
| `portrait` | 1800 × 2700 | 50 mm, f/2.3, 4:6 | full figure, shoji read as a lit washi window in a dark wall, 2 cards only |

```
blender_rt_headless --script_file "...\mv\build\poster.py" --args "--w 960 --h 540 --samples 24 --out poster_v2_960x540.png"
blender_rt_headless --script_file "...\mv\build\poster.py" --args "--portrait --w 600 --h 900 --out poster_v2_portrait_600x900.png"
```

Relative `--out` names resolve into `mv/out/lookdev/`. Build ≈ 1.4 s
(83 objects); render ≈ 16–36 s at 960×540 / 24 spp while the GPU is contended.
The two approved previews are the look reference (`poster_v2_960x540.png`,
`poster_v2_portrait_600x900.png`); the **final 2560×1440 / 32 spp and
1800×2700 / 32 spp renders are executed by the Lead in the film's render queue
once it is idle** — do not launch extra Blender processes while the queue is
full (8 GB VRAM: one extra EEVEE process makes every film frame ~8× slower).

Implementation notes:
* character = `core.paper_cutout(mv/ref/art/galgame/whale-starry.webp)` — the
  standing rotation lives in the card's `rotation_euler` (90°, 0, 180°); add
  your yaw, never overwrite it.
* whale silhouettes = `mv/assets/whale_silhouette.png` as BLENDED alpha
  planes (`_glow` rewires emission colour, keeps the hue; lower the strength
  ~0.6–1.0 or AgX clips them to white).
* index cards are real paper planes (`core.paper`, ink text via `core.text_obj`,
  Consolas) facing the camera; text sits 8 mm in front of the plate.
* shoji = two warm emissive sheets + an ink mullion grid, per-layout
  `strength` / `cool` wash so the window reads lit, not backgroundless white.
* the stage comes from `world_theater.theatre(seed=3)` + `stage.lighting()`;
  two poster-only lights (warm face fill, cyan back kick) and 380 dust motes.

### 10.3 Final renders — exact commands (run from the project root)

Landscape 2560×1440 / 32 spp → `mv/out/lookdev/poster_2560x1440.png`:

```
blender_rt_headless --script_file "D:\Code\Code MV\new-word.search(you)\mv\build\poster.py" --args "--w 2560 --h 1440 --samples 32 --out poster_2560x1440.png"
```

Portrait 1800×2700 / 32 spp → `mv/out/lookdev/poster_1800x2700.png`
(`--portrait` defaults to 1800×2700 when `--w/--h` are omitted):

```
blender_rt_headless --script_file "D:\Code\Code MV\new-word.search(you)\mv\build\poster.py" --args "--portrait --w 1800 --h 2700 --samples 32 --out poster_1800x2700.png"
```

Equivalent plain-Blender form:

```
"D:\Blender Foundation\Blender 4.5\blender.exe" -b --factory-startup -P "D:\Code\Code MV\new-word.search(you)\mv\build\poster.py" -- --w 2560 --h 1440 --samples 32 --out poster_2560x1440.png
```

Only tokens **after the first `--`** are parsed; `--out` is a bare filename that
resolves into `mv/out/lookdev/` (the DSH `--args` line is split on spaces and the
project path contains spaces, so never pass an absolute `--out`).

Cost: build ≈ 1.4–1.8 s, plus ≈ 2–4 min landscape / ≈ 3–5 min portrait (7× / 9×
preview pixels, 24→32 spp) on an otherwise idle GPU. Run **after** the film queue
drains, never alongside it (8 GB VRAM).

#### Patched render setup (queue defaults) — poster impact

`poster.py` inherits the scene setup through `shotkit.begin()` → `core.setup_render()`,
so the queue patch (`use_raytracing=False`, `volumetric_tile_size=8`, trimmed light
shadow maps) applies automatically. Impact on the poster: **none visible** — there are
no reflective/glossy surfaces, raytraced reflections, AO dependence or screen-space
effects; shading is paper (Principled, roughness ≥ 0.86), emissive sheets and two
silhouette cards. `volumetric_tile_size 8` only makes the fog sampling coarser/cheaper
(slightly softer fog noise at 32 spp); trimmed shadow maps only soften the contact
shadows. If the tightest fog is wanted, set `scene.eevee.volumetric_tile_size = '4'`
in a one-line wrapper before `render()` — not needed for the key visual.
