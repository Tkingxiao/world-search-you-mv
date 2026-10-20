"""s10 - FORGET / typewriter: the typewriter page, words miss, dope -> love.

Memory buries the error.  She stands in front of a huge hanging typewriter page and types over
her own memory: letters fall and miss the page, a torn photo sinks past her, and she goes
exasperated -> confused -> frightened as the wrong word gets written.

Character = 2.5D paper doll (K.char_actor).  No modelled character.

FRAMES = (151.84, 179.47) -> N = 1658 local frames.
"""
import bpy, math, os, sys, random

MV = r'D:\Code\Code MV\new-word.search(you)'
sys.path.insert(0, os.path.join(MV, 'mv', 'build'))
import shotkit as K
import core as C
import world_theater as T
import specimens as SP

FRAMES = (151.84, 179.47)
FLOOR = K.FLOOR
N = 1658

INK = (0.045, 0.055, 0.075)
PAPER = (0.84, 0.80, 0.70)
WARM = (1.0, 0.72, 0.44)
CYAN = (0.30, 0.68, 1.0)

HER = (0.05, -11.60, FLOOR)
HER_FACE = (0.00, -4.0, FLOOR + 1.45)
PAGE_Y = -13.60
PAGE_X = -1.05

FS = 4.0


def _page():
    """The huge typewriter page, hanging in the archive.

    NOTE: intentionally a *plain* lit sheet + real type instead of
    SP.build_index_sheet(): the specimen builder's hologram layers
    (wireframe + point cloud + shell) made this shot ~9x slower
    (18 s/frame vs ~2 s), so they are disabled here.
    """
    m = C.paper('m_typepage', base=(0.60, 0.555, 0.475), rough=0.94)
    pg = C.plane('type_page', size=1.0, loc=(PAGE_X, PAGE_Y, FLOOR + 1.34),
                 rot=(math.radians(90), 0, math.pi), mat=m)
    pg.scale = (2.02, 2.62, 1.0)
    try:
        pg.visible_shadow = False
    except Exception:
        pass
    # typed lines, dark ink on the lit page
    ink = C.paper('m_typeink', base=(0.055, 0.050, 0.048), rough=0.75)
    lines = [
        "dear you,",
        "each one of us has a bucket of love",
        "some empty, some filled up",
        "cut this into pieces, break us down",
        "to the cell, merge us back up",
        "we have evolved now",
        "",
        "you must be the most delicate ever",
        "you must be blue point at the toe",
        "you must be small enough to hold",
        "",
        "I'm searching",
        "I'm searching",
        "I'm searching",
    ]
    z0 = FLOOR + 2.30
    for i, ln in enumerate(lines):
        if not ln:
            continue
        t = C.text_obj('type_line_%02d' % i, ln, size=0.074,
                       loc=(PAGE_X, PAGE_Y + 0.012, z0 - i * 0.158), mat=ink,
                       align='CENTER', extrude=0.0,
                       font='C:/Windows/Fonts/consola.ttf')
        K.face_plus_y(t)
        try:
            t.visible_shadow = False
        except Exception:
            pass
    # hanging threads of the page (two thin emissive lines)
    th = C.emissive('m_pthread', (0.62, 0.58, 0.50), 0.6)
    for sx in (PAGE_X - 0.92, PAGE_X + 0.92):
        a = (sx, PAGE_Y, FLOOR + 2.66)
        b = (sx, PAGE_Y, FLOOR + 5.6)
        dh = b[2] - a[2]
        bpy.ops.mesh.primitive_cylinder_add(radius=0.006, depth=dh,
            location=((a[0]+b[0])/2, (a[1]+b[1])/2, (a[2]+b[2])/2), vertices=6)
        tob = bpy.context.object
        tob.name = 'page_thread_' + ('l' if sx < 0 else 'r')
        tob.data.materials.append(th)
        tob.visible_shadow = False


def _falling_letters():
    """Ink-dark letter cards raining down in front of the page; they miss."""
    rnd = random.Random(23)
    for i in range(40):
        x = rnd.uniform(-2.6, 2.6)
        y = rnd.uniform(-12.9, -10.1)
        z0 = FLOOR + rnd.uniform(3.0, 5.0)
        w = rnd.uniform(0.05, 0.13)
        ob = K.sheet('letter_%02d' % i, (x, y, z0), w, w * rnd.uniform(0.85, 1.25),
                     rot=(rnd.uniform(-0.9, 0.9), rnd.uniform(-0.9, 0.9),
                          rnd.uniform(0, 6.28)),
                     color=INK, strength=0.0, seed=i + 61)
        # fall, drifting sideways, staggered start
        f0 = 1 + int(rnd.uniform(0.0, 0.55) * N)
        f1 = min(N, f0 + int(N * rnd.uniform(0.35, 0.6)))
        if f1 <= f0 + 2:
            continue
        K.drift(ob, f0, f1,
                dloc=(rnd.uniform(-0.5, 0.5), rnd.uniform(-0.2, 0.2),
                      -(z0 - FLOOR - rnd.uniform(0.0, 0.6))),
                drot=(rnd.uniform(-2.0, 2.0), rnd.uniform(-2.0, 2.0),
                      rnd.uniform(-1.5, 1.5)), loop=False)


