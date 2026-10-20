"""specimen_preview.py -- build + render validation sheets for specimens.py.

Run (headless, single session so EEVEE shader compile is paid once):

    blender -b -P mv/build/specimen_preview.py -- --stage all

Stages
    smoke      build every builder, print measurement JSON, 1 tiny render
    specimens  per-specimen front / side / 45deg contact sheet (2560x1440)
    kites      koinobori lineup (2560x1440)
    props      bucket / tomato / index-sheet contact sheets
    hall       hall_test.png: 3 specimens + spotlights + volumetric fog
    all        everything above

Artifacts land in mv/out/tests/specimens/ (PNG) plus measurements.json.
"""

import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Euler, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))          # workspace root
OUT = os.path.join(ROOT, "mv", "out", "tests", "specimens")
sys.path.insert(0, HERE)

import specimens as SP  # noqa: E402

RES = (2560, 1440)
PANEL_W = 853          # 853 * 3 = 2559 (1 px trimmed)
SAMPLES_SHEET = 24
SAMPLES_HALL = 48

C = {
    "water": (0.020, 0.062, 0.085, 1.0),   # linear-ish deep teal
    "floor": (0.012, 0.020, 0.026, 1.0),
    "spot": (1.0, 0.72, 0.42, 1.0),
    "scan": (0.12, 0.62, 1.0, 1.0),
    "fill": (0.16, 0.42, 0.62, 1.0),
}


# ---------------------------------------------------------------------------
# scene bootstrap
# ---------------------------------------------------------------------------

def reset_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for coll in list(bpy.data.collections):
        if coll.users == 0:
            bpy.data.collections.remove(coll)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.fps = 60
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.film_transparent = False
    scene.eevee.taa_render_samples = SAMPLES_SHEET
    scene.view_settings.view_transform = "AgX"
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    scene.view_settings.exposure = 0.0
    # world: dark water + volume fog
    world = bpy.data.worlds.new("W_museum")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = C["water"]
    bg.inputs["Strength"].default_value = 0.32
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    vol = nt.nodes.new("ShaderNodeVolumeScatter")
    vol.inputs["Color"].default_value = (0.42, 0.68, 0.82, 1.0)
    vol.inputs["Density"].default_value = 0.0085
    vol.inputs["Anisotropy"].default_value = 0.35
    nt.links.new(vol.outputs["Volume"], out.inputs["Volume"])
    # compositor: soft fog-glow bloom
    scene.use_nodes = True
    ct = scene.node_tree
    ct.nodes.clear()
    rl = ct.nodes.new("CompositorNodeRLayers")
    glare = ct.nodes.new("CompositorNodeGlare")
    for attr, val in (("glare_type", "FOG_GLOW"), ("quality", "HIGH"),
                      ("threshold", 1.05), ("size", 7), ("mix", 0.0)):
        try:
            setattr(glare, attr, val)
        except Exception as exc:
            print(f"[preview] glare.{attr}: {exc}")
    comp = ct.nodes.new("CompositorNodeComposite")
    ct.links.new(rl.outputs["Image"], glare.inputs["Image"])
    ct.links.new(glare.outputs["Image"], comp.inputs["Image"])
    make_floor()
    make_camera()
    make_lights()
    return scene


def make_floor():
    bpy.ops.mesh.primitive_plane_add(size=80.0, location=(0, 0, 0))
    floor = bpy.context.object
    floor.name = "floor"
    mat = bpy.data.materials.new("MAT_floor")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = C["floor"]
    bsdf.inputs["Roughness"].default_value = 0.42
    bsdf.inputs["Specular IOR Level"].default_value = 0.35
    floor.data.materials.append(mat)
    return floor


def make_camera():
    cam_data = bpy.data.cameras.new("cam")
    cam_data.lens = 55.0
    cam_data.sensor_width = 36.0
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    return cam


def _aim(obj, loc, target):
    obj.location = Vector(loc)
    d = Vector(target) - Vector(loc)
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def _area(name, loc, target, power, color, size=2.4, shape="SQUARE"):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = power
    data.color = color[:3]
    data.size = size
    data.shape = shape
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    _aim(obj, loc, target)
    return obj


def _spot(name, loc, target, power, color, size_deg=42.0, blend=0.55,
          radius=0.12):
    data = bpy.data.lights.new(name, "SPOT")
    data.energy = power
    data.color = color[:3]
    data.spot_size = math.radians(size_deg)
    data.spot_blend = blend
    data.shadow_soft_size = radius
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    _aim(obj, loc, target)
    return obj


