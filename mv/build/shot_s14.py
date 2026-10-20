"""s14 - RESURFACE / ascent: rising toward the water surface, god rays, koinobori.

Simple, strong version (per lead instruction): vertical camera rise + paper debris + koinobori
+ her as a glowing paper silhouette, with the water surface blooming above.

Character = 2.5D paper doll (K.char_actor).  No modelled character.

FRAMES = (261.06, 275.75) -> N = 881 local frames.
"""
import bpy, math, os, sys, random

MV = r'D:\Code\Code MV\new-word.search(you)'
sys.path.insert(0, os.path.join(MV, 'mv', 'build'))
import shotkit as K
import core as C
import world_theater as T
import specimens as SP

FRAMES = (261.06, 275.75)
FLOOR = K.FLOOR
N = 881

PAPER = (0.84, 0.78, 0.64)
WARM = (1.0, 0.74, 0.46)
CYAN = (0.34, 0.72, 1.0)
GOLD = (1.0, 0.84, 0.48)

UP = 12.0          # how far we rise (metres) - the surface lives at FLOOR+UP
HER = (0.55, -11.60, FLOOR)

FS = 4.0


def _surface():
    """The water surface: a soft warm glow far above, so it reads as light, not a ceiling."""
    m = C.emissive('m_surface', (0.92, 0.84, 0.68), 0.85)
    ob = C.plane('water_surface', size=1.0, loc=(0.0, -18.0, FLOOR + 26.0),
                 rot=(0.0, 0.0, 0.0), mat=m)
    ob.scale = (170.0, 170.0, 1.0)
    K.glow_orb('surface_glow', (0.5, -16.0, FLOOR + 23.0), radius=9.0,
               color=(1.0, 0.84, 0.64), strength=4.5)


def _water_column():
    """Big dim teal backdrop behind the climb: reads as the water column, kills the black void."""
    m = C.emissive('m_column', (0.22, 0.42, 0.55), 0.30)
    w = C.plane('column_wall', size=1.0, loc=(0.0, -46.0, FLOOR + 14.0),
                rot=(math.radians(90), 0, 0), mat=m)
    w.scale = (150.0, 90.0, 1.0)
    w.visible_shadow = False
    m2 = C.emissive('m_column_low', (0.30, 0.52, 0.62), 0.16)
    w2 = C.plane('column_wall_far', size=1.0, loc=(0.0, -70.0, FLOOR + 6.0),
                 rot=(math.radians(90), 0, 0), mat=m2)
    w2.scale = (220.0, 90.0, 1.0)
    w2.visible_shadow = False


def _god_rays():
    for i, (x, y) in enumerate(((-6.5, -13.0), (-2.5, -15.0), (1.5, -16.0),
                                (5.0, -14.0), (8.0, -12.5))):
        lt = C.light('ray_%d' % i, 'SPOT', loc=(x, y, FLOOR + UP + 2.0),
                     energy=1250, color=(1.0, 0.84, 0.60), size=1.8,
                     angle=math.radians(22))
        C.look_at(lt, (x * 0.2, y + 4.0, FLOOR))
        lt.data.volume_factor = 4.2


def _bubbles():
    """Bubble columns rising with the climb: small glowing spheres."""
    rnd = random.Random(57)
    for i in range(28):
        x = rnd.uniform(-3.6, 3.6)
        y = rnd.uniform(-16.0, -8.5)
        z = FLOOR + rnd.uniform(0.3, 2.5)
        ob = K.glow_orb('bubble_%02d' % i, (x, y, z),
                        radius=rnd.uniform(0.010, 0.035),
                        color=(0.72, 0.88, 1.0),
                        strength=rnd.uniform(0.25, 0.80))
        K.rise(ob, 1, N, dz=rnd.uniform(UP * 0.7, UP * 1.15),
               start_scale=0.8, end_scale=1.0)


def _koinobori():
    """Koinobori paper kites drifting up alongside the climb."""
    specs = [('#ff5733', -6.2, -18.5, 1.15),
             ('#3878ff', 5.6, -19.0, 0.95),
             ('#ffc756', -4.2, -21.0, 1.35),
             ('#eeeeea', 6.8, -20.4, 0.80),
             ('#ff8a5c', -9.0, -21.5, 0.90),
             ('#6fa8ff', 9.2, -20.0, 0.75),
             ('#ffd27a', -2.0, -22.5, 1.05),
             ('#e8f0f2', 3.0, -23.0, 0.70)]
    for i, (col, x, y, ln) in enumerate(specs):
        coll = None
        try:
            coll = SP.build_koinobori(color=col, length=ln,
                                      location=(x, y, FLOOR + 1.4 + i * 1.9),
                                      rotation=(0.0, math.radians(12), math.radians(-10)))
        except Exception:
            coll = None
        root = None
        if coll is not None:
            try:
                root = SP.root_of(coll)
            except Exception:
                root = None
        if root is None:
            continue
        K.drift(root, 1, N,
                dloc=(0.0, 0.0, UP * 0.62),
                drot=(0.10, 0.06, 0.25 * (1 if i % 2 else -1)), loop=False)
        try:
            SP.animate_flutter(coll, amplitude=0.10, speed=0.6 + 0.1 * i)
        except Exception:
            pass


