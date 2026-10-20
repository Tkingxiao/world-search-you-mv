"""look2.py - quality-pass set dressing for the paper theatre (v2 look).

Adds the things a real stage has: a proscenium arch, overhead rigging with ropes
and sandbags, wing clutter (crates, ladders, leaning flats), a cluster of hanging
tags, two practical work lamps with glowing shades, and taped stage marks.
Everything is paper / ink materials so it stays in the same visual language.
"""
import bpy
import math
import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
for _m in ('core', 'world', 'geo', 'world_theater'):
    sys.modules.pop(_m, None)

import core as C
import geo as G
import world_theater as T

FLOOR = -6.0


def proscenium():
    """Heavy paper proscenium: two layered side towers + lintel + hanging valance."""
    M = T._mats()
    g = G.Geo('proscenium')
    for side in (-1, 1):
        x = side * 5.05
        # main column
        g.box((0.62, 0.55, 5.9), (x, -7.15, FLOOR + 2.95), (0, 0, 0), M['ink'])
        # inner pilaster, lighter face
        g.box((0.30, 0.30, 5.55), (x - side * 0.34, -6.92, FLOOR + 2.80), (0, 0, 0), M['ink2'])
        # gold reveal strips
        g.box((0.035, 0.045, 5.55), (x - side * 0.50, -6.90, FLOOR + 2.80), (0, 0, 0), M['gold'])
        g.box((0.035, 0.045, 5.55), (x - side * 0.18, -6.90, FLOOR + 2.80), (0, 0, 0), M['gold'])
        # base block
        g.box((0.86, 0.80, 0.42), (x, -7.05, FLOOR + 0.21), (0, 0, 0), M['plank_dark'])
        # capital
        g.box((0.80, 0.72, 0.26), (x, -7.05, FLOOR + 5.62), (0, 0, 0), M['plank_dark'])
        # little stacked ring detail
        for k in range(3):
            g.cylinder(0.10, 0.05, (x, -6.88, FLOOR + 1.30 + k * 0.16), (math.radians(90), 0, 0), M['gold'], seg=10)
    # lintel across
    g.box((10.9, 0.72, 0.70), (0.0, -7.10, FLOOR + 6.10), (0, 0, 0), M['ink'])
    g.box((10.7, 0.12, 0.10), (0.0, -6.76, FLOOR + 5.80), (0, 0, 0), M['gold'])
    # hanging valance: strips of dark paper with a sag
    rnd = random.Random(21)
    for i in range(15):
        x = -4.9 + i * (9.8 / 14.0)
        droop = 0.30 + 0.42 * math.sin((i / 14.0) * math.pi) ** 1.4
        h = 0.55 + rnd.uniform(-0.06, 0.10)
        g.plane(0.66, (x, -6.80, FLOOR + 5.78 - h / 2 - droop * 0.15),
                (math.radians(90), 0, 0), M['ink'] if i % 2 else M['ink2'],
                sx=1.0, sy=h)
    ob = g.build()
    return ob


