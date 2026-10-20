"""s05 - RECALL: the museum hall  (quality pass v2).

Two archive specimens (TABLE -> EGGPLANT) stand on white paper plinths under cold
scan shafts.  She walks between them; each one is scanned while she watches.

v2 premium look: a deep archive aisle built from receding shelf walls stuffed with
files, a colonnade + distant wall, ceiling rigging with hanging index tags, three
small side exhibits on dim pedestals with practical pools, paper floor debris, a
polished floor with sheen, and a proper film rig: hard warm key / cold rim /
visible volumetric shaft on the hero specimen, warm bounce, dust.

The hall (`_build_hall`), the rig (`_hall_lights`), `_shaft`, `_energy`, `_place`
and `_label_light` are shared with shot_s07.py / shot_s08.py.
"""
import bpy, math, os, random, sys

MV = r'D:\Code\Code MV\new-word.search(you)'
sys.path.insert(0, os.path.join(MV, 'mv', 'build'))
import shotkit as K
import core as C
import geo as G
import world_theater as T
import stage as S
import specimens as SP

FRAMES = (40.86, 68.17)
FLOOR = K.FLOOR
N = int(round(FRAMES[1] * K.FPS)) - int(round(FRAMES[0] * K.FPS))

CHAR = (0.55, -11.20, FLOOR)
TABLE = (-3.15, -13.90)
EGG = (2.85, -14.10)


# ---------------------------------------------------------------------------
# materials
# ---------------------------------------------------------------------------
def _mats():
    m = {}
    m['ink'] = C._principled('m_hall_ink', (0.020, 0.027, 0.035), rough=0.88)
    m['ink2'] = C._principled('m_hall_ink2', (0.031, 0.040, 0.050), rough=0.80)
    m['ink3'] = C._principled('m_hall_ink3', (0.044, 0.056, 0.068), rough=0.72)
    m['plank'] = C._principled('m_hall_plank', (0.058, 0.052, 0.042), rough=0.70)
    m['gold'] = C._principled('m_hall_gold', (0.34, 0.22, 0.09), rough=0.32, metal=0.55)
    m['paper'] = C.paper('m_hall_paper', base=(0.60, 0.56, 0.48), rough=0.86, fiber=0.8)
    m['paperw'] = C.paper('m_hall_paperw', base=(0.66, 0.58, 0.44), rough=0.88, fiber=0.6)
    m['strip'] = C.emissive('m_hall_strip', (0.10, 0.34, 0.52), 0.42)
    m['strip2'] = C.emissive('m_hall_strip2', (0.22, 0.50, 0.74), 0.62)
    m['floor'] = C._principled('m_hall_floor', (0.012, 0.018, 0.023),
                               rough=0.30, metal=0.18)
    return m


# ---------------------------------------------------------------------------
# shared hall set
# ---------------------------------------------------------------------------
def _shelf_wall(m, side, seed=7):
    """One long receding archive shelf wall: modules, shelves, files, glow strips."""
    tag = 'L' if side < 0 else 'R'
    g = G.Geo('hall_shelf_' + tag)
    gl = G.Geo('hall_shelf_glow_' + tag)
    for i in range(11):
        y = -7.3 - i * 2.10
        x = side * (5.05 + 0.055 * i)
        h = 4.55 + (0.28 if i % 3 == 0 else 0.0)
        # module back + two side uprights
        g.box((1.78, 0.07, h), (x + side * 0.20, y, FLOOR + h * 0.5), mat=m['ink'])
        for sx in (-0.82, 0.82):
            g.box((0.075, 0.78, h), (x + sx, y, FLOOR + h * 0.5), mat=m['ink2'])
        # four shelf boards + varied files
        rnd = random.Random(seed * 1000 + i * 17 + (0 if side < 0 else 1))
        for k in range(4):
            z = FLOOR + 0.58 + k * 1.06
            g.box((1.66, 0.74, 0.045), (x, y, z), mat=m['ink3'])
            gl.box((1.60, 0.016, 0.012), (x, y + 0.365, z - 0.028),
                   mat=m['strip'])
            for j in range(3 + (k % 2)):
                bw = rnd.uniform(0.13, 0.40)
                bh = rnd.uniform(0.15, 0.46)
                bd = rnd.uniform(0.22, 0.56)
                g.box((bw, bd, bh),
                      (x + rnd.uniform(-0.56, 0.56), y + rnd.uniform(-0.06, 0.10),
                       z + 0.024 + bh * 0.5),
                      mat=(m['ink'] if j % 2 else m['plank']))
        # a thin cyan catalog strip on every second module
        if i % 2 == 0:
            gl.box((1.62, 0.02, 0.014), (x, y + 0.60, FLOOR + 0.10), mat=m['strip'])
        if i % 5 == 2:
            gl.box((1.58, 0.02, 0.010), (x, y + 0.60, FLOOR + 2.62), mat=m['strip2'])
    g.build()
    gl.build()


