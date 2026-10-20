# SHOT MODULE CONTRACT (v1)

Everyone writing a shot module must follow this. The pipeline renders one module per process,
then I concat the mp4s in shot order.

## File layout

```
mv/build/shot_sNN.py      # one file per shot, exports FRAMES + build()
mv/build/shotkit.py       # shared helpers (do not edit)
mv/build/render_shot.py   # renderer (do not edit)
```

## Module template

```python
"""s05 - RECALL / hall: table + eggplant specimens under scan light."""
import bpy, math, os, sys
MV = r'D:\Code\Code MV\new-word.search(you)'
sys.path.insert(0, os.path.join(MV, 'mv', 'build'))
import shotkit as K
import core as C
import world_theater as T
import specimens as SP

FRAMES = (40.86, 68.17)          # global song seconds (from mv/data/shot_plan.json)

def build():
    K.begin(samples=12, fog_density=0.02, exposure=0.15)   # resets scene + render settings
    ...build set, lights, props, character...
    K.cam_path('cam_s05', [
        (1,   (x,y,z), (tx,ty,tz), lens, fstop),
        (N,   (x,y,z), (tx,ty,tz), lens, fstop),
    ])
```

Rules:
* Animation keys are LOCAL frame numbers, `1 .. N`, where
  `N = round(t1*60) - round(t0*60)` (the renderer computes it). Do not use global song frames.
* `build()` must be fully deterministic (seed your random).
* Scene units: metres, FLOOR = -6.0 is the stage floor, +Y is toward the camera side,
  character faces +Y by default. Camera looking toward -Y means world +X appears on the LEFT.
* Keep the render under ~1.0 s/frame at 1920x1080 / 10 samples on the 4060.
* Do not add hundreds of objects with `bpy.ops.mesh.primitive_*` in a loop — use
  `geo.Geo` (bmesh, one mesh) or `specimens` collections. More than ~60 objects slows sync.
* Do not touch other people's shot files. Only write `mv/build/shot_<your ids>.py`
  and your own test outputs under `mv/out/tests/<yourname>/`.

## Render / test commands

```bash
# single still at the film profile (1920x1080 / 10spp)
blender_rt_headless --script_file "D:\Code\Code MV\new-word.search(you)\mv\build\render_shot.py" \
  --args "--shot s05 --still 1"
```

Outputs: still -> `mv/out/lookdev/s05.png`.
Final 1080p mp4 (I run this): `--shot s05` -> `mv/out/shots/s05.mp4`.

## Shared API cheat sheet

### shotkit as K
* `K.begin(fog_density=0.02, fog_color=(...), ambient=(...), exposure=0.15)`
  — reset scene, EEVEE Next, AgX, glare bloom, volume fog (10 samples).
* `K.FRAMES / K.FPS / K.FLOOR / K.W / K.H / K.OUT / K.DATA`
* `K.cam_path(name, [(frame, loc, target, lens, fstop), ...], dof=True)` — animated camera
  (bezier), sets scene camera.
* `K.char_actor(expr, loc, height=1.75, face=(x,y,z), **opts)` -> ctrl  (2.5D paper character,
  faces the point `face`; opts: bend, edge_mm, glow, split_head)
* `K.char_expr(ctrl, [(frame, 'starry'), (frame, 'serious', bend_deg, lateral_deg)])`
  expressions: cheerful angry confused exasperated frightened serious shy starry
* `K.char_pose(ctrl, [(frame, loc, (bend, lateral), scale)])`
* `K.face_plus_y(ob)` — make a text/card face +Y and read correctly (use for ALL text).
* `K.rise(ob, f0, f1, dz, start_scale, end_scale)`, `K.drift(ob, f0, f1, dloc, drot)`,
  `K.obj_keys(ob, [(f, val)], prop='location')`, `K.blink_scale(ob, f0, f1, ...)`
* `K.glow_orb(name, loc, r, color, strength)`, `K.sheet(...)`, `K.floor_slab(...)`,
  `K.water_slab(...)`, `K.save_blend(path)`, `K.render_mp4(...)` (renderer calls it)

### stage as S (paper theatre, warm)
* `S.build_stage(char='cheerful', window_strength=1.05)` — full theatre set + character
  (character is a simple cutout; prefer K.char_actor for expression control)
* `S.foreground_papers(seed, n)` — out-of-focus paper scraps
* `S.lighting('default')` — warm key / cold rim / top shaft / window spill / desk pool + dust
* `S.cameras()` — named lookdev cameras

### world_theater as T (set pieces)
`T.theatre(seed=3)` builds stage floor, side curtains, backdrop wall + glowing shoji window,
distant archive silhouettes, top batten, hanging threads, audience railing, footlights,
paper lanterns, 4 plinths + hero plinth + terminal desk.
Also: `T.stage_floor`, `T.curtain_wing`, `T.paper_window`, `T.backdrop_wall`, `T.footlights`,
`T.top_batten`, `T.threads`, `T.paper_lanterns`, `T.audience_railing`, `T.distant_archive`,
`T.plinth(x, y, z=FLOOR, h, w, d, gold, label)`, `T.terminal_desk(loc, rotz)`, `T._mats()`.

### core as C
`C.paper(name, base, rough, fiber)`, `C.emissive(name, color, strength)`, `C.glass(...)`,
`C.text_mat(name, color, strength)`, `C.fog_world(density, color, ambient)`,
`C.plane(name, size, loc, rot, mat)`, `C.box(name, dims, loc, rot, mat)`,
`C.text_obj(name, body, size, loc, rot, font, mat)`, `C.light(name, kind, loc, energy, color, size, target, angle)`,
`C.look_at(ob, target)`, `C.camera(...)`, `C.keyframe(ob, frame, loc, rot, scale)`,
`C.dust(name, count, extent, center, size, color, strength)`, `C.simple_world(bg, strength)`,
`C.paper_cutout(path, height, loc, name, emission_strength)`, `C.illustration_card(...)`.
Palette: `C.PALETTE` (ink/paper/her/warm/gold/cyan/abyss), `C.TEX` = mv/ref/art.

### specimens as SP (museum holograms)
`SP.build_table/eggplant/cat/steak/flower/human/koinobori/bucket/tomato_paper/index_sheet(
   location=None, rotation=None, scale=None, style=None, collection=None, link=True, **kw)`
-> Collection, root Empty, base z=0, height normalised to 1.0, includes paper plinth +
hanging label + scan layers. `SP.set_scan_params(coll, wire_thickness=..., wire_strength=...)`,
`SP.animate_flutter(obj, amp, speed, phase, yaw)`, `SP.animate_scan(coll, period, frame_start, frame_end, fps)`,
`SP.measure(coll)`, `SP.root_of(coll)`. PEER_COLORS for model-name kites.

### char_paper as CH (lower level, already wrapped by K.char_actor)
`CH.build_character(name, expr, height, location, split_head, **opts)` -> ctrl dict with
`set_expression / set_bend / set_edge_glow / set_flash / set_fog / set_backface / anchor`.
Art faces -Y by default; `K.char_actor` handles the yaw.

## Deliverables per shot
1. `mv/build/shot_sNN.py` that renders cleanly.
2. One still PNG per ~20% of the shot length, sent in your report message as paths.
3. Report: build time, per-frame render time at 1080p / 10spp, any TODO.
