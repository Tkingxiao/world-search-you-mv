"""s13 - RESURFACE / warm: warm paper sky, the whale swims through drifting sheets.

Memory: merged.  She stands in a warm, fog-hazed paper hall while a giant paper-cut whale
(printed with her own ghosted art) glides past above her.  Halfway through she is merged into
it: white flash, her card shrinks into a cyan outline (halo card), then the outline dissolves
and only the warm sheets + the whale remain.

The character is the 2.5D paper-doll (char_paper.build_character via K.char_actor); the whale
is a single paper cut-out PNG (mv/assets/char/whale_paper.png) - no modelled geometry.

FRAMES = (233.77, 261.06) -> N = 1638 local frames.
"""
import bpy, math, os, sys, random

MV = r'D:\Code\Code MV\new-word.search(you)'
sys.path.insert(0, os.path.join(MV, 'mv', 'build'))
import shotkit as K
import core as C
import geo as G
import world_theater as T
import stage as S
import specimens as SP

FRAMES = (233.77, 261.06)
FLOOR = K.FLOOR
N = 1638

CHAR_PATH = os.path.join(MV, 'mv', 'assets', 'char')
WHALE = os.path.join(CHAR_PATH, 'whale_paper.png')
WHALE_SMALL = os.path.join(CHAR_PATH, 'whale_paper_small.png')
HALO = os.path.join(CHAR_PATH, 'halo_serious.png')

HER = (0.55, -11.60, FLOOR)          # her feet
HER_FACE = (0.15, -2.0, FLOOR + 1.35)

WARM = (1.0, 0.74, 0.46)
PAPER = (0.80, 0.72, 0.58)
CYAN = (0.30, 0.70, 1.0)
GOLD = (1.0, 0.80, 0.42)


def _sky():
    """Warm paper sky: one huge dim warm backdrop + a sun disc, both eaten by the fog."""
    m = C.emissive('m_sky', (1.0, 0.74, 0.48), 0.50)
    w = C.plane('sky_wall', size=1.0, loc=(0.0, -72.0, FLOOR + 2.0),
                rot=(math.radians(90), 0, 0), mat=m)
    w.scale = (320.0, 140.0, 1.0)
    w.visible_shadow = False
    # luminous horizon band: the sheets / whale are read against it, and the floor
    # dissolves into it instead of ending on a hard line
    # sun: three layered discs = soft glare without a bloom pass
    K.glow_orb('sun', (8.6, -34.0, FLOOR + 7.0), radius=3.0,
               color=(1.0, 0.76, 0.46), strength=16.0)
    K.glow_orb('sun_halo', (8.6, -36.0, FLOOR + 7.0), radius=6.4,
               color=(1.0, 0.66, 0.36), strength=1.6)


def _sheets():
    """Drifting back-lit sheets, kept in a band well behind the camera corridor."""
    rnd = random.Random(13)
    obs = []
    for i in range(11):
        x = rnd.uniform(-6.5, 6.5)
        y = rnd.uniform(-19.0, -13.0)
        z = FLOOR + rnd.uniform(0.8, 4.6)
        w = rnd.uniform(0.55, 1.5)
        h = w * rnd.uniform(0.65, 1.05)
        tint = rnd.choice([PAPER, (0.86, 0.78, 0.62), (0.72, 0.66, 0.54), (0.90, 0.80, 0.60)])
        ob = K.sheet('warm_sheet_%02d' % i, (x, y, z), w, h,
                     rot=(math.radians(90) + rnd.uniform(-0.30, 0.30),
                          rnd.uniform(-0.25, 0.25), rnd.uniform(0, 6.28)),
                     color=tint, strength=rnd.uniform(0.10, 0.30), seed=i + 3)
        ob.visible_shadow = False
        K.drift(ob, 1, N,
                dloc=(rnd.uniform(-0.9, 0.9), rnd.uniform(-0.5, 0.5), rnd.uniform(0.35, 1.1)),
                drot=(rnd.uniform(-0.25, 0.25), rnd.uniform(-0.25, 0.25), rnd.uniform(-0.5, 0.5)))
        obs.append(ob)
    return obs


