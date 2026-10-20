"""s15 - RESTORE / dawn: dawn surface, paper dog / tomato, the question comes back.

Memory: ?.  She surfaces into a warm dawn sea made of paper: a low paper sun on the horizon,
god rays through the haze, a paper tomato and a little paper pet on the floor beside her,
petals drifting up.  She looks up, turns starry, then cheerful - the question is answered.

Character = 2.5D paper doll (K.char_actor -> char_paper.build_character).  No modelled character.

FRAMES = (275.75, 295.35) -> N = 1176 local frames.
"""
import bpy, math, os, sys, random

MV = r'D:\Code\Code MV\new-word.search(you)'
sys.path.insert(0, os.path.join(MV, 'mv', 'build'))
import shotkit as K
import core as C
import world_theater as T
import specimens as SP

FRAMES = (275.75, 295.35)
FLOOR = K.FLOOR
N = 1176

WARM = (1.0, 0.72, 0.44)
PAPER = (0.84, 0.76, 0.62)
CYAN = (0.34, 0.72, 1.0)
GOLD = (1.0, 0.82, 0.46)

HER = (0.00, -11.90, FLOOR)
HER_FACE = (0.10, -4.0, FLOOR + 1.45)

FS = 4.0


def _dawn():
    """Low paper sun + glowing horizon band, eaten by the fog."""
    m = C.emissive('m_dawn', (1.0, 0.62, 0.34), 1.45)
    ob = C.plane('dawn_sky', size=1.0, loc=(0.0, -80.0, FLOOR + 9.0),
                 rot=(math.radians(90), 0, 0), mat=m)
    ob.scale = (300.0, 160.0, 1.0)
    K.glow_orb('dawn_sun', (2.2, -58.0, FLOOR + 4.2), radius=6.6,
               color=(1.0, 0.70, 0.40), strength=5.0)
    K.glow_orb('dawn_sun_halo', (2.2, -60.5, FLOOR + 4.2), radius=12.5,
               color=(1.0, 0.62, 0.34), strength=0.85)
    # soft haze band along the waterline: no straight horizon line, the sea dissolves into dawn
    for _i, _x in enumerate((-34.0, -18.0, -4.0, 10.0, 26.0, 40.0)):
        K.glow_orb('dawn_haze_%d' % _i, (_x, -64.0, FLOOR + 1.1), radius=12.0,
                   color=(1.0, 0.72, 0.46), strength=0.85)
    # the "sea" - a reflective slab so the sun smears into a path of light
    try:
        K.water_slab('dawn_sea', z=FLOOR, size=220.0)
    except Exception:
        K.floor_slab('dawn_sea', z=FLOOR, size=220.0, color=(0.020, 0.045, 0.060))
    # self-lit sheen over the sea so prop cards never band it with hard shadows
    try:
        _ms = C.emissive('m_sea_glow', (0.20, 0.25, 0.28), 0.34)
        _ps = C.plane('sea_glow', size=1.0, loc=(0.0, -26.0, FLOOR + 0.04),
                      rot=(0.0, 0.0, 0.0), mat=_ms)
        _ps.scale = (260.0, 260.0, 1.0)
        _ps.visible_shadow = False
    except Exception:
        pass


def _sunpath():
    """The sun's reflection on the water: a long warm sliver + soft breakup patches."""
    sp = C.plane('sun_path', size=1.0, loc=(1.8, -32.0, FLOOR + 0.08),
                 rot=(0.0, 0.0, 0.0),
                 mat=C.emissive('m_sunpath', (1.0, 0.72, 0.44), 0.55))
    sp.scale = (8.0, 46.0, 1.0)
    sp.visible_shadow = False
    for i, (yy, w, s) in enumerate(((-27.0, 12.0, 0.35), (-18.5, 16.0, 0.22),
                                    (-11.0, 20.0, 0.12))):
        ob = C.plane('sun_path_%d' % i, size=1.0, loc=(1.8, yy, FLOOR + 0.12),
                     rot=(0.0, 0.0, 0.0),
                     mat=C.emissive('m_sunpath_%d' % i, (1.0, 0.66, 0.38), s))
        ob.scale = (w, 3.0, 1.0)
        ob.visible_shadow = False


