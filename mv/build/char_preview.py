"""char_preview.py - preview renders for the paper-doll character (char_paper.py).

Foggy sunken paper archive look from TREATMENT 2.1: dark teal volumetric fog, warm coral
key light, cyan rim/back light, gold specimen spot, paper-toned floor.

Usage (headless):
    blender -b --factory-startup -P mv/build/char_preview.py -- --mode quick
    blender -b --factory-startup -P mv/build/char_preview.py -- --mode stills
    blender -b --factory-startup -P mv/build/char_preview.py -- --mode turntable
    blender -b --factory-startup -P mv/build/char_preview.py -- --mode hero
    blender -b --factory-startup -P mv/build/char_preview.py -- --mode all

Modes
    quick      5 diagnostic views at 960x540 (front / 3-4 / edge-on / back / face)
    calib      orthographic Standard-transform fidelity test (one cell, 1124x2022 RGBA)
    stills     the 8 expressions, 1920x1080 each  -> expr_<name>.png
    turntable  360 deg orbit, 240 frames (4 s @ 60 fps), 1920x1080 -> turntable/frame_####.png
    hero       one 2560x1440 hero frame             -> hero_2560x1440.png
    all        stills + turntable + hero

Every mode writes into mv/out/tests/char/. The turntable frames are encoded to mp4 with
    C:\\ffmpeg\\bin\\ffmpeg.exe -y -framerate 60 -i turntable/frame_%04d.png
        -c:v libx264 -crf 16 -pix_fmt yuv420p turntable_360.mp4
"""
import argparse
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "mv", "out", "tests", "char")
sys.path.insert(0, HERE)
import char_paper as cp  # noqa: E402

FPS = 60
FOG = "#0a2230"
INK = "#071a24"
PAPER = "#ece8de"
CORAL = "#ff6b4a"
CYAN = "#38c9ff"
GOLD = "#ffd28a"

# framing: the alpha bbox of the reference expression is 1.75 m tall, card is 2.14 m
BODY_H = 1.75
FRAME_H = 1.98          # metres of vertical world visible in the full-body framing
TARGET_Z = 0.88         # camera aim height
LENS = 85.0
SENSOR = 36.0


# ----------------------------------------------------------------------------- helpers
def lin(hexstr, alpha=1.0):
    return cp.hex_to_linear(hexstr, alpha)


