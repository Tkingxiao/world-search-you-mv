"""s02 - PROLOGUE / dive: the camera falls through the dark fly tower, past drifting
memory slips and hanging lanterns, down toward the glowing index page standing on the stage."""
import bpy, math, os, sys, random

MV = r'D:\Code\Code MV\new-word.search(you)'
sys.path.insert(0, os.path.join(MV, 'mv', 'build'))
import shotkit as K
import core as C
import world_theater as T
import geo as G

FRAMES = (6.0, 14.36)
FLOOR = K.FLOOR
N = 502

NAMES = ['first_hello.txt', 'typo_you_made.txt', 'laugh_0314.txt', 'your_cat.txt',
         'weather.txt', 'goodnight.txt', 'see_you.txt', 'last_msg.txt']


def _index_page(loc):
    """Dark paper page standing on the stage with glowing memory index."""
    m = C.paper('m_index_page', base=(0.010, 0.011, 0.014), rough=0.95)
    bsdf = C._bsdf(m.node_tree)
    bsdf.inputs['Emission Strength'].default_value = 0.0
    pg = C.plane('index_page', size=1.0, loc=loc,
                 rot=(math.radians(90), 0, math.pi), mat=m)
    pg.scale = (2.35, 3.05, 1.0)
    pg.visible_shadow = False

    ink = C.emissive('m_index_ink', (0.72, 0.88, 0.78), 8.0)
    lines = ['~/memory/you/'] + NAMES
    z0 = loc[2] + 1.22
    for i, txt in enumerate(lines):
        ob = C.text_obj('idx_%02d' % i, txt, size=0.125,
                        loc=(loc[0] + 0.96, loc[1] + 0.05, z0 - i * 0.275),
                        font='C:/Windows/Fonts/consola.ttf', mat=ink)
        K.face_plus_y(ob)
    return pg


def _name_slips():
    """Small paper slips, each carrying one memory filename, drifting in the shaft."""
    rnd = random.Random(11)
    m = C.paper('m_slip', base=(0.085, 0.080, 0.068), rough=0.9)
    ink = C.emissive('m_slip_ink', (0.86, 0.82, 0.64), 6.0)
    slips = []
    for i, name in enumerate(NAMES):
        ang = rnd.uniform(0, 6.28)
        rad = rnd.uniform(1.6, 3.1)
        x = 0.5 + math.cos(ang) * rad
        y = min(-9.2 + math.sin(ang) * rad * 0.55, -6.9)
        z = FLOOR + 2.2 + i * 0.55 + rnd.uniform(-0.2, 0.2)
        card = C.plane('slip_%d' % i, size=1.0, loc=(x, y, z),
                       rot=(math.radians(90), 0, math.pi + rnd.uniform(-0.35, 0.35)), mat=m)
        card.scale = (0.52, 0.20, 1.0)
        card.visible_shadow = False
        txt = C.text_obj('slip_txt_%d' % i, name, size=0.050,
                         loc=(x + 0.22, y + 0.012, z + 0.062),
                         font='C:/Windows/Fonts/consola.ttf', mat=ink)
        K.face_plus_y(txt)
        slips.append((card, txt, rnd.uniform(0.5, 1.1), rnd.uniform(0.2, 1.0)))
    return slips


def build():
    K.begin(fog_density=0.050, fog_color=(0.006, 0.026, 0.048),
            ambient=(0.004, 0.012, 0.022), exposure=0.30)
    T.theatre(seed=3)
    L = C.light('fall_shaft', 'SPOT', loc=(0.2, -7.4, FLOOR + 13.5), energy=2600,
                color=(0.40, 0.68, 1.0), size=0.5, angle=math.radians(30))
    C.look_at(L, (0.35, -10.6, FLOOR))
    L.data.volume_factor = 5.0

    _index_page((0.30, -11.4, FLOOR + 1.55))
    back = C.light('page_back', 'AREA', loc=(0.30, -13.6, FLOOR + 2.3), energy=120,
                   color=(0.80, 0.88, 1.0), size=2.6)
    C.look_at(back, (0.30, -11.2, FLOOR + 2.3))

    # drifting name slips: descend slowly, sway
    for (card, txt, spd, ph) in _name_slips():
        for f, dz in ((1, 0.0), (N, -1.5 * spd)):
            card.location = (card.location.x, card.location.y, FLOOR + 2.0 + dz + ph * 2.4)
            txt.location = (txt.location.x, txt.location.y, FLOOR + 2.0 + dz + ph * 2.4 + 0.075)
            card.keyframe_insert('location', frame=f)
            txt.keyframe_insert('location', frame=f)
        card.rotation_euler = (math.radians(90), 0, math.pi)
        card.keyframe_insert('rotation_euler', frame=1)
        card.rotation_euler = (math.radians(90), 0, math.pi + 0.55)
        card.keyframe_insert('rotation_euler', frame=N)
        K.ease(card)
        K.ease(txt)

    # loose sheets sinking
    rnd = random.Random(21)
    g = G.Geo('sink_sheets')
    em = C.emissive('m_sink', (0.44, 0.38, 0.28), 0.3)
    for i in range(26):
        x = rnd.uniform(-3.4, 3.4)
        y = rnd.uniform(-14.0, -4.6)
        z = FLOOR + rnd.uniform(0.8, 8.0)
        w = rnd.uniform(0.12, 0.32)
        g.plane(1.0, (x, y, z),
                (rnd.uniform(-0.9, 0.9), rnd.uniform(-1.2, 1.2), rnd.uniform(0, 6.28)),
                em, sx=w, sy=w * rnd.uniform(0.6, 1.1))
    ss = g.build()
    ss.visible_shadow = False
    ss.keyframe_insert('location', frame=1)
    ss.location = (0, 0, 1.0)
    ss.keyframe_insert('location', frame=N)
    K.ease(ss)

    K.cam_path('cam_s02', [
        (1, (1.85, -2.9, FLOOR + 9.6), (0.25, -10.8, FLOOR + 1.3), 22, 5.6),
        (170, (1.15, -3.5, FLOOR + 6.4), (0.35, -10.9, FLOOR + 1.3), 25, 4.5),
        (340, (0.82, -3.9, FLOOR + 3.3), (0.45, -11.0, FLOOR + 1.3), 29, 3.5),
        (N, (0.70, -4.4, FLOOR + 1.65), (0.55, -11.2, FLOOR + 1.35), 35, 2.8),
    ])