def _paper_sky():
    """Far layer of big warm paper sheets: reads as a paper-cloud sky, hides the empty wall."""
    rnd = random.Random(29)
    for i in range(11):
        x = rnd.uniform(-16.0, 16.0)
        y = rnd.uniform(-34.0, -22.0)
        z = FLOOR + rnd.uniform(2.0, 11.0)
        w = rnd.uniform(4.0, 9.0)
        h = w * rnd.uniform(0.55, 0.9)
        tint = rnd.choice([(0.92, 0.82, 0.64), (0.86, 0.74, 0.56), (0.95, 0.86, 0.70)])
        ob = K.sheet('sky_sheet_%02d' % i, (x, y, z), w, h,
                     rot=(math.radians(90) + rnd.uniform(-0.22, 0.22),
                          rnd.uniform(-0.20, 0.20), rnd.uniform(0, 6.28)),
                     color=tint, strength=rnd.uniform(0.30, 0.55), seed=i + 11)
        ob.visible_shadow = False
        K.drift(ob, 1, N,
                dloc=(rnd.uniform(-1.4, 1.4), rnd.uniform(-0.6, 0.6), rnd.uniform(0.2, 0.7)),
                drot=(rnd.uniform(-0.06, 0.06), rnd.uniform(-0.06, 0.06), rnd.uniform(-0.08, 0.08)))


def _mid_sheets():
    """A few mid-distance sheets (behind the whale) that fill the middle band."""
    rnd = random.Random(37)
    for i in range(4):
        x = rnd.uniform(-11.0, 11.0)
        y = rnd.uniform(-24.0, -18.0)
        z = FLOOR + rnd.uniform(1.5, 6.5)
        w = rnd.uniform(1.2, 2.6)
        h = w * rnd.uniform(0.6, 1.0)
        tint = rnd.choice([(0.95, 0.86, 0.70), (0.88, 0.78, 0.62), (0.98, 0.90, 0.76)])
        ob = K.sheet('mid_sheet_%02d' % i, (x, y, z), w, h,
                     rot=(math.radians(90) + rnd.uniform(-0.35, 0.35),
                          rnd.uniform(-0.30, 0.30), rnd.uniform(0, 6.28)),
                     color=tint, strength=rnd.uniform(0.25, 0.45), seed=i + 21)
        ob.visible_shadow = False
        K.drift(ob, 1, N, dloc=(rnd.uniform(-1.0, 1.0), rnd.uniform(-0.5, 0.5),
                                rnd.uniform(0.2, 0.8)),
                drot=(rnd.uniform(-0.08, 0.08), rnd.uniform(-0.08, 0.08),
                      rnd.uniform(-0.12, 0.12)))


def _clouds():
    """Big soft paper clouds, two more depth layers behind the whale band."""
    rnd = random.Random(71)
    for i in range(5):
        x = rnd.uniform(-14.0, 14.0)
        y = rnd.uniform(-48.0, -40.0)
        z = FLOOR + rnd.uniform(2.0, 6.5)
        w = rnd.uniform(4.0, 7.0)
        ob = K.sheet('cloud_%02d' % i, (x, y, z), w, w * 0.52,
                     rot=(math.radians(90) + rnd.uniform(-0.12, 0.12),
                          rnd.uniform(-0.10, 0.10), rnd.uniform(0, 6.28)),
                     color=(1.0, 0.86, 0.66), strength=rnd.uniform(0.35, 0.60), seed=i + 91)
        ob.visible_shadow = False
        K.drift(ob, 1, N, dloc=(rnd.uniform(-2.0, 2.0), 0.0, rnd.uniform(0.1, 0.4)),
                drot=(0.0, 0.0, rnd.uniform(-0.04, 0.04)), loop=True)


def _rays():
    """Warm volumetric shafts raking out of the sun through the haze."""
    for i, (x, y) in enumerate(((6.4, -13.0), (2.0, -15.5), (-2.0, -16.5), (-5.5, -14.5))):
        lt = C.light('sun_ray_%d' % i, 'SPOT', loc=(x, y, FLOOR + 12.0),
                     energy=1200, color=(1.0, 0.80, 0.52), size=1.6,
                     angle=math.radians(17))
        C.look_at(lt, (x - 2.6, y + 5.5, FLOOR + 1.0))
        lt.data.volume_factor = 5.0


def _petals():
    """Warm paper petals / scraps floating through the light between camera and her."""
    rnd = random.Random(83)
    for i in range(24):
        x = rnd.uniform(-6.0, 6.0)
        y = rnd.uniform(-14.0, -7.0)
        z = FLOOR + rnd.uniform(0.3, 3.2)
        w = rnd.uniform(0.05, 0.13)
        ob = K.sheet('s_petal_%02d' % i, (x, y, z), w, w * rnd.uniform(0.6, 1.0),
                     rot=(rnd.uniform(-0.9, 0.9), rnd.uniform(-0.9, 0.9),
                          rnd.uniform(0, 6.28)),
                     color=(1.0, 0.90, 0.72), strength=rnd.uniform(0.15, 0.35),
                     seed=i + 43)
        ob.visible_shadow = False
        K.drift(ob, 1, N,
                dloc=(rnd.uniform(-0.6, 0.6), rnd.uniform(-0.3, 0.3),
                      rnd.uniform(0.3, 1.0)),
                drot=(rnd.uniform(-0.6, 0.6), rnd.uniform(-0.5, 0.5),
                      rnd.uniform(-0.8, 0.8)), loop=True)