def aim(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def new_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.render.fps = FPS
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.view_settings.exposure = 0.0
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.image_settings.color_depth = "8"
    sc.render.image_settings.compression = 15
    ee = sc.eevee
    ee.taa_render_samples = 24
    ee.use_raytracing = False
    ee.volumetric_start = 0.4
    ee.volumetric_end = 40.0
    ee.volumetric_samples = 64
    ee.use_volumetric_shadows = True
    ee.volumetric_shadow_samples = 24
    return sc


def setup_world(sc, density=0.014):
    world = bpy.data.worlds.new("FogArchive")
    sc.world = world
    world.use_nodes = True
    nt = world.node_tree
    nodes, links = nt.nodes, nt.links
    for n in list(nodes):
        nodes.remove(n)
    out = nodes.new("ShaderNodeOutputWorld")
    out.location = (300, 0)
    bg = nodes.new("ShaderNodeBackground")
    bg.location = (0, 200)
    bg.inputs["Color"].default_value = lin(INK)
    bg.inputs["Strength"].default_value = 0.35
    links.new(bg.outputs[0], out.inputs["Surface"])
    vol = nodes.new("ShaderNodeVolumePrincipled")
    vol.location = (0, -150)
    vol.inputs["Color"].default_value = lin(FOG)
    vol.inputs["Density"].default_value = density
    vol.inputs["Anisotropy"].default_value = 0.35
    vol.inputs["Absorption Color"].default_value = lin("#0c2a38")
    links.new(vol.outputs[0], out.inputs["Volume"])


def add_area(name, loc, target, energy, hexcolor, size=2.0, shape="SQUARE"):
    data = bpy.data.lights.new(name, "AREA")
    data.shape = shape
    data.size = size
    data.energy = energy
    data.color = lin(hexcolor)[:3]
    obj = bpy.data.objects.new(name, data)
    obj.location = loc
    bpy.context.scene.collection.objects.link(obj)
    aim(obj, target)
    return obj


def add_spot(name, loc, target, energy, hexcolor, size_deg=32.0, blend=0.45,
             radius=0.12, shadow=True):
    data = bpy.data.lights.new(name, "SPOT")
    data.energy = energy
    data.color = lin(hexcolor)[:3]
    data.spot_size = math.radians(size_deg)
    data.spot_blend = blend
    data.shadow_soft_size = radius
    data.use_shadow = shadow
    obj = bpy.data.objects.new(name, data)
    obj.location = loc
    bpy.context.scene.collection.objects.link(obj)
    aim(obj, target)
    return obj


def add_floor():
    me = bpy.data.meshes.new("Floor")
    # 400 m: the far edge must stay beyond the fog / below the horizon so the turntable
    # never shows a hard diagonal where the plane ends (was 60 m -> visible seam at 30 m).
    s = 400.0
    me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
    me.update()
    obj = bpy.data.objects.new("Floor", me)
    bpy.context.scene.collection.objects.link(obj)
    mat = bpy.data.materials.new("FloorPaper")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = lin("#08161c")
    bsdf.inputs["Roughness"].default_value = 0.60
    bsdf.inputs["Specular IOR Level"].default_value = 0.14
    bsdf.inputs["Metallic"].default_value = 0.0
    obj.data.materials.append(mat)
    return obj


# master light gain: 1.0 = the level that reproduces the art at ~1x albedo under AgX
LIGHT_GAIN = 1.0


def setup_lights(gain=None):
    """warm coral key / cool fill / cyan back rim / gold specimen spot.
    Energies were calibrated so the *diffuse albedo* comes back at ~1.0x (calib mode),
    i.e. the art is reproduced, not relit: the palette stays the palette."""
    g = LIGHT_GAIN if gain is None else float(gain)
    key = add_area("Key_Warm", (2.6, -3.4, 3.1), (0, 0, 1.15), 500.0 * g, "#ffd9c2", size=3.0)
    # fill sits 2.3 m up and is small: at z=1.5 / size 4 the 4 m square was half *below* the
    # floor plane, so the floor cut the light in half and its lower half cast a hard straight
    # shadow edge across the floor (visible as a diagonal wedge in the turntable).
    fill = add_area("Fill_Cool", (-3.2, -2.6, 2.3), (0, 0, 1.0), 120.0 * g, "#8fc4ff", size=2.6)
    rim = add_area("Rim_Cyan", (0.9, 3.4, 3.3), (0, 0, 1.45), 700.0 * g, CYAN, size=2.0)
    rim2 = add_area("Rim_Cyan_Low", (-2.2, 2.4, 1.4), (0, 0, 0.9), 110.0 * g, "#2ea8e0", size=1.5)
    spot = add_spot("Specimen_Gold", (0.35, -1.1, 6.4), (0, 0, 0.2), 1150.0 * g, GOLD,
                    size_deg=19.0, blend=0.55, radius=0.5)
    return dict(key=key, fill=fill, rim=rim, rim2=rim2, spot=spot)


def add_compositor(sc, threshold=1.05, size=7, mix=-0.45):
    sc.use_nodes = True
    nt = sc.node_tree
    nodes, links = nt.nodes, nt.links
    for n in list(nodes):
        nodes.remove(n)
    rl = nodes.new("CompositorNodeRLayers")
    rl.location = (-400, 0)
    glare = nodes.new("CompositorNodeGlare")
    glare.location = (-150, 0)
    glare.glare_type = "BLOOM"
    glare.quality = "HIGH"
    glare.threshold = threshold
    glare.size = size
    glare.mix = mix
    comp = nodes.new("CompositorNodeComposite")
    comp.location = (200, 0)
    links.new(rl.outputs["Image"], glare.inputs["Image"])
    links.new(glare.outputs["Image"], comp.inputs["Image"])


def camera(sc, yaw_deg=0.0, target_z=TARGET_Z, frame_h=FRAME_H, lens=LENS,
           res=(1920, 1080), pitch_drop=0.75, dist_scale=1.0, name="Cam"):
    """Place a camera on an arc around the character; yaw 0 = straight on (art faces -Y)."""
    sensor_h = SENSOR * res[1] / res[0]
    vfov = 2.0 * math.atan(sensor_h / (2.0 * lens))
    dist = (frame_h / 2.0) / math.tan(vfov / 2.0) * dist_scale
    yaw = math.radians(yaw_deg)
    pos = Vector((dist * math.sin(yaw), -dist * math.cos(yaw), target_z + pitch_drop))
    data = bpy.data.cameras.new(name)
    data.lens = lens
    data.sensor_width = SENSOR
    data.sensor_fit = "HORIZONTAL"
    data.clip_start = 0.05
    data.clip_end = 200.0
    obj = bpy.data.objects.new(name, data)
    obj.location = pos
    sc.collection.objects.link(obj)
    aim(obj, (0.0, 0.0, target_z))
    sc.camera = obj
    return obj


def set_res(sc, res, pct=100):
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = pct
    sc.render.pixel_aspect_x = sc.render.pixel_aspect_y = 1.0


def render_to(sc, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("RENDERED", path)


def build_character(name="fish", expr="cheerful", bend=2.5):
    ctrl = cp.build_character(name=name, expr=expr, height=BODY_H,
                              location=(0.0, 0.0, 0.0), bend=bend)
    ctrl["set_edge_glow"](CYAN, 2.5)
    ctrl["set_fog"](FOG, 0.014)      # EEVEE does not fog blended surfaces; see char_paper
    return ctrl


# ----------------------------------------------------------------------------- modes
def mode_quick():
    sc = new_scene()
    setup_world(sc)
    setup_lights()
    add_floor()
    add_compositor(sc)
    set_res(sc, (960, 540))
    ctrl = build_character()
    for tag, yaw in (("front", 0.0), ("three_quarter", 35.0), ("edge", 90.0), ("back", 180.0)):
        camera(sc, yaw_deg=yaw, name=f"Cam_{tag}")
        render_to(sc, os.path.join(OUT, "_diag", f"Q_{tag}.png"))
    # face close-up: 200 mm from 4 m, aimed at the face anchor
    face = ctrl["anchor"]("face")
    data = bpy.data.cameras.new("CamFace")
    data.lens = 200.0
    data.sensor_width = SENSOR
    obj = bpy.data.objects.new("CamFace", data)
    obj.location = (0.0, -5.0, face.z + 0.02)
    sc.collection.objects.link(obj)
    aim(obj, face)
    sc.camera = obj
    set_res(sc, (960, 540))
    render_to(sc, os.path.join(OUT, "_diag", "Q_face.png"))


def mode_stills():
    sc = new_scene()
    setup_world(sc)
    setup_lights()
    add_floor()
    add_compositor(sc)
    set_res(sc, (1920, 1080))
    ctrl = build_character()
    camera(sc, yaw_deg=0.0, name="CamStills")
    for expr in cp.EXPRESSIONS:
        ctrl["set_expression"](expr)
        render_to(sc, os.path.join(OUT, f"expr_{expr}.png"))
    ctrl["set_expression"]("maid")
    render_to(sc, os.path.join(OUT, "expr_maid.png"))


def mode_turntable():
    sc = new_scene()
    setup_world(sc)
    setup_lights()
    add_floor()
    add_compositor(sc)
    set_res(sc, (1920, 1080))
    build_character()
    # orbit rig: empty at body centre, camera parented, track-to keeps her centred
    pivot = bpy.data.objects.new("Orbit", None)
    pivot.location = (0.0, 0.0, TARGET_Z)
    sc.collection.objects.link(pivot)
    target = bpy.data.objects.new("OrbitTarget", None)
    target.location = (0.0, 0.0, TARGET_Z)
    sc.collection.objects.link(target)
    # keep the lighting camera-relative: at yaw 180 the fixed rim lights sit in FRONT of the
    # card and blow it out. A turntable is a geometry check, so light it consistently.
    for lname in ("Key_Warm", "Fill_Cool", "Rim_Cyan", "Rim_Cyan_Low", "Specimen_Gold"):
        lo = bpy.data.objects.get(lname)
        if lo is not None:
            lo.parent = pivot
            lo.matrix_parent_inverse = pivot.matrix_world.inverted()
    cam = camera(sc, yaw_deg=0.0, name="CamTurntable")
    cam.parent = pivot
    cam.location = cam.location - pivot.location
    tr = cam.constraints.new("TRACK_TO")
    tr.target = target
    tr.track_axis = "TRACK_NEGATIVE_Z"
    tr.up_axis = "UP_Y"
    sc.frame_start, sc.frame_end = 1, 240
    pivot.rotation_euler = (0.0, 0.0, 0.0)
    pivot.keyframe_insert("rotation_euler", index=2, frame=1)
    pivot.rotation_euler = (0.0, 0.0, 2.0 * math.pi)
    pivot.keyframe_insert("rotation_euler", index=2, frame=241)
    ad = pivot.animation_data
    for fc in ad.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    sc.render.filepath = os.path.join(OUT, "turntable", "frame_####")
    sc.render.use_file_extension = True
    bpy.ops.render.render(animation=True)
    print("TURNTABLE frames ->", os.path.join(OUT, "turntable"))


def mode_hero():
    sc = new_scene()
    setup_world(sc)
    setup_lights()
    add_floor()
    add_compositor(sc)
    set_res(sc, (2560, 1440))
    ctrl = build_character(expr="starry", bend=3.0)
    cam = camera(sc, yaw_deg=22.0, target_z=0.98, frame_h=2.15, lens=110.0,
                 res=(2560, 1440), pitch_drop=0.55, name="CamHero")
    # DOF OFF on purpose: EEVEE-Next DOF does not write BLENDED surfaces into the depth
    # prepass, so the alpha card is treated as *background* and gets the background CoC
    # (measured: lap-p99 31 vs 57 with the material switched to DITHERED). Any fstop <= 8
    # turns her into mush. See CHAR_INTERFACE.md "known limitations".
    cam.data.dof.use_dof = False
    render_to(sc, os.path.join(OUT, "hero_2560x1440.png"))


def mode_calib():
    """Colour-fidelity proof: orthographic, Standard view transform, film transparent,
    a sun of strength pi straight onto the art and *no* other light -> the render must
    reproduce the atlas cell 1:1 (compare with mv/out/tests/char/_diag/calib_compare.py)."""
    sc = new_scene()
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = 0.0
    sc.render.film_transparent = True
    sc.render.image_settings.color_mode = "RGBA"
    sc.eevee.taa_render_samples = 64
    # sun of strength pi: diffuse radiance = albedo * pi / pi = albedo
    sun_data = bpy.data.lights.new("CalibSun", "SUN")
    sun_data.energy = math.pi
    sun_data.color = (1.0, 1.0, 1.0)
    sun_data.angle = 0.0
    sun = bpy.data.objects.new("CalibSun", sun_data)
    sun.rotation_euler = (math.radians(90.0), 0.0, 0.0)   # light travels +Y, onto the art
    sc.collection.objects.link(sun)
    ctrl = cp.build_character(name="calib", expr="cheerful", height=BODY_H,
                              location=(0.0, 0.0, 0.0), bend=0.0, glow_strength=0.0)
    # kill specular so the render is pure albedo (no highlight added to the print)
    for m in (ctrl["mat"], ctrl["paper_mat"]):
        m.node_tree.nodes["Principled"].inputs["Specular IOR Level"].default_value = 0.0
    s = BODY_H / cp.REF_PX                     # metres per atlas pixel
    cam_data = bpy.data.cameras.new("CalibCam")
    cam_data.type = "ORTHO"
    cam_data.sensor_fit = "VERTICAL"
    cam_data.ortho_scale = cp.CELL_H * s
    cam = bpy.data.objects.new("CalibCam", cam_data)
    cam.location = (0.0, -10.0, (cp.ANCHOR_Y - cp.CELL_H * 0.5) * s)
    cam.rotation_euler = (math.radians(90.0), 0.0, 0.0)   # look along +Y
    sc.collection.objects.link(cam)
    sc.camera = cam
    set_res(sc, (cp.CELL_W, cp.CELL_H))
    render_to(sc, os.path.join(OUT, "_diag", "calib_cell.png"))


MODES = {"quick": mode_quick, "stills": mode_stills, "turntable": mode_turntable,
         "hero": mode_hero, "calib": mode_calib}


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="all", choices=list(MODES) + ["all"])
    ap.add_argument("--samples", type=int, default=0)
    ap.add_argument("--pct", type=int, default=0)
    args = ap.parse_args(argv)
    os.makedirs(OUT, exist_ok=True)
    if args.mode == "all":
        for m in ("stills", "turntable", "hero"):
            MODES[m]()
    else:
        MODES[args.mode]()
    print("DONE", args.mode)


if __name__ == "__main__":
    main()