def _torn_photo():
    """A torn photo of her, sinking past the page."""
    p = os.path.join(MV, 'mv', 'assets', 'char', 'maid_card.png')
    try:
        front, mat, back = C.paper_cutout(p, height=0.26, loc=(-1.05, -11.25, FLOOR + 1.15),
                                          name='torn_photo', emission_strength=0.04,
                                          rim=0.003)
        for ob in (front, back):
            ob.rotation_euler = (0.0, math.radians(-18.0), math.radians(15.0))
            try:
                ob.visible_shadow = False
            except Exception:
                pass
        for ob in (front, back):
            K.obj_keys(ob, [(1, (ob.location[0], ob.location[1], FLOOR + 1.45)),
                            (int(N * 0.55), (ob.location[0], ob.location[1], FLOOR + 0.80)),
                            (int(N * 0.85), (ob.location[0], ob.location[1], FLOOR + 0.05))],
                       prop='location')
            K.ease(ob)
    except Exception:
        pass


def _scatter():
    """Loose archive paper on the floor of the archive."""
    rnd = random.Random(31)
    for i in range(18):
        x = rnd.uniform(-3.4, 3.4)
        y = rnd.uniform(-12.6, -8.6)
        w = rnd.uniform(0.25, 0.55)
        ob = K.sheet('loose_%02d' % i, (x, y, FLOOR + 0.012), w, w * rnd.uniform(0.6, 0.95),
                     rot=(rnd.uniform(-0.04, 0.04), rnd.uniform(-0.04, 0.04),
                          rnd.uniform(0, 6.28)),
                     color=(0.80, 0.76, 0.66), strength=0.02, seed=i + 71)
        K.drift(ob, 1, N, dloc=(rnd.uniform(-0.1, 0.1), 0.0, 0.0),
                drot=(0.0, 0.0, rnd.uniform(-0.10, 0.10)), loop=True)


def _lights():
    # --- KEY: hard warm theatre key from high front-left, the only strong shadow
    key = C.light('type_key', 'SPOT', loc=(-3.10, -6.40, FLOOR + 4.80), energy=1900,
                  color=(1.0, 0.70, 0.44), size=0.30, angle=math.radians(30))
    C.look_at(key, (0.0, -11.60, FLOOR + 1.15))
    key.data.volume_factor = 2.6
    # --- cool window beam out of the shoji grid
    win = C.light('type_window', 'AREA', loc=(-3.40, -9.40, FLOOR + 2.80), energy=620,
                  color=(0.52, 0.76, 1.0), size=2.60)
    C.look_at(win, (0.0, -12.40, FLOOR + 1.10))
    win.data.use_shadow = False
    win.data.volume_factor = 1.4
    # --- cyan kicker from behind: separates the paper edge from the dark
    rim = C.light('type_rim', 'AREA', loc=(1.40, -16.20, FLOOR + 2.90), energy=640,
                  color=CYAN, size=2.00)
    C.look_at(rim, (0.0, -11.60, FLOOR + 1.45))
    # --- warm pool on the hanging page so the type reads
    pl = C.light('type_pagelight', 'AREA', loc=(PAGE_X, PAGE_Y + 2.6, FLOOR + 2.7),
                 energy=170, color=(1.0, 0.84, 0.62), size=3.2)
    C.look_at(pl, (PAGE_X, PAGE_Y, FLOOR + 1.35))
    pl.data.use_shadow = False
    # --- warm bounce card off the floor in front of her
    bounce = C.light('type_bounce', 'AREA', loc=(0.0, -8.80, FLOOR + 0.45), energy=125,
                     color=(1.0, 0.66, 0.40), size=3.0)
    C.look_at(bounce, (0.0, -11.40, FLOOR + 1.20))
    bounce.data.use_shadow = False
    # --- practicals: a work lamp on the long table + its glowing bulb
    lamp = C.light('type_lamp', 'POINT', loc=(3.35, -12.60, FLOOR + 1.62), energy=90,
                   color=(1.0, 0.62, 0.32), size=0.16)
    lamp.data.use_shadow = False
    lamp.data.volume_factor = 1.3
    K.glow_orb('type_lamp_bulb', (3.35, -12.60, FLOOR + 1.57), radius=0.05,
               color=(1.0, 0.66, 0.36), strength=10.0)