def _whale(path, height, loc, name, x0, x1, y0, y1, z0, z1, keys=5):
    """Paper-cut whale gliding across the hall (nose leads: x decreases)."""
    front, mat, back = C.paper_cutout(path, height=height, loc=loc, name=name,
                                      emission_strength=0.12, rim=0.012)
    for ob in (front, back):
        p = tuple(ob.location)
        for i in range(keys):
            t = i / (keys - 1.0)
            f = 1 + round((N - 1) * t)
            ob.location = (x0 + (x1 - x0) * t,
                           p[1] + y0 + (y1 - y0) * t,
                           p[2] + z0 + (z1 - z0) * t + 0.12 * math.sin(t * math.pi * 3.0))
            ob.keyframe_insert('location', frame=f)
        K.ease(ob)
    return front, back


def build():
    K.begin(fog_density=0.018,
            fog_color=(0.285, 0.222, 0.158), ambient=(0.070, 0.050, 0.034),
            exposure=0.20)

    _sky()
    K.floor_slab('warm_floor', z=FLOOR, size=400.0, color=(0.100, 0.082, 0.062))
    # self-lit paper floor: kills the hard shadow band the big backdrop cards cast across the
    # far floor (opaque emissive cards still occlude the key light in EEVEE-Next).
    _mf = C.emissive('m_floor_glow', (0.42, 0.33, 0.23), 0.30)
    _pf = C.plane('floor_glow', size=1.0, loc=(0.0, -20.0, FLOOR + 0.03),
                  rot=(0.0, 0.0, 0.0), mat=_mf)
    _pf.scale = (150.0, 150.0, 1.0)
    _pf.visible_shadow = False
    _sheets()
    _paper_sky()
    _mid_sheets()
    _rays()
    _petals()

    # ---- the paper flower she is looking at (camera opens on it)
    try:
        T.plinth(-2.55, -9.30, h=0.52, w=0.66, d=0.66, gold=True, label=False)
    except Exception:
        pass
    try:
        SP.build_flower(location=(-2.55, -9.30, FLOOR + 0.52), scale=0.62)
    except Exception:
        pass

    # ---- giant paper whale (printed with her ghosted art) + a small distant one
    _whale(WHALE, 3.00, (7.0, -14.2, FLOOR + 2.85), 'whale', 8.0, -9.5, 0.0, 1.2, 0.0, 0.20)
    _whale(WHALE_SMALL, 1.25, (5.0, -29.0, FLOOR + 3.40), 'whale_far', 6.0, -9.0, 0.0, 1.2, 0.0, -0.4)

    # ---- her: the 2.5D paper doll
    ctrl = K.char_actor('shy', HER, height=1.75, face=HER_FACE, bend=2.0, glow_strength=0.8)
    K.char_expr(ctrl, [(1, 'shy', 2.0, 0.0),
                       (420, 'serious', 3.0, 1.2),
                       (N, 'serious', 2.2, 0.0)])
    K.char_pose(ctrl, [(1, HER, (2.0, 0.0), 1.0),
                       (620, (HER[0], HER[1] + 0.10, HER[2] + 0.05), (2.6, 0.0), 1.0),
                       (1000, (HER[0], HER[1] + 0.16, HER[2] + 0.10), (3.0, 0.0), 1.0),
                       (1150, (HER[0], HER[1] + 0.20, HER[2] + 0.14), (3.4, 0.0), 1.0),
                       (N, (HER[0], HER[1] + 0.22, HER[2] + 0.16), (3.0, 0.0), 1.0)])
    # white flash on the merge, then she shrinks into her own outline
    ctrl['set_flash'](0.0, frame=980)
    ctrl['set_flash'](1.0, frame=1030)
    ctrl['set_flash'](0.0, frame=1075)
    root = ctrl['root']
    for f, s in ((1, 1.0), (1030, 1.0), (1120, 0.55), (1150, 0.001), (N, 0.001)):
        root.scale = (s, s, s)
        root.keyframe_insert('scale', frame=f)
    K.ease(root)

    # ---- her outline: cyan halo card aligned to her card, fades in as she dissolves
    s = 1.75 / 1653.0
    halo_h = 2022 * s
    halo, halo_mat = C.illustration_card(HALO, height=halo_h,
                                        loc=(HER[0], HER[1] - 0.012, HER[2] - 9 * s),
                                        name='her_outline', emission_strength=0.0)
    nt = halo_mat.node_tree
    bsdf = nt.nodes['Principled BSDF']
    tex = None
    for nd in nt.nodes:
        if nd.type == 'TEX_IMAGE':
            tex = nd
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Emission Color'])
    bsdf.inputs['Base Color'].default_value = (0.02, 0.03, 0.04, 1.0)
    mul = nt.nodes.new('ShaderNodeMath')
    mul.operation = 'MULTIPLY'
    mul.name = 'Halo_Alpha'
    mul.inputs[1].default_value = 0.0
    nt.links.new(tex.outputs['Alpha'], mul.inputs[0])
    nt.links.new(mul.outputs[0], bsdf.inputs['Alpha'])
    for f, e in ((1, 0.0), (1000, 0.0), (1060, 1.4), (1120, 1.7), (1400, 1.45), (1560, 0.0), (N, 0.0)):
        bsdf.inputs['Emission Strength'].default_value = e
        bsdf.inputs['Emission Strength'].keyframe_insert('default_value', frame=f)
    for f, a in ((1, 0.0), (1000, 0.0), (1060, 1.0), (1500, 1.0), (1560, 0.0), (N, 0.0)):
        mul.inputs[1].default_value = a
        mul.inputs[1].keyframe_insert('default_value', frame=f)
    try:
        halo_mat.use_transparent_shadow = False
    except Exception:
        pass

    # ---- lights: warm key, soft warm fill, cyan rim from behind, gold spot on the flower,
    #      and a huge warm backlight that makes the fog itself glow (the "paper sky")
    key = C.light('warm_key', 'AREA', loc=(-3.2, -7.2, FLOOR + 3.0), energy=560,
                  color=(1.0, 0.80, 0.58), size=2.4)
    C.look_at(key, (0.4, -11.6, FLOOR + 1.2))
    fill = C.light('warm_fill', 'AREA', loc=(1.9, -8.2, FLOOR + 2.3), energy=110,
                   color=(1.0, 0.86, 0.72), size=2.4)
    C.look_at(fill, (0.4, -11.6, FLOOR + 1.1))
    rim = C.light('cyan_rim', 'AREA', loc=(2.6, -14.4, FLOOR + 2.6), energy=470,
                  color=(0.34, 0.70, 1.0), size=1.8)
    C.look_at(rim, (0.4, -11.6, FLOOR + 1.3))
    bounce = C.light('warm_bounce', 'AREA', loc=(-2.2, -9.0, FLOOR + 0.45), energy=170,
                     color=(1.0, 0.66, 0.40), size=2.6)
    C.look_at(bounce, (0.5, -11.6, FLOOR + 1.2))
    bounce.data.use_shadow = False
    spot = C.light('gold_spot', 'SPOT', loc=(-2.40, -6.60, FLOOR + 4.0), energy=240,
                   color=GOLD, size=0.55, angle=math.radians(26))
    C.look_at(spot, (-2.55, -9.30, FLOOR + 0.92))
    spot.data.volume_factor = 2.0
    back = C.light('sky_glow', 'AREA', loc=(3.5, -26.0, FLOOR + 7.0), energy=900,
                   color=(1.0, 0.70, 0.42), size=12.0)
    C.look_at(back, (0.0, -11.0, FLOOR + 2.0))
    back.data.volume_factor = 2.0

    C.dust('warm_dust', count=650, extent=(11.0, 11.0, 6.0),
           center=(0.4, -13.0, FLOOR + 2.4), size=0.012,
           color=(1.0, 0.84, 0.58), strength=1.3)

    # ---- camera: flower -> her -> wide (long take)
    _cam = K.cam_path('cam_s13', [
        (1, (2.35, -4.15, FLOOR + 2.55), (-1.90, -13.20, FLOOR + 1.20), 38, 4.0),
        (300, (0.85, -5.30, FLOOR + 1.95), (0.45, -11.60, FLOOR + 1.10), 46, 4.0),
        (620, (0.30, -5.20, FLOOR + 1.72), (0.50, -11.60, FLOOR + 1.02), 50, 4.0),
        (980, (-0.35, -5.15, FLOOR + 1.66), (0.55, -11.60, FLOOR + 1.06), 53, 4.0),
        (1240, (-0.95, -5.10, FLOOR + 1.58), (0.60, -11.60, FLOOR + 1.10), 55, 4.0),
        (N, (2.55, -3.60, FLOOR + 2.35), (-0.40, -13.20, FLOOR + 1.05), 42, 4.0),
    ])
    K.add_handheld(_cam, amp=0.012, scale=2.1, seed=13, rot_amp=0.0032)