def _colonnade(m):
    """Six faint rear columns + lintel: pushes the hall back into the fog."""
    g = G.Geo('hall_colonnade')
    gl = G.Geo('hall_colonnade_glow')
    for side in (-1.0, 1.0):
        for k, yy in enumerate((-22.4, -25.0, -27.6)):
            x = side * (2.55 + k * 2.35)
            g.box((0.68, 0.68, 6.05), (x, yy, FLOOR + 3.02), mat=m['ink'])
            g.box((0.86, 0.86, 0.24), (x, yy, FLOOR + 0.12), mat=m['ink2'])
            g.box((0.82, 0.82, 0.20), (x, yy, FLOOR + 5.92), mat=m['ink2'])
            gl.box((0.020, 0.020, 5.30), (x + side * 0.35, yy - 0.35,
                                         FLOOR + 3.0), mat=m['strip'])
    g.box((11.4, 0.42, 0.55), (0.0, -24.2, FLOOR + 6.22), mat=m['ink'])
    g.box((11.2, 0.10, 0.07), (0.0, -24.0, FLOOR + 5.94), mat=m['gold'])
    g.build()
    gl.build()


def _rigging(m):
    """Overhead pipes + thin cables + a few hanging index tags = archive depth."""
    g = G.Geo('hall_rigging')
    cards = G.Geo('hall_tags')
    pins = G.Geo('hall_tag_pins')
    for y, zz in ((-9.0, FLOOR + 5.92), (-13.6, FLOOR + 6.06), (-18.4, FLOOR + 6.22)):
        g.box((10.6, 0.075, 0.075), (0.0, y, zz), mat=m['ink2'])
    rnd = random.Random(31)
    for i in range(6):
        x = -4.2 + i * 1.68
        y = -9.6 - (i % 3) * 3.4
        top = FLOOR + 5.95
        ln = rnd.uniform(1.7, 2.6)
        g.box((0.010, 0.010, ln), (x, y, top - ln * 0.5), mat=m['ink3'])
    for i in range(13):
        x = rnd.uniform(-4.5, 4.5)
        y = rnd.uniform(-10.8, -17.6)
        z = FLOOR + rnd.uniform(3.30, 4.85)
        w = rnd.uniform(0.10, 0.20)
        h = w * rnd.uniform(1.15, 1.55)
        cards.plane(1.0, (x, y, z), (math.radians(90), 0, rnd.uniform(0, 6.28)),
                    m['paper'] if i % 3 else m['paperw'], sx=w, sy=h)
        pins.cylinder(0.0045, 1.6, (x, y, z + h * 0.5 + 0.8), (0, 0, 0),
                      m['ink3'], seg=4)
    ob = cards.build()
    ob.visible_shadow = False
    p = pins.build()
    p.visible_shadow = False
    # overhead practical rig lamps (bulb + shade)
    em = C.emissive('m_hall_bulb', (1.0, 0.66, 0.34), 14.0)
    for i, (x, y) in enumerate(((-3.55, -12.4), (3.45, -15.2))):
        g.box((0.34, 0.34, 0.06), (x, y, FLOOR + 4.62), mat=m['plank'])
        g.box((0.045, 0.045, 0.55), (x, y, FLOOR + 4.35), mat=m['ink3'])
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.075,
                                              location=(x, y, FLOOR + 4.06))
        b = bpy.context.object
        b.name = 'hall_bulb_%d' % i
        b.data.materials.append(em)
        b.visible_shadow = False
    g.build()


