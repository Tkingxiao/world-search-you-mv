"""shotkit.py - shared helpers for per-shot Blender modules.

A shot module lives at mv/build/shot_sXX.py and exposes:

    FRAMES = (t0, t1)          # seconds, global song time
    def build():               # builds scene from scratch, returns dict (optional)

Run with render_shot.py --shot sXX (1920x1080 / 60fps / 10 samples)
"""
import bpy, math, os, sys, random, json
from mathutils import Vector

MV = r'D:\Code\Code MV\new-word.search(you)'
BUILD = os.path.join(MV, 'mv', 'build')
if BUILD not in sys.path:
    sys.path.insert(0, BUILD)
for _m in ('core', 'world', 'geo', 'world_theater', 'stage', 'char_paper', 'specimens'):
    sys.modules.pop(_m, None)

import core as C
import world_theater as T
import geo as G
import stage as S
import char_paper as CH

FPS = C.FPS
W = C.W
H = C.H
SAMPLES = C.SAMPLES
FLOOR = -6.0
OUT = os.path.join(MV, 'mv', 'out', 'shots')
DATA = os.path.join(MV, 'mv', 'data')


# ------------------------------------------------------------------ timing / render
def frames_for(t0, t1):
    return int(round(t0 * FPS)) + 1, int(round(t1 * FPS))


def begin(samples=SAMPLES, fog_density=0.020, fog_color=(0.010, 0.045, 0.075),
          ambient=(0.008, 0.028, 0.045), exposure=0.15, glare=True):
    C.reset_soft()
    C.setup_render(samples=samples, w=W, h=H, glare=glare)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.render.fps_base = 1.0
    sc.render.resolution_percentage = 100
    sc.view_settings.exposure = exposure
    C.fog_world(density=fog_density, color=fog_color, ambient=ambient)
    return sc


def render_mp4(path, f0, f1, w=W, h=H, samples=SAMPLES, crf='HIGH'):
    sc = bpy.context.scene
    sc.render.resolution_x = w
    sc.render.resolution_y = h
    sc.render.resolution_percentage = 100
    sc.eevee.taa_render_samples = samples
    sc.render.image_settings.file_format = 'FFMPEG'
    sc.render.ffmpeg.format = 'MPEG4'
    sc.render.ffmpeg.codec = 'H264'
    sc.render.ffmpeg.constant_rate_factor = crf
    sc.render.ffmpeg.ffmpeg_preset = 'GOOD'
    sc.render.fps = FPS
    sc.frame_start = int(f0)
    sc.frame_end = int(f1)
    sc.frame_set(int(f0))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sc.render.filepath = path
    import time
    t = time.time()
    bpy.ops.render.render(animation=True)
    print('SHOT_RENDER %s frames=%d sec=%.1f per_frame=%.2f' % (
        os.path.basename(path), f1 - f0 + 1, time.time() - t,
        (time.time() - t) / max(1, f1 - f0 + 1)), flush=True)


def save_blend(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=path)
    print('SAVED ' + path, flush=True)


# ------------------------------------------------------------------ camera
def _set_interp(ob, kind='BEZIER'):
    ad = ob.animation_data
    if not ad or not ad.action:
        return
    for fc in ad.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = kind
            kp.handle_left_type = 'AUTO_CLAMPED'
            kp.handle_right_type = 'AUTO_CLAMPED'