def make_lights():
    """Museum closeup lighting rig, aimed at origin at z=0.9."""
    tgt = (0.0, 0.0, 0.85)
    _spot("key", (-2.0, -2.6, 3.9), tgt, 1300.0, C["spot"], 44.0, 0.62, 0.22)
    _area("fill", (2.9, -2.0, 1.5), tgt, 80.0, C["fill"], 3.2)
    _area("rim", (0.6, 2.8, 2.5), (0.0, 0.0, 1.15), 200.0, C["scan"], 2.2)
    _area("top", (0.0, 0.2, 5.2), tgt, 65.0, (0.72, 0.86, 1.0, 1.0), 4.0)


# ---------------------------------------------------------------------------
# rendering helpers
# ---------------------------------------------------------------------------

def set_res(w, h, samples):
    scene = bpy.context.scene
    scene.render.resolution_x = w
    scene.render.resolution_y = h
    scene.eevee.taa_render_samples = samples


def render_to(path):
    scene = bpy.context.scene
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print(f"[preview] wrote {path}")
    return path


def shot_views(prefix, cam, center, dist, views=None, samples=SAMPLES_SHEET,
               lens=55.0):
    """Render front / side / 45 contact panels."""
    views = views or [("front", 0.0), ("side", 90.0), ("q45", 45.0)]
    cam.data.lens = lens
    paths = []
    for name, az in views:
        a = math.radians(az)
        elev = math.radians(7.0)
        loc = (center[0] + math.sin(a) * dist * math.cos(elev),
               center[1] - math.cos(a) * dist * math.cos(elev),
               center[2] + math.sin(elev) * dist)
        _aim(cam, loc, center)
        set_res(PANEL_W, RES[1], samples)
        paths.append(render_to(os.path.join(OUT, f"{prefix}_{name}.png")))
    return paths