def _floor_debris(m, seed=17):
    """A few paper sheets on the polished floor: quiet foreground texture."""
    g = G.Geo('hall_debris')
    rnd = random.Random(seed)
    for i in range(11):
        x = rnd.uniform(-4.6, 4.6)
        y = rnd.uniform(-9.4, -17.2)
        w = rnd.uniform(0.16, 0.34)
        g.plane(1.0, (x, y, FLOOR + 0.012 + i * 0.0002),
                (rnd.uniform(-0.03, 0.03), rnd.uniform(-0.03, 0.03),
                 rnd.uniform(0, 6.28)),
                m['paperw'] if i % 2 else m['paper'], sx=w, sy=w * rnd.uniform(0.7, 1.4))
    ob = g.build()
    ob.visible_shadow = False


def _side_exhibit(builder, xy, scale=0.62, rotz=0.0, style=None, h=0.58):
    """Small dim exhibit on a rear pedestal (silhouette in the dark)."""
    T.plinth(xy[0], xy[1], z=FLOOR, h=h, w=0.62, d=0.62, gold=False, label=False)
    st = dict(plinth=False, label=False, point_count=160, wire_strength=1.35,
              wire_ratio=0.42, wire_thickness=0.0026, point_strength=2.2,
              shell_alpha=0.04)
    if style:
        st.update(style)
    coll = builder(location=(xy[0], xy[1], FLOOR + h), rotation=(0, 0, math.radians(rotz)),
                   style=st, scale=scale)
    return coll


def _build_hall(seed=5, dust=True):
    """Cold paper-archive hall v2. Specimens bring their own paper plinths."""
    m = _mats()
    C.plane('hall_floor', size=70.0, loc=(0.0, -14.0, FLOOR), rot=(0, 0, 0),
            mat=m['floor'])
    C.plane('hall_wall', size=46.0, loc=(0.0, -32.0, FLOOR + 6.0),
            rot=(math.radians(90.0), 0.0, 0.0), mat=m['ink'])
    T.distant_archive(y=-30.0, seed=7, rows=3)
    _shelf_wall(m, -1.0, seed)
    _shelf_wall(m, 1.0, seed + 3)
    _colonnade(m)
    _rigging(m)
    _floor_debris(m, seed + 11)
    # three small exhibits receding into the dark
    _side_exhibit(SP.build_tomato_paper, (-5.05, -20.30), scale=0.46, rotz=18.0)
    _side_exhibit(SP.build_bucket, (4.60, -19.10), scale=0.48, rotz=-24.0,
                  style=dict(fill=0.40))
    # paper carp kite hung nose-up from the ceiling rig (reads as a specimen in the dark)
    SP.build_koinobori(color='kimi', label_text='kimi / table_2', length=1.4,
                       location=(-5.30, -18.20, FLOOR + 2.30),
                       rotation=(0.0, math.radians(90.0), math.radians(-8.0)),
                       scale=0.86)
    gk = G.Geo('hall_kite_hang')
    gk.cylinder(0.006, 2.30, (-5.30, -18.20, FLOOR + 4.10), (0, 0, 0),
                m['ink3'], seg=4)
    gk.build()
    if dust:
        C.dust('hall_dust', count=1500, extent=(12.5, 20.0, 9.0),
               center=(0.0, -14.5, FLOOR + 3.3), size=0.005,
               color=(0.58, 0.84, 1.0), strength=2.4)