def _rays():
    """God rays: warm volumetric spots raking down through the haze."""
    for i, x in enumerate((-11.0, -7.0, -3.0, 1.0, 5.0, 9.0)):
        lt = C.light('ray_%d' % i, 'SPOT', loc=(x + 2.0, -18.0, FLOOR + 12.0),
                     energy=1150, color=(1.0, 0.80, 0.55), size=1.6,
                     angle=math.radians(20))
        C.look_at(lt, (x * 0.35, -9.5, FLOOR))
        lt.data.volume_factor = 3.6


def _props():
    """Paper tomato + a little paper pet, both standing on the paper sea."""
    try:
        SP.build_tomato_paper(location=(-1.85, -9.90, FLOOR), scale=0.55)
    except Exception:
        pass
    try:
        SP.build_cat(location=(1.60, -10.10, FLOOR), rotation=(0, 0, math.radians(-24)),
                     scale=0.30)
    except Exception:
        pass
    # chibi-pet cards cut from the official sprite sheet, far right, as a small flock
    cells = os.path.join(MV, 'mv', 'ref', 'art', 'sprite_cells')
    picks = ['9_4.png', '10_1.png', '8_6.png']
    for i, fn in enumerate(picks):
        p = os.path.join(cells, fn)
        if not os.path.exists(p):
            continue
        try:
            front, mat, back = C.paper_cutout(
                p, height=0.34, loc=(2.6 + i * 0.42, -9.4 - i * 0.35, FLOOR + 0.04),
                name='pet_card_%d' % i, emission_strength=0.05, rim=0.004)
            for ob in (front, back):
                try:
                    ob.visible_shadow = False
                except Exception:
                    pass
                K.drift(ob, 1, N, dloc=(0.0, 0.0, 0.10 + 0.03 * i),
                        drot=(0.0, 0.0, 0.0), loop=True)
        except Exception:
            pass


def _birds():
    """Distant paper koi kites above the dawn sea: read as birds in the haze."""
    for i, (col, x, ln, y, z) in enumerate((('#ff8a5c', -10.0, 0.9, -25.0, 2.4),
                                            ('#7fb0ff', -6.0, 0.8, -27.5, 3.1),
                                            ('#ffd27a', 8.0, 1.0, -26.0, 2.7),
                                            ('#ff6f5e', 12.0, 0.7, -28.5, 3.6))):
        try:
            coll = SP.build_koinobori(color=col, length=ln,
                                      location=(x, y, FLOOR + z),
                                      rotation=(0.0, math.radians(8), math.radians(-8)))
            root = SP.root_of(coll)
            K.drift(root, 1, N, dloc=(0.8 if i % 2 else -0.8, 0.0, 0.20),
                    drot=(0.0, 0.0, 0.06), loop=True)
        except Exception:
            pass


def _petals():
    rnd = random.Random(17)
    for i in range(20):
        x = rnd.uniform(-4.5, 4.5)
        y = rnd.uniform(-15.6, -12.9)
        z = FLOOR + rnd.uniform(0.2, 2.2)
        w = rnd.uniform(0.06, 0.16)
        tint = rnd.choice([PAPER, (0.92, 0.80, 0.62), (0.98, 0.86, 0.70)])
        ob = K.sheet('petal_%02d' % i, (x, y, z), w, w * rnd.uniform(0.5, 1.0),
                     rot=(math.radians(90) + rnd.uniform(-0.7, 0.7),
                          rnd.uniform(-0.7, 0.7), rnd.uniform(0, 6.28)),
                     color=tint, strength=rnd.uniform(0.10, 0.35), seed=i + 41)
        try:
            ob.visible_shadow = False
        except Exception:
            pass
        K.rise(ob, 1, N, dz=rnd.uniform(2.0, 4.5), start_scale=1.0, end_scale=1.0)