def rigging():
    """Overhead pipes, hanging ropes, pulleys and sandbag counterweights."""
    M = T._mats()
    g = G.Geo('rigging')
    for y, zz in ((-8.6, FLOOR + 5.55), (-13.4, FLOOR + 5.75), (-18.2, FLOOR + 5.95)):
        g.box((9.6, 0.09, 0.09), (0.0, y, zz), (0, 0, 0), M['ink2'])
    rnd = random.Random(5)
    made = []
    rope_xs = [(-3.4, -8.9), (-1.4, -8.7), (1.3, -8.8), (3.5, -8.6),
               (-2.2, -13.6), (2.3, -13.2), (-3.9, -18.5), (3.8, -18.0)]
    for i, (x, y) in enumerate(rope_xs):
        top = FLOOR + 5.55 + (0.2 if y < -12 else 0.0) + (0.4 if y < -17 else 0.0)
        ln = top - (FLOOR + 0.55 + rnd.uniform(0.0, 1.05))
        # rope
        bpy.ops.mesh.primitive_cylinder_add(vertices=5, radius=0.006, depth=ln,
                                           location=(x, y, top - ln / 2))
        o = bpy.context.object
        o.name = 'rope_%d' % i
        o.data.materials.append(M['ink2'])
        o.visible_shadow = False
        made.append(o)
        # pulley wheel
        g.cylinder(0.045, 0.030, (x, y, top), (0, math.radians(90), 0), M['plank_dark'], seg=10)
        # sandbag at the end
        if rnd.random() < 0.6:
            g.box((0.16, 0.10, 0.24), (x, y, FLOOR + 0.62 + rnd.uniform(-0.1, 0.1)),
                  (rnd.uniform(-0.1, 0.1), 0, rnd.uniform(-0.2, 0.2)), M['plank_dark'])
    ob = g.build()
    for o in made:
        o.parent = ob
    return ob


def wing_clutter():
    """Crates, leaning flats, a ladder, coiled cable: gives the wings weight."""
    M = T._mats()
    g = G.Geo('wing_clutter')
    rnd = random.Random(9)
    # crates left and right, stacked at different depths
    for side in (-1, 1):
        for i in range(4):
            x = side * (4.30 + rnd.uniform(-0.18, 0.18))
            y = -8.6 - i * 1.15 + rnd.uniform(-0.2, 0.2)
            sz = rnd.uniform(0.42, 0.62)
            g.box((sz, sz * 0.9, sz * 0.75), (x, y, FLOOR + sz * 0.375), (0, 0, rnd.uniform(-0.2, 0.2)),
                  M['plank_dark'] if i % 2 else M['ink2'])
            if rnd.random() < 0.55:
                g.box((sz * 0.95, 0.03, 0.05), (x, y - sz * 0.46, FLOOR + sz * 0.62), (0, 0, 0), M['gold'])
        # leaning flats
        for i in range(3):
            x = side * (4.55 + rnd.uniform(-0.1, 0.1))
            y = -11.5 - i * 0.9
            g.plane(1.05, (x, y, FLOOR + 0.85), (math.radians(78), 0, side * math.radians(12)),
                    M['ink'] if i % 2 else M['ink3'], sx=1.0, sy=1.9)
    # ladder on the right
    for xo in (-0.16, 0.16):
        g.box((0.045, 0.045, 2.6), (4.35 + xo, -13.9, FLOOR + 1.30), (0, 0, 0), M['plank_dark'])
    for k in range(7):
        g.box((0.36, 0.035, 0.035), (4.35, -13.9, FLOOR + 0.28 + k * 0.36), (0, 0, 0), M['plank_dark'])
    # coiled cable on the floor
    for k in range(3):
        g.cylinder(0.30 + k * 0.05, 0.020, (-3.9 + k * 0.02, -10.4, FLOOR + 0.035), (0, 0, 0), M['ink2'], seg=14)
    ob = g.build()
    return ob


def hanging_tags(seed=13, n=11):
    """Cluster of small hanging paper tags above / around the stage."""
    M = T._mats()
    rnd = random.Random(seed)
    cards = G.Geo('hanging_tags')
    pins = G.Geo('tag_pins')
    for i in range(n):
        x = rnd.uniform(-4.6, 4.6)
        y = rnd.uniform(-9.2, -18.5)
        z = FLOOR + rnd.uniform(4.35, 5.25)
        w = rnd.uniform(0.085, 0.15)
        h = w * rnd.uniform(1.15, 1.5)
        cards.plane(1.0, (x, y, z), (math.radians(90), 0, rnd.uniform(0, 6.28)),
                    M['paper_warm'] if i % 3 else M['paper'], sx=w, sy=h)
        pins.cylinder(0.004, z - (FLOOR + 4.9), (x, y, (z + FLOOR + 5.3) / 2), (0, 0, 0), M['ink2'], seg=4)
    ob = cards.build()
    ob.visible_shadow = False
    p = pins.build()
    p.visible_shadow = False
    return ob, p