def _load_rgb(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    buf = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(buf)
    bpy.data.images.remove(img)
    return buf.reshape(h, w, 4)


def stitch(paths, out_path, gap=2):
    panels = [_load_rgb(p) for p in paths]
    h = max(p.shape[0] for p in panels)
    total_w = sum(p.shape[1] for p in panels) + gap * (len(panels) - 1)
    canvas = np.zeros((h, total_w, 4), dtype=np.float32)
    canvas[..., 3] = 1.0
    x = 0
    for p in panels:
        canvas[:p.shape[0], x:x + p.shape[1], :] = p
        x += p.shape[1] + gap
    out = bpy.data.images.new("stitch", width=total_w, height=h, alpha=False)
    out.pixels.foreach_set(canvas.reshape(-1))
    out.filepath_raw = out_path
    out.file_format = "PNG"
    out.save()
    bpy.data.images.remove(out)
    print(f"[preview] stitched {out_path}")
    return out_path


def stitch_grid(paths, cols, out_path, gap=2):
    """Stitch panels into a grid (rows top-down, left-to-right)."""
    panels = [_load_rgb(p) for p in paths]
    rows = (len(panels) + cols - 1) // cols
    cw = max(p.shape[1] for p in panels)
    ch = max(p.shape[0] for p in panels)
    total_w = cols * cw + gap * (cols - 1)
    total_h = rows * ch + gap * (rows - 1)
    canvas = np.zeros((total_h, total_w, 4), dtype=np.float32)
    canvas[..., 3] = 1.0
    for idx, p in enumerate(panels):
        r, c = divmod(idx, cols)
        # numpy row 0 is the bottom row in Blender image space
        y = (rows - 1 - r) * (ch + gap)
        x = c * (cw + gap)
        canvas[y:y + p.shape[0], x:x + p.shape[1], :] = p
    out = bpy.data.images.new("stitchg", width=total_w, height=total_h,
                              alpha=False)
    out.pixels.foreach_set(canvas.reshape(-1))
    out.filepath_raw = out_path
    out.file_format = "PNG"
    out.save()
    bpy.data.images.remove(out)
    print(f"[preview] stitched grid {out_path}")
    return out_path


def bbox_of(coll, skip_label=True):
    bpy.context.view_layer.update()
    mins = Vector((1e18, 1e18, 1e18))
    maxs = Vector((-1e18, -1e18, -1e18))
    for o in coll.all_objects:
        if o.type not in {"MESH", "FONT", "CURVE"}:
            continue
        if skip_label and "_label" in o.name:
            continue
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            mins = Vector((min(mins.x, w.x), min(mins.y, w.y),
                           min(mins.z, w.z)))
            maxs = Vector((max(maxs.x, w.x), max(maxs.y, w.y),
                           max(maxs.z, w.z)))
    return mins, maxs


def _label_bbox(coll):
    """World bbox of the hanging label plate (None if the specimen has none)."""
    bpy.context.view_layer.update()
    mins = Vector((1e18, 1e18, 1e18))
    maxs = Vector((-1e18, -1e18, -1e18))
    found = False
    for o in coll.all_objects:
        if o.type != "MESH" or "_label" not in o.name:
            continue
        if "_label_plate" not in o.name and "_label_bar" not in o.name:
            continue
        found = True
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            mins = Vector((min(mins.x, w.x), min(mins.y, w.y),
                           min(mins.z, w.z)))
            maxs = Vector((max(maxs.x, w.x), max(maxs.y, w.y),
                           max(maxs.z, w.z)))
    return (mins, maxs) if found else None


def frame_distance(mins, maxs, lens=55.0, fill=1.22,
                   aspect=PANEL_W / RES[1]):
    """Distance that fits the box in a PORTRAIT panel.

    Blender sensor_fit AUTO maps the 36 mm sensor to the larger image
    dimension, so for a portrait panel the vertical FOV is 36/lens and the
    horizontal one is 36*aspect/lens.
    """
    dim = maxs - mins
    tan_v = 18.0 / lens
    tan_h = 18.0 * aspect / lens
    d_v = (0.5 * dim.z) / tan_v
    d_h = (0.5 * max(dim.x, dim.y)) / tan_h
    return max(d_v, d_h) * fill


# ---------------------------------------------------------------------------
# per-stage rendering
# ---------------------------------------------------------------------------

SPECIMENS = [
    ("table", SP.build_table),
    ("eggplant", SP.build_eggplant),
    ("cat", SP.build_cat),
    ("steak", SP.build_steak),
    ("flower", SP.build_flower),
    ("human", SP.build_human),
]


def _drop_collection(coll):
    for o in list(coll.all_objects):
        data = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if data is not None and getattr(data, "users", 1) == 0:
            try:
                if isinstance(data, bpy.types.Mesh):
                    bpy.data.meshes.remove(data)
                elif isinstance(data, bpy.types.Curve):
                    bpy.data.curves.remove(data)
            except Exception:
                pass
    if coll.name in bpy.data.collections:
        bpy.data.collections.remove(coll)


def stage_specimens():
    scene = bpy.context.scene
    cam = scene.camera
    report = {}
    for name, builder in SPECIMENS:
        coll = builder()
        mins, maxs = bbox_of(coll)
        lab = _label_bbox(coll)
        if lab:
            # include the hanging label in the horizontal framing only
            mins.x = min(mins.x, lab[0].x)
            maxs.x = max(maxs.x, lab[1].x)
            mins.y = min(mins.y, lab[0].y)
            maxs.y = max(maxs.y, lab[1].y)
        dim = maxs - mins
        center = (0.5 * (mins.x + maxs.x), 0.5 * (mins.y + maxs.y),
                  mins.z + dim.z * 0.50)
        dist = frame_distance(mins, maxs, cam.data.lens, 1.14)
        paths = shot_views(name, cam, center, dist)
        stitch(paths, os.path.join(OUT, f"contact_{name}.png"))
        report[name] = {
            "measure": SP.measure(coll),
            "bbox_min": [round(v, 4) for v in mins],
            "bbox_max": [round(v, 4) for v in maxs],
            "dim": [round(v, 4) for v in dim],
            "coll_size": list(coll.get("size", [])),
        }
        _drop_collection(coll)
    with open(os.path.join(OUT, "measurements.json"), "w") as fh:
        json.dump(report, fh, indent=2)
    print("[preview] MEASURE " + json.dumps(report))
    return report


def stage_labels():
    """6 label closeups (3x2 grid, 853x720 panels -> 2560x1440)."""
    cam = bpy.context.scene.camera
    pw, ph = 853, 720
    paths = []
    for name, builder in SPECIMENS:
        coll = builder()
        bpy.context.view_layer.update()
        plate = bpy.data.objects.get(f"{name}_label_plate")
        frame = bpy.data.objects.get(f"{name}_label_frame")
        if plate is None or frame is None:
            print(f"[preview] no label for {name}")
            _drop_collection(coll)
            continue
        loc = frame.matrix_world.translation
        w = plate.dimensions.x
        lens = 85.0
        dist = (0.5 * w) / (18.0 / lens) * 1.16
        cam.data.lens = lens
        # label text faces +Y (film-camera side) since the 2026-10-19 label-face
        # fix in specimens._make_label, so the closeup camera must sit on +Y too.
        _aim(cam, (loc.x, loc.y + dist, loc.z + 0.10),
             (loc.x, loc.y, loc.z))
        set_res(pw, ph, SAMPLES_SHEET)
        paths.append(render_to(os.path.join(OUT, f"label_{name}.png")))
        _drop_collection(coll)
    stitch_grid(paths, 3, os.path.join(OUT, "labels_sheet.png"))
    return paths


def stage_props():
    scene = bpy.context.scene
    cam = scene.camera
    report = {}
    props = [
        ("bucket", lambda: SP.build_bucket(fill=0.55)),
        ("tomato", SP.build_tomato_paper),
        ("index", lambda: SP.build_index_sheet()),
    ]
    for name, builder in props:
        coll = builder()
        mins, maxs = bbox_of(coll)
        dim = maxs - mins
        center = (0.0, 0.0, mins.z + dim.z * 0.50)
        dist = frame_distance(mins, maxs, cam.data.lens, 1.30)
        paths = shot_views(f"prop_{name}", cam, center, dist)
        stitch(paths, os.path.join(OUT, f"contact_{name}.png"))
        report[name] = {"measure": SP.measure(coll),
                        "dim": [round(v, 4) for v in dim]}
        _drop_collection(coll)
    with open(os.path.join(OUT, "measurements_props.json"), "w") as fh:
        json.dump(report, fh, indent=2)
    print("[preview] PROPS " + json.dumps(report))
    return report


def stage_kites():
    scene = bpy.context.scene
    cam = scene.camera
    peers = ["kimi", "qwen", "mimo", "glm", "minimax", "hy4", "ernie",
             "step", "longcat", "merged"]
    files = {"kimi": "table_2", "qwen": "eggplant_3", "mimo": "cat_2",
             "glm": "steak_2", "minimax": "piece", "hy4": "dope",
             "ernie": "love", "step": "asked_again", "longcat": "her_again",
             "merged": "merged"}
    colls = []
    n = len(peers)
    span = 2.35
    for i, peer in enumerate(peers):
        row = i // 5
        col = i % 5
        x = (col - 2) * span + (0.5 * span if row else 0.0)
        z = 2.05 + row * 0.98 + 0.09 * math.sin(i * 1.1)
        y = 0.0 + row * 1.45
        yaw = math.radians(11.0 * math.sin(i * 1.7 + 0.6))
        roll = math.radians(5.5 * math.cos(i * 1.3))
        pitch = math.radians(4.0 * math.sin(i * 0.8))
        coll = SP.build_koinobori(
            color=SP.PEER_COLORS[peer],
            label_text=f"{peer}\n{files[peer]}",
            length=1.6,
            location=(x, y, z),
            rotation=(pitch, roll, yaw),
        )
        colls.append(coll)
    _spot("kite_spot", (0.0, -5.0, 8.0), (0.0, 0.6, 2.6), 2000.0,
          C["spot"], 62.0, 0.5, 0.4)
    _area("kite_key", (0.0, -7.5, 5.2), (0.0, 0.6, 2.6), 480.0,
          (0.80, 0.88, 1.0, 1.0), 8.0)
    _area("kite_fill", (-4.5, -5.0, 2.4), (0.0, 0.6, 2.5), 110.0, C["fill"], 6.0)
    _area("kite_rim", (0.0, 6.0, 4.6), (0.0, 0.0, 2.6), 420.0, C["scan"], 5.0)
    cam.data.lens = 42.0
    _aim(cam, (0.0, -15.5, 3.0), (0.0, 0.7, 2.55))
    set_res(*RES, SAMPLES_SHEET)
    render_to(os.path.join(OUT, "kites_lineup.png"))
    report = {c["label"]: {"measure": SP.measure(c), "size": list(c["size"])}
              for c in colls}
    with open(os.path.join(OUT, "measurements_kites.json"), "w") as fh:
        json.dump(report, fh, indent=2)
    for c in colls:
        _drop_collection(c)
    return report


def stage_hall():
    scene = bpy.context.scene
    cam = scene.camera
    # brighter fog for the hall shot (treatment density 0.012)
    world = scene.world
    for n in world.node_tree.nodes:
        if n.bl_idname == "ShaderNodeVolumeScatter":
            n.inputs["Density"].default_value = 0.012
    colls = [
        SP.build_table(location=(-2.15, 0.0, 0.0)),
        SP.build_cat(location=(0.0, 0.0, 0.0)),
        SP.build_human(location=(2.15, 0.0, 0.0)),
    ]
    # dedicated spot per specimen
    for i, x in enumerate((-2.15, 0.0, 2.15)):
        _spot(f"hall_spot{i}", (x, -2.6, 5.6), (x, 0.0, 0.95), 1700.0,
              C["spot"], 34.0, 0.55, 0.20)
    _area("hall_fill", (0.0, -6.0, 2.2), (0.0, 0.0, 1.0), 85.0, C["fill"], 6.0)
    _area("hall_rim", (-1.0, 5.0, 3.6), (0.0, 0.0, 1.1), 280.0, C["scan"], 4.0)
    cam.data.lens = 45.0
    _aim(cam, (2.70, -6.60, 2.45), (0.0, 0.10, 0.92))
    set_res(*RES, SAMPLES_HALL)
    render_to(os.path.join(OUT, "hall_test.png"))
    report = {c["specimen"]: {"measure": SP.measure(c)} for c in colls}
    with open(os.path.join(OUT, "measurements_hall.json"), "w") as fh:
        json.dump(report, fh, indent=2)
    return report


def stage_smoke():
    colls = []
    for name, builder in SPECIMENS:
        coll = builder()
        colls.append((name, coll))
    for name, builder in [("bucket", SP.build_bucket),
                          ("tomato", SP.build_tomato_paper),
                          ("index", SP.build_index_sheet),
                          ("kite", lambda: SP.build_koinobori("kimi", "kimi / table_2"))]:
        colls.append((name, builder()))
    report = {}
    for name, coll in colls:
        mins, maxs = bbox_of(coll)
        report[name] = {
            "measure": SP.measure(coll),
            "bbox_min": [round(v, 4) for v in mins],
            "bbox_max": [round(v, 4) for v in maxs],
        }
    # a couple of animated samples
    kite = dict(colls)["kite"]
    anim = SP.animate_flutter(kite, amp=0.05, speed=0.5, cycles=2)
    spec = dict(colls)["table"]
    ring = SP.animate_scan(spec, period=3.0, frame_end=60)
    report["_anim"] = {"flutter": anim, "scan_ring": ring.name}
    print("[preview] SMOKE " + json.dumps(report))
    with open(os.path.join(OUT, "measurements_smoke.json"), "w") as fh:
        json.dump(report, fh, indent=2)
    # tiny render of everything stacked in a row
    for i, (name, coll) in enumerate(colls):
        root = SP.root_of(coll)
        if root:
            root.location.x = (i - (len(colls) - 1) * 0.5) * 1.9
    cam = bpy.context.scene.camera
    cam.data.lens = 32.0
    _aim(cam, (0.0, -13.5, 3.0), (0.0, 0.0, 1.0))
    set_res(1280, 720, 16)
    render_to(os.path.join(OUT, "_smoke_all.png"))
    return report


# ---------------------------------------------------------------------------

STAGES = {"smoke", "specimens", "labels", "props", "kites", "hall", "all"}


def main():
    argv = sys.argv
    stage = "all"
    if "--" in argv:
        rest = argv[argv.index("--") + 1:]
        tokens = []
        for tok in rest:
            tokens.extend(tok.replace("--", " ").split())
        for tok in tokens:
            if tok in STAGES:
                stage = tok
    os.makedirs(OUT, exist_ok=True)
    reset_scene()
    print(f"[preview] stage={stage} out={OUT} argv={argv}")
    if stage in ("smoke",):
        stage_smoke()
        return
    if stage in ("specimens", "all"):
        stage_specimens()
    if stage in ("labels", "all"):
        stage_labels()
    if stage in ("props", "all"):
        stage_props()
    if stage in ("kites", "all"):
        stage_kites()
    if stage in ("hall", "all"):
        stage_hall()
    print("[preview] done")


if __name__ == "__main__":
    main()