def build():
    K.begin(fog_density=0.030,
            fog_color=(0.120, 0.086, 0.055), ambient=(0.026, 0.019, 0.013),
            exposure=0.10)

    _dawn()
    _rays()

    key = C.light('dawn_key', 'AREA', loc=(4.2, -4.6, FLOOR + 4.2), energy=340,
                  color=(1.0, 0.78, 0.56), size=4.0)
    C.look_at(key, (0.2, -11.0, FLOOR + 1.10))
    sun_rim = C.light('dawn_sun_rim', 'AREA', loc=(1.6, -15.8, FLOOR + 3.4),
                      energy=640, color=(1.0, 0.72, 0.46), size=2.4)
    C.look_at(sun_rim, (0.0, -11.9, FLOOR + 1.40))
    rim = C.light('dawn_rim', 'AREA', loc=(-3.4, -15.4, FLOOR + 3.0), energy=260,
                  color=CYAN, size=2.2)
    C.look_at(rim, (0.2, -11.6, FLOOR + 1.30))
    fill = C.light('dawn_fill', 'AREA', loc=(2.6, -8.6, FLOOR + 2.0), energy=90,
                   color=(1.0, 0.88, 0.74), size=3.0)
    C.look_at(fill, (0.0, -11.9, FLOOR + 1.00))
    face = C.light('dawn_face', 'AREA', loc=(0.3, -8.4, FLOOR + 1.9), energy=55,
                   color=(1.0, 0.90, 0.80), size=1.6)
    C.look_at(face, (0.0, -11.9, FLOOR + 1.45))
    try:
        face.data.specular_factor = 0.1
    except Exception:
        pass

    _props()

    # ---- her
    ctrl = K.char_actor('shy', HER, height=1.75, face=HER_FACE, bend=2.0, glow_strength=0.9)
    K.char_expr(ctrl, [(1, 'shy', 2.0, 0.0),
                       (430, 'starry', 2.6, 0.8),
                       (820, 'cheerful', 2.0, 0.0),
                       (N, 'cheerful', 1.6, 0.0)])
    K.char_pose(ctrl, [(1, HER, (2.0, 0.0), 1.0),
                       (600, (HER[0], HER[1], HER[2] + 0.06), (2.4, 0.0), 1.0),
                       (N, (HER[0], HER[1], HER[2] + 0.10), (2.0, 0.0), 1.0)])

    _petals()
    C.dust('dawn_dust', count=520, extent=(11.0, 11.0, 6.0),
           center=(0.2, -11.0, FLOOR + 2.2), size=0.010,
           color=(1.0, 0.86, 0.62), strength=1.3)

    # ---- camera: wide dawn -> eye-level close
    for _ob in bpy.data.objects:
        _n = _ob.name.lower()
        if _ob.type != 'MESH':
            continue
        if _n.startswith(('fish', 'char')):
            continue
        _ob.visible_shadow = False


    _cam = K.cam_path('cam_s15', [
        (1, (5.20, -4.60, FLOOR + 2.90), (-0.10, -12.40, FLOOR + 1.35), 30, FS),
        (380, (1.45, -6.30, FLOOR + 1.85), (0.00, -11.95, FLOOR + 1.15), 38, FS),
        (760, (0.35, -6.85, FLOOR + 1.40), (0.04, -11.90, FLOOR + 1.02), 41, FS),
        (N, (0.10, -6.95, FLOOR + 1.18), (0.04, -11.90, FLOOR + 0.98), 42, FS),
    ])
    K.add_handheld(_cam, amp=0.010, scale=2.0, seed=15, rot_amp=0.0030)