def _debris():
    rnd = random.Random(43)
    for i in range(26):
        x = rnd.uniform(-6.0, 6.0)
        y = rnd.uniform(-18.0, -8.0)
        z = FLOOR + rnd.uniform(0.0, 3.0)
        w = rnd.uniform(0.08, 0.30)
        tint = rnd.choice([PAPER, (0.92, 0.84, 0.70), (0.74, 0.78, 0.86)])
        ob = K.sheet('debris_%02d' % i, (x, y, z), w, w * rnd.uniform(0.55, 1.0),
                     rot=(math.radians(90) + rnd.uniform(-0.9, 0.9),
                          rnd.uniform(-0.9, 0.9), rnd.uniform(0, 6.28)),
                     color=tint, strength=rnd.uniform(0.05, 0.25), seed=i + 51)
        K.rise(ob, 1, N, dz=rnd.uniform(UP * 0.8, UP * 1.3),
               start_scale=1.0, end_scale=1.0)


def build():
    K.begin(fog_density=0.028,
            fog_color=(0.095, 0.135, 0.160), ambient=(0.062, 0.082, 0.102),
            exposure=0.46)

    _surface()
    _water_column()
    K.floor_slab('ascent_floor', z=FLOOR, size=400.0, color=(0.170, 0.205, 0.225))
    # self-lit water floor: hides the slab horizon and the hard prop shadows
    try:
        _mf = C.emissive('m_asc_glow', (0.16, 0.22, 0.26), 0.35)
        _pf = C.plane('asc_glow', size=1.0, loc=(0.0, -24.0, FLOOR + 0.03),
                      rot=(0.0, 0.0, 0.0), mat=_mf)
        _pf.scale = (220.0, 220.0, 1.0)
        _pf.visible_shadow = False
    except Exception:
        pass
    _god_rays()
    _koinobori()
    _bubbles()
    _debris()

    key = C.light('asc_key', 'AREA', loc=(3.6, -6.0, FLOOR + 4.0), energy=620,
                  color=(1.0, 0.80, 0.58), size=3.6)
    C.look_at(key, (0.5, -11.6, FLOOR + 1.20))
    up = C.light('asc_up', 'AREA', loc=(0.5, -12.0, FLOOR + 20.0), energy=2400,
                 color=(1.0, 0.86, 0.68), size=14.0)
    C.look_at(up, (0.4, -11.4, FLOOR + 2.0))
    up.data.volume_factor = 0.6
    rim = C.light('asc_rim', 'AREA', loc=(-2.6, -15.0, FLOOR + 3.2), energy=380,
                  color=CYAN, size=2.2)
    C.look_at(rim, (0.5, -11.6, FLOOR + 1.40))

    # ---- her: rises with the camera, high glow so she reads as a paper silhouette
    ctrl = K.char_actor('serious', HER, height=1.75, face=(0.4, -4.0, FLOOR + 1.45),
                        bend=2.5, glow_strength=1.6)
    K.char_expr(ctrl, [(1, 'serious', 2.5, 0.0), (N, 'starry', 2.0, 0.0)])
    # continuity with s13: she dissolved into an outline, so she re-forms out of light here
    try:
        ctrl['set_flash'](0.80, frame=1)
        ctrl['set_flash'](0.42, frame=int(N * 0.22))
        ctrl['set_flash'](0.16, frame=int(N * 0.55))
        ctrl['set_flash'](0.05, frame=int(N * 0.80))
        ctrl['set_flash'](0.0, frame=N)
        ctrl['set_edge_glow'](strength=3.0, frame=1)
        ctrl['set_edge_glow'](strength=1.2, frame=int(N * 0.55))
        ctrl['set_edge_glow'](strength=0.6, frame=N)
    except Exception:
        import traceback
        traceback.print_exc()
    K.char_pose(ctrl, [(1, (HER[0], HER[1], FLOOR - 0.40), (2.5, 0.0), 1.0),
                       (int(N * 0.35), (HER[0] - 0.25, HER[1] + 0.15, FLOOR + 3.10), (3.0, 0.0), 1.0),
                       (int(N * 0.70), (HER[0] - 0.50, HER[1] + 0.30, FLOOR + 6.55), (2.8, 0.0), 1.0),
                       (N, (HER[0] - 0.70, HER[1] + 0.40, FLOOR + 9.00), (2.4, 0.0), 1.0)])

    C.dust('asc_dust', count=480, extent=(12.0, 12.0, 8.0),
           center=(0.4, -12.0, FLOOR + 4.0), size=0.010,
           color=(0.86, 0.92, 1.0), strength=1.1)

    # ---- camera: rigid vertical rise, slight look-up
    _cam = K.cam_path('cam_s14', [
        (1, (0.90, -7.40, FLOOR + 0.70), (0.55, -11.60, FLOOR + 0.70), 29, FS),
        (int(N * 0.35), (0.35, -7.15, FLOOR + 4.10), (0.30, -11.50, FLOOR + 4.20), 30, FS),
        (int(N * 0.70), (-0.20, -6.95, FLOOR + 7.60), (0.05, -11.40, FLOOR + 7.70), 31, FS),
        (N, (-0.55, -6.80, FLOOR + 10.20), (-0.20, -11.30, FLOOR + 10.20), 33, FS),
    ])
    K.add_handheld(_cam, amp=0.011, scale=2.2, seed=14, rot_amp=0.0030)