def cam_path(name, keys, dof=False, smooth=True):
    """key = (frame, loc, target, lens, fstop).

    dof defaults to False: EEVEE-Next DOF does not write BLENDED (alpha) surfaces
    into its depth pre-pass, so the paper-cutout character gets background CoC and
    goes soft. Paper is flat anyway; keep DOF off for character shots.
    """
    """keys: [(frame, loc, target, lens, fstop)] -> animated camera.

    Rotation is keyed as QUATERNION (with sign continuity) so euler flips /
    gimbal spins cannot happen between keys that swing around the subject.
    """
    f0, loc0, tgt0, lens0, fs0 = keys[0]
    cam = C.camera(name, lens=lens0, loc=loc0, target=tgt0, dof=dof, fstop=fs0)
    cam.rotation_mode = 'QUATERNION'
    prev_q = None
    for (f, loc, tgt, lens, fs) in keys:
        cam.location = loc
        q = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y')
        if prev_q is not None and q.dot(prev_q) < 0.0:
            q.negate()
        prev_q = q.copy()
        cam.rotation_quaternion = q
        cam.data.lens = lens
        cam.data.dof.aperture_fstop = fs
        cam.data.dof.focus_distance = (Vector(tgt) - Vector(loc)).length
        cam.keyframe_insert('location', frame=f)
        cam.keyframe_insert('rotation_quaternion', frame=f)
        cam.data.keyframe_insert('lens', frame=f)
        cam.data.dof.keyframe_insert('aperture_fstop', frame=f)
        cam.data.dof.keyframe_insert('focus_distance', frame=f)
    if smooth:
        _set_interp(cam)
        _set_interp(cam.data)
    bpy.context.scene.camera = cam
    try:
        add_handheld(cam, amp=0.0075, scale=1.9, seed=abs(hash(name)) % 997)
    except Exception as _e:
        print('handheld failed: %r' % (_e,), flush=True)
    return cam


def add_handheld(cam, amp=0.012, scale=1.6, seed=0, rot_amp=0.0045):
    """DISABLED (v3): the noise drift read as constant camera shake in motion.

    Kept as a no-op so every existing call site (cam_path's automatic call and the
    explicit per-shot calls) keeps working while the cameras stay rock steady.
    """
    return cam
    rnd = __import__('random').Random(seed)  # noqa: unreachable (kept for reference)
    ad = cam.animation_data
    if ad is None:
        return cam
    for i, fc in enumerate(ad.action.fcurves):
        mod = fc.modifiers.new('NOISE')
        mod.scale = scale * rnd.uniform(0.8, 1.25)
        mod.strength = amp if i < 3 else rot_amp
        mod.phase = rnd.uniform(0, 100)
        mod.depth = 2
    return cam


def ease(ob):
    _set_interp(ob)


# ------------------------------------------------------------------ character
def char_actor(expr='cheerful', loc=(0.55, -11.2, FLOOR), height=1.75,
               face=(0.0, -2.0, FLOOR + 1.2), **opts):
    """Build the 2.5D paper character facing `face` (a world point)."""
    dx = face[0] - loc[0]
    dy = face[1] - loc[1]
    yaw = math.degrees(math.atan2(dx, dy)) + 180.0
    ctrl = CH.build_character(expr=expr, height=height, location=loc,
                              yaw=yaw, **opts)
    return ctrl


def char_expr(ctrl, keys):
    """keys: [(frame, expr)] or [(frame, expr, bend, lateral)]"""
    for k in keys:
        f, expr = k[0], k[1]
        bend = k[2] if len(k) > 2 else None
        lat = k[3] if len(k) > 3 else None
        ctrl['set_expression'](expr, frame=f, flash=0)
        if bend is not None:
            ctrl['set_bend'](bend, lateral=lat, frame=f)


def char_pose(ctrl, keys):
    """keys: [(frame, (x,y,z), (bend_deg, lateral_deg), height_scale)]"""
    root = ctrl['root']
    for k in keys:
        f = k[0]
        if len(k) > 1 and k[1] is not None:
            root.location = k[1]
            root.keyframe_insert('location', frame=f)
        if len(k) > 2 and k[2] is not None:
            ctrl['set_bend'](k[2][0], lateral=k[2][1], frame=f)
        if len(k) > 3 and k[3] is not None:
            root.scale = (k[3], k[3], k[3])
            root.keyframe_insert('scale', frame=f)


# ------------------------------------------------------------------ generic object anim
def obj_keys(ob, keys, prop='location'):
    for f, val in keys:
        setattr(ob, prop, val)
        ob.keyframe_insert(prop, frame=f)
    ease(ob)