def _hall_lights():
    """Film rig v2: hard warm key, cold rim, crossing beams, practical pools."""
    key = C.light('her_key', 'SPOT', loc=(-2.70, -7.30, FLOOR + 4.35),
                  energy=6300, color=(1.0, 0.59, 0.31), size=0.20,
                  angle=math.radians(21.0))
    C.look_at(key, (CHAR[0], CHAR[1], FLOOR + 1.15))
    key.data.volume_factor = 1.9
    rim = C.light('her_rim', 'SPOT', loc=(2.55, -16.40, FLOOR + 3.95),
                  energy=7200, color=(0.16, 0.50, 1.0), size=0.16,
                  angle=math.radians(21.0))
    C.look_at(rim, (CHAR[0], CHAR[1], FLOOR + 1.30))
    rim.data.volume_factor = 3.4
    fill = C.light('her_fill', 'AREA', loc=(3.60, -7.20, FLOOR + 3.05),
                   energy=70, color=(0.42, 0.62, 1.0), size=3.0)
    C.look_at(fill, (CHAR[0], CHAR[1], FLOOR + 1.0))
    fill.data.use_shadow = False
    bounce = C.light('bounce', 'AREA', loc=(-2.60, -9.40, FLOOR + 1.70),
                     energy=120, color=(1.0, 0.64, 0.36), size=2.2)
    C.look_at(bounce, (CHAR[0], CHAR[1], FLOOR + 1.45))
    bounce.data.use_shadow = False
    wash = C.light('hall_wash', 'AREA', loc=(0.0, -22.0, FLOOR + 5.2),
                   energy=220, color=(0.30, 0.50, 0.85), size=9.0)
    C.look_at(wash, (0.0, -30.0, FLOOR + 2.5))
    wash.data.use_shadow = False
    beam = C.light('distant_beam', 'SPOT', loc=(0.0, -26.0, FLOOR + 4.40),
                   energy=1200, color=(0.50, 0.72, 1.0), size=1.2,
                   angle=math.radians(52.0))
    C.look_at(beam, (0.0, -13.0, FLOOR + 1.20))
    beam.data.volume_factor = 2.5
    beam.data.use_shadow = False
    # practical pools under the three rear exhibits
    for i, (x, y, z) in enumerate(((-5.05, -20.30, FLOOR + 1.20),
                                   (4.60, -19.10, FLOOR + 1.25),
                                   (-5.30, -18.20, FLOOR + 1.05))):
        L = C.light('practical_pool_%d' % i, 'POINT', loc=(x, y + 0.05, z),
                    energy=(14.0 if i == 0 else 32.0), color=(1.0, 0.60, 0.30),
                    size=0.16)
        L.data.volume_factor = 1.3
        L.data.use_shadow = False
    # two overhead rig bulbs as faint pools
    for i, (x, y) in enumerate(((-3.55, -12.4), (3.45, -15.2))):
        L = C.light('rig_pool_%d' % i, 'POINT', loc=(x, y, FLOOR + 4.06),
                    energy=34.0, color=(1.0, 0.68, 0.38), size=0.10)
        L.data.volume_factor = 1.0
        L.data.use_shadow = False


def _label_light(coll, idx=0, energy=14.0):
    """Small warm museum picture-light grazing a specimen's hanging label card."""
    bpy.context.view_layer.update()
    plate = None
    for ob in coll.all_objects:
        if ob.name.endswith('_label_plate'):
            plate = ob
            break
    if plate is None:
        return None
    loc = plate.matrix_world.translation
    L = C.light('label_light_%d' % idx, 'SPOT',
                loc=(loc.x, loc.y + 0.78, loc.z + 0.30),
                energy=energy, color=(1.0, 0.84, 0.58), size=0.045,
                angle=math.radians(17.0))
    C.look_at(L, (loc.x, loc.y, loc.z))
    L.data.volume_factor = 0.7
    L.data.use_shadow = False
    return L


def _shaft(name, xy, energy=2400.0, angle=24.0):
    """Cold scan shaft falling on a plinth."""
    L = C.light(name, 'SPOT', loc=(xy[0], xy[1] + 0.35, FLOOR + 6.60),
                energy=energy, color=(0.36, 0.70, 1.0), size=0.22,
                angle=math.radians(angle))
    C.look_at(L, (xy[0], xy[1], FLOOR + 0.90))
    L.data.volume_factor = 4.0
    return L


def _energy(L, keys):
    for f, e in keys:
        L.data.energy = float(e)
        L.data.keyframe_insert('energy', frame=f)
    K.ease(L.data)


def _place(builder, xy, rotz=0.0, style=None, scale=None, shadow=True):
    coll = builder(location=(xy[0], xy[1], FLOOR),
                   rotation=(0.0, 0.0, math.radians(rotz)), style=style,
                   scale=scale)
    if shadow:
        S._contact_shadow(xy, sx=1.20, sy=0.90)
    return coll