def _dress():
    """Denser archive: extra box stacks along the back wall + two practical bulbs."""
    box_m = C.paper('m_archive_box', base=(0.58, 0.54, 0.46), rough=0.9)
    gold_m = C.paper('m_archive_gold', base=(0.64, 0.52, 0.28), rough=0.62)
    rnd = random.Random(97)
    for i in range(10):
        x = rnd.uniform(-4.20, 4.20)
        y = rnd.uniform(-16.80, -13.40)
        s = rnd.uniform(0.28, 0.70)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y, FLOOR + s * 0.5 + 0.01))
        ob = bpy.context.object
        ob.name = 'archive_box_%02d' % i
        ob.scale = (s * 1.55, s * 1.10, s)
        ob.rotation_euler = (0.0, 0.0, rnd.uniform(-0.12, 0.12))
        ob.data.materials.append(gold_m if i % 3 == 0 else box_m)
        try:
            ob.visible_shadow = False
        except Exception:
            pass
    thread_m = C.paper('m_bulb_thread', base=(0.50, 0.46, 0.38), rough=0.9)
    for i, (x, y) in enumerate(((-2.20, -13.40), (2.90, -14.60))):
        bpy.ops.mesh.primitive_cylinder_add(vertices=5, radius=0.004, depth=2.40,
                                           location=(x, y, FLOOR + 3.90))
        th = bpy.context.object
        th.name = 'bulb_thread_%d' % i
        th.data.materials.append(thread_m)
        th.visible_shadow = False
        K.glow_orb('hang_bulb_%d' % i, (x, y, FLOOR + 2.72), radius=0.055,
                   color=(1.0, 0.64, 0.34), strength=9.0)


def build():
    K.begin(fog_density=0.012,
            fog_color=(0.030, 0.055, 0.080), ambient=(0.014, 0.021, 0.030),
            exposure=-0.06)

    # cheap volumetrics (s10 is the heaviest shot in the queue)
    try:
        bpy.context.scene.eevee.volumetric_samples = 24
        bpy.context.scene.eevee.volumetric_start = 0.05
    except Exception:
        pass

    try:
        # s10 uses its own dark archive floor; skip the theatre planks (their top is
        # coplanar with the slab at FLOOR and made the floor flicker with z-fighting).
        T.theatre(seed=3, floor=False)
    except Exception:
        pass
    K.floor_slab('type_floor', z=FLOOR, size=120.0, color=(0.055, 0.062, 0.075))
    _dress()

    _page()
    _scatter()
    _falling_letters()
    _torn_photo()
    _lights()

    # ---- her
    ctrl = K.char_actor('exasperated', HER, height=1.75, face=HER_FACE, bend=1.5,
                        glow_strength=0.9)
    K.char_expr(ctrl, [(1, 'exasperated', 1.5, 0.0),
                       (620, 'confused', 1.8, 0.8),
                       (1120, 'frightened', 2.4, 1.0),
                       (N, 'frightened', 2.0, 0.0)])
    # she sinks while typing: feet drop below the floor slab, card shrinks a touch
    K.char_pose(ctrl, [(1, HER, (1.5, 0.0), 1.0),
                       (900, (HER[0], HER[1], HER[2] - 0.18), (1.8, 0.0), 1.0),
                       (N, (HER[0], HER[1], HER[2] - 0.52), (2.2, 0.0), 0.94)])
    C.dust('type_dust', count=420, extent=(8.0, 8.0, 5.0),
           center=(0.0, -11.6, FLOOR + 2.0), size=0.010,
           color=(0.86, 0.90, 1.0), strength=0.9)

    # ---- camera: frontal flat 35 mm, slow push in as she sinks
    _cam = K.cam_path('cam_s10', [
        (1, (-0.35, -5.35, FLOOR + 1.62), (0.00, -12.60, FLOOR + 1.32), 32, FS),
        (420, (0.10, -5.85, FLOOR + 1.44), (-0.05, -12.40, FLOOR + 1.16), 35, FS),
        (980, (0.55, -6.20, FLOOR + 1.30), (0.05, -12.20, FLOOR + 1.00), 37, FS),
        (N, (0.95, -6.55, FLOOR + 1.10), (0.10, -12.10, FLOOR + 0.90), 39, FS),
    ])
    K.add_handheld(_cam, amp=0.010, scale=2.3, seed=10, rot_amp=0.0030)