def rise(ob, f0, f1, dz=0.6, start_scale=0.6, end_scale=1.0):
    """Object rises and grows into place."""
    p0 = tuple(ob.location)
    p1 = (p0[0], p0[1], p0[2] + dz)
    ob.location = p1
    ob.scale = (end_scale, end_scale, end_scale)
    ob.keyframe_insert('location', frame=f1)
    ob.keyframe_insert('scale', frame=f1)
    ob.location = (p1[0], p1[1], p1[2] - dz * 1.6)
    ob.scale = (start_scale, start_scale, start_scale)
    ob.keyframe_insert('location', frame=f0)
    ob.keyframe_insert('scale', frame=f0)
    ease(ob)


def drift(ob, f0, f1, dloc=(0, 0, 0), drot=(0, 0, 0), loop=True):
    p0 = tuple(ob.location)
    r0 = tuple(ob.rotation_euler)
    ob.location = p0
    ob.rotation_euler = r0
    ob.keyframe_insert('location', frame=f0)
    ob.keyframe_insert('rotation_euler', frame=f0)
    ob.location = (p0[0] + dloc[0], p0[1] + dloc[1], p0[2] + dloc[2])
    ob.rotation_euler = (r0[0] + drot[0], r0[1] + drot[1], r0[2] + drot[2])
    ob.keyframe_insert('location', frame=f1)
    ob.keyframe_insert('rotation_euler', frame=f1)
    ease(ob)


def blink_scale(ob, f0, f1, period=36, base=1.0, dim=0.001):
    """Cursor blink: keyframe scale between base*dims and ~0, keeping the object's dims."""
    b = tuple(ob.scale)
    f = f0
    on = True
    while f <= f1:
        s = base if on else dim
        ob.scale = (b[0] * s, b[1] * s, b[2] * s)
        ob.keyframe_insert('scale', frame=int(f))
        on = not on
        f += period
    if ob.animation_data and ob.animation_data.action:
        for fc in ob.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'CONSTANT'


# ------------------------------------------------------------------ emissive helpers
def face_plus_y(ob):
    """Orient a flat card / text so its front faces +Y and it reads correctly
    for a camera standing on the +Y side (screen right = world -X)."""
    from mathutils import Matrix
    ob.matrix_world = Matrix(((-1, 0, 0, ob.location.x),
                              (0, 0, 1, ob.location.y),
                              (0, 1, 0, ob.location.z),
                              (0, 0, 0, 1)))
    return ob


def glow_orb(name, loc, radius=0.05, color=(0.4, 0.8, 1.0), strength=6.0):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=loc, segments=12, ring_count=8)
    ob = bpy.context.object
    ob.name = name
    ob.data.materials.append(C.emissive(name + '_m', color, strength))
    ob.visible_shadow = False
    return ob


def sheet(name, loc, w, h, rot=(math.radians(90), 0, 0), color=(0.72, 0.66, 0.54),
          strength=0.06, seed=1):
    """A paper sheet with soft fiber material (flat card)."""
    m = C.paper(name + '_m', base=color, rough=0.88)
    try:
        m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = strength
    except Exception:
        pass
    ob = C.plane(name, size=1.0, loc=loc, rot=rot, mat=m)
    ob.scale = (w, h, 1.0)
    return ob


def floor_slab(name='floor', z=FLOOR, size=60.0, color=(0.055, 0.050, 0.042)):
    m = C.paper(name + '_m', base=color, rough=0.92)
    ob = C.plane(name, size=size, loc=(0, -12, z), rot=(0, 0, 0), mat=m)
    return ob


def water_slab(name='water', z=FLOOR, size=120.0, color=(0.010, 0.020, 0.030)):
    m = C._principled(name + '_m', color, rough=0.06, metal=0.35)
    ob = C.plane(name, size=size, loc=(0, -14, z), rot=(0, 0, 0), mat=m)
    return ob