def practical_lamps():
    """Two caged work lamps at the stage edges: shade + glowing bulb + warm pool."""
    M = T._mats()
    g = G.Geo('practicals')
    em = C.emissive('m_practical_bulb', (1.0, 0.62, 0.30), 22.0)
    lamps = []
    for i, (x, y) in enumerate(((-4.15, -9.6), (4.10, -10.9))):
        # little table
        g.box((0.40, 0.40, 0.05), (x, y, FLOOR + 0.94), (0, 0, 0), M['plank_dark'])
        g.box((0.05, 0.05, 0.92), (x, y, FLOOR + 0.46), (0, 0, 0), M['ink2'])
        # lamp stem
        g.cylinder(0.018, 0.40, (x, y, FLOOR + 1.16), (0, 0, 0), M['ink2'], seg=8)
        # shade
        g.cylinder(0.015, 0.16, (x, y, FLOOR + 1.48), (0, 0, 0), M['gold'], seg=10)
        # glowing bulb
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.045,
                                              location=(x, y, FLOOR + 1.40))
        o = bpy.context.object
        o.name = 'practical_bulb_%d' % i
        o.data.materials.append(em)
        o.visible_shadow = False
        lamps.append(o)
        L = C.light('practical_%d' % i, 'POINT', loc=(x, y, FLOOR + 1.44), energy=70.0,
                    color=(1.0, 0.60, 0.30), size=0.10)
        L.data.volume_factor = 1.2
        L.data.use_shadow = False
    ob = g.build()
    return ob, lamps


def stage_marks():
    """Two crossed strips of gold tape marking the playing area, plus corner wedges."""
    M = T._mats()
    g = G.Geo('stage_marks')
    x, y = 0.55, -11.2
    for ang in (math.radians(90), 0.0):
        g.box((0.86, 0.024, 0.004), (x, y, FLOOR + 0.006), (0, 0, ang), M['gold'])
    # little corner wedges in front of the plinths
    for dx in (-1.6, 1.6):
        g.box((0.06, 0.30, 0.004), (x + dx, y + 0.9, FLOOR + 0.006), (0, 0, 0), M['gold'])
    ob = g.build()
    ob.visible_shadow = False
    return ob


def backdrop_detail():
    """Extra depth behind the shoji window: distant paper panels + a faint door frame."""
    M = T._mats()
    g = G.Geo('backdrop_detail')
    for side in (-1, 1):
        for k in range(3):
            x = side * (5.4 + k * 2.3)
            g.box((1.35, 0.06, 4.6), (x, -21.3 - k * 0.15, FLOOR + 2.3), (0, 0, 0), M['ink3'])
            g.box((0.90, 0.03, 3.9), (x, -21.24 - k * 0.15, FLOOR + 2.1), (0, 0, 0), M['ink2'])
    # faint far door frame
    g.box((1.9, 0.08, 0.10), (-8.6, -24.0, FLOOR + 2.35), (0, 0, 0), M['ink2'])
    g.box((0.10, 0.08, 2.5), (-9.52, -24.0, FLOOR + 1.15), (0, 0, 0), M['ink2'])
    g.box((0.10, 0.08, 2.5), (-7.68, -24.0, FLOOR + 1.15), (0, 0, 0), M['ink2'])
    return g.build()


def dress_all():
    """Add every v2 set element. Returns a dict."""
    out = {}
    out['proscenium'] = proscenium()
    out['rigging'] = rigging()
    out['clutter'] = wing_clutter()
    out['tags'], out['tag_pins'] = hanging_tags()
    out['practical'], out['practical_bulbs'] = practical_lamps()
    out['marks'] = stage_marks()
    out['backdrop_detail'] = backdrop_detail()
    return out