# ---------------------------------------------------------------------------
def build():
    K.begin(fog_density=0.022, fog_color=(0.009, 0.032, 0.052),
            ambient=(0.005, 0.015, 0.026), exposure=0.24)
    _build_hall()
    _hall_lights()

    tcoll = _place(SP.build_table, TABLE, rotz=-9.0,
                   style=dict(wire_strength=1.5, point_count=470, wire_ratio=0.47,
                              wire_thickness=0.0028, shell_alpha=0.06))
    ecoll = _place(SP.build_eggplant, EGG, rotz=11.0,
                   style=dict(label_side='left', point_count=460, wire_ratio=0.46,
                              wire_thickness=0.0026, shell_alpha=0.06))
    ring_c = "#598fb0"
    SP.animate_scan(tcoll, period=3.4, frame_start=1, frame_end=N, color=ring_c)
    SP.animate_scan(ecoll, period=2.8, frame_start=880, frame_end=N, color=ring_c)
    _label_light(tcoll, 0, 6.0)
    _label_light(ecoll, 1, 6.0)

    t_shaft = _shaft('table_shaft', TABLE, energy=700.0)
    e_shaft = _shaft('egg_shaft', EGG, energy=450.0)
    _energy(t_shaft, [(1, 700), (170, 3100), (640, 3600), (860, 1000), (N, 600)])
    _energy(e_shaft, [(1, 450), (880, 800), (1030, 3100), (1450, 3600), (N, 900)])

    ctrl = K.char_actor('confused', CHAR)
    K.char_expr(ctrl, [
        (1, 'confused', 2.5, 0.0),
        (330, 'shy', 4.0, -1.5),
        (620, 'serious', 2.5, 0.5),
        (900, 'exasperated', 3.0, 2.0),
        (1200, 'cheerful', 3.0, 1.0),
        (1450, 'confused', 2.0, 0.0),
        (N, 'confused', 2.0, 0.0),
    ])
    K.char_pose(ctrl, [
        (1, CHAR, None, None),
        (560, (-0.95, -12.15, FLOOR), None, None),
        (900, (0.10, -11.55, FLOOR), None, None),
        (1180, (0.45, -11.85, FLOOR), None, None),
        (1450, (0.80, -11.45, FLOOR), None, None),
        (N, (0.80, -11.40, FLOOR), None, None),
    ])

    # arc-in establishing -> push to table -> arc across to eggplant -> settle on her
    cam = K.cam_path('cam_s05', [
        (1, (2.55, -5.90, FLOOR + 1.95), (-0.35, -13.60, FLOOR + 1.30), 26, 3.6),
        (240, (2.05, -6.15, FLOOR + 1.88), (-1.05, -13.85, FLOOR + 1.30), 29, 3.3),
        (520, (0.55, -6.60, FLOOR + 1.95), (-2.42, -13.95, FLOOR + 1.16), 34, 3.0),
        (700, (-0.75, -7.10, FLOOR + 1.90), (-2.95, -13.90, FLOOR + 1.10), 40, 2.7),
        (900, (-1.35, -7.65, FLOOR + 1.82), (-2.90, -13.80, FLOOR + 1.06), 45, 2.4),
        (1080, (0.15, -7.95, FLOOR + 1.80), (2.35, -14.05, FLOOR + 1.05), 42, 2.5),
        (1300, (0.95, -8.10, FLOOR + 1.76), (2.95, -14.10, FLOOR + 1.05), 46, 2.3),
        (1390, (1.10, -8.15, FLOOR + 1.74), (0.88, -11.75, FLOOR + 1.36), 50, 2.1),
        (1470, (1.22, -8.28, FLOOR + 1.72), (0.84, -11.62, FLOOR + 1.33), 52, 2.1),
        (N, (1.32, -8.40, FLOOR + 1.70), (0.80, -11.52, FLOOR + 1.31), 54, 2.1),
    ])
    K.add_handheld(cam, amp=0.014, scale=1.15, seed=5)
    return {'table': tcoll, 'eggplant': ecoll}
