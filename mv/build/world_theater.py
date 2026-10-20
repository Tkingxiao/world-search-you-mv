"""world_theater.py - "paper puppet theatre" sets for the MV.

Design language (locked):
  * everything on stage is folded / cut paper; silhouettes are ink-dark
  * light comes from practicals (footlights, paper lanterns) + one cold shaft from above
  * the character is a paper cut-out puppet on visible threads
  * the world outside the stage is a sunken archive: layered silhouettes, glowing water
Floor is z = -6.0 everywhere.
"""
import bpy, bmesh, math, random
import core as C
import geo as G
from mathutils import Vector, Euler

FLOOR = -6.0


# --------------------------------------------------------------------------- materials
def _mats():
    return dict(
        plank=C.paper('m_plank', base=(0.175, 0.150, 0.120), rough=0.85),
        plank_dark=C.paper('m_plank_dark', base=(0.040, 0.036, 0.030), rough=0.9),
        ink=C.paper('m_theater_ink', base=(0.016, 0.016, 0.019), rough=0.92),
        ink2=C.paper('m_theater_ink2', base=(0.038, 0.036, 0.034), rough=0.9),
        ink3=C.paper('m_theater_ink3', base=(0.070, 0.066, 0.060), rough=0.88),
        paper=C.paper('m_theater_paper', base=(0.62, 0.57, 0.47), rough=0.8),
        paper_warm=C.paper('m_theater_paper_warm', base=(0.72, 0.60, 0.42), rough=0.8),
        gold=C.paper('m_theater_gold', base=(0.82, 0.60, 0.20), rough=0.32),
    )


def paper_window(w=3.6, h=2.9, loc=(0.0, -21.0, FLOOR + 2.6), color=(0.72, 0.84, 1.0), strength=1.6,
                 cols=7, rows=5):
    """A big square shoji (paper screen) window at the back of the stage: glowing paper + dark lattice."""
    M = _mats()
    # --- glowing paper panel with soft vertical falloff + faint mottle
    m = bpy.data.materials.new('m_window')
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (*[min(1.0, c * 1.10) for c in color], 1)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (*[c * 0.35 for c in color], 1)
    noise = nt.nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 9.0
    mix = nt.nodes.new('ShaderNodeMixRGB'); mix.blend_type = 'MULTIPLY'; mix.inputs['Fac'].default_value = 0.18
    nt.links.new(tc.outputs['Object'], sep.inputs['Vector'])
    nt.links.new(sep.outputs['Z'], ramp.inputs['Fac'])
    nt.links.new(tc.outputs['Object'], noise.inputs['Vector'])
    nt.links.new(ramp.outputs['Color'], mix.inputs['Color1'])
    nt.links.new(noise.outputs['Color'], mix.inputs['Color2'])
    nt.links.new(mix.outputs['Color'], em.inputs['Color'])
    em.inputs['Strength'].default_value = strength
    nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    g = G.Geo('backdrop_window')
    g.plane(w, loc, (math.radians(90), 0, 0), m, sx=1.0, sy=h)
    win = g.build()
    win.visible_shadow = False
    # --- dark lattice, slightly in front of the paper
    g2 = G.Geo('window_lattice')
    fy = loc[1] + 0.05
    for i in range(1, cols):
        x = loc[0] - w / 2 + i * w / cols
        g2.box((0.045, 0.03, h), (x, fy, loc[2]), (0, 0, 0), M['ink'])
    for j in range(1, rows):
        z = loc[2] - h / 2 + j * h / rows
        g2.box((w, 0.03, 0.045), (loc[0], fy, z), (0, 0, 0), M['ink'])
    # outer frame (gold) + dark reveal so the opening reads as a cut in the wall
    g2.box((w + 0.22, 0.05, 0.07), (loc[0], fy + 0.02, loc[2] + h / 2), (0, 0, 0), M['gold'])
    g2.box((w + 0.22, 0.05, 0.07), (loc[0], fy + 0.02, loc[2] - h / 2), (0, 0, 0), M['gold'])
    g2.box((0.07, 0.05, h + 0.22), (loc[0] - w / 2, fy + 0.02, loc[2]), (0, 0, 0), M['gold'])
    g2.box((0.07, 0.05, h + 0.22), (loc[0] + w / 2, fy + 0.02, loc[2]), (0, 0, 0), M['gold'])
    g2.box((w + 0.10, 0.08, 0.16), (loc[0], fy, loc[2] + h / 2 + 0.11), (0, 0, 0), M['ink'])
    g2.box((w + 0.10, 0.08, 0.16), (loc[0], fy, loc[2] - h / 2 - 0.11), (0, 0, 0), M['ink'])
    lat = g2.build()
    lat.visible_shadow = False
    return win, lat


# --------------------------------------------------------------------------- stage
def stage_floor(width=12.0, y0=-6.2, y1=-24.0, z=FLOOR, plank_w=0.62, seed=3):
    """Raked paper-plank stage with visible seams; front edge gets a dark lip."""
    rnd = random.Random(seed)
    M = _mats()
    g = G.Geo('stage_floor')
    n = int((y0 - y1) / plank_w)
    for i in range(n):
        y = y0 - (i + 0.5) * plank_w
        base = (0.30 + rnd.uniform(-0.03, 0.03), 0.255 + rnd.uniform(-0.025, 0.025), 0.20 + rnd.uniform(-0.02, 0.02))
        m = C.paper(f'm_plank_{i%4}', base=base, rough=0.84)
        g.box((width + rnd.uniform(-0.3, 0.3), plank_w - 0.012, 0.055), (rnd.uniform(-0.04, 0.04), y, z - 0.0275), (0, 0, 0), m)
    # front lip: keep its top 1 mm below the planks so the two coplanar tops cannot fight
    g.box((width, 0.16, 0.16), (0, y0 + 0.02, z - 0.081), (0, 0, 0), M['ink'])
    ob = g.build()
    return ob


def curtain_wing(side=-1, x=3.6, y=-8.0, z=FLOOR, height=5.2, panels=7, seed=1):
    """Layered vertical paper curtain (theatre leg) that hides the set edges."""
    rnd = random.Random(seed)
    M = _mats()
    g = G.Geo(f'wing_{side}')
    for i in range(panels):
        px = x + side * i * 0.22 + rnd.uniform(-0.04, 0.04)
        py = y - i * 0.16
        h = height * (0.78 + 0.22 * math.sin(i * 1.7 + seed))
        g.plane(0.9, (px, py, z + h / 2), (math.radians(90), 0, side * math.radians(6 + i * 0.6)),
                M['ink'] if i % 2 == 0 else M['ink2'], sx=1.0, sy=h)
    ob = g.build()
    return ob


def backdrop_wall(y=-21.0, w=26.0, h=10.0, z=FLOOR, hole=(0.0, FLOOR + 2.6, 1.8, 1.45), seed=5):
    """A wall of dark paper with a rectangular cut-out; a glowing shoji window sits behind it.
    hole = (cx, cz, half_w, half_h)."""
    M = _mats()
    cx, cz, hw, hh = hole
    g = G.Geo('backdrop_wall')
    left_w = (cx - hw) - (-w / 2)
    right_w = (w / 2) - (cx + hw)
    g.box((left_w, 0.12, h), (-w / 2 + left_w / 2, y, z + h / 2), (0, 0, 0), M['ink3'])
    g.box((right_w, 0.12, h), (cx + hw + right_w / 2, y, z + h / 2), (0, 0, 0), M['ink3'])
    g.box((2 * hw, 0.12, (z + h) - (cz + hh)), (cx, y, ((cz + hh) + (z + h)) / 2), (0, 0, 0), M['ink3'])
    g.box((2 * hw, 0.12, (cz - hh) - z), (cx, y, ((cz - hh) + z) / 2), (0, 0, 0), M['ink3'])
    # vertical paper panel seams for scale
    for i in range(-6, 7):
        sx = i * 2.0
        if abs(sx - cx) < hw + 0.2:
            continue
        g.box((0.035, 0.02, h), (sx, y + 0.07, z + h / 2), (0, 0, 0), M['ink2'])
    wall = g.build()
    win, lat = paper_window(w=2 * hw, h=2 * hh, loc=(cx, y - 0.32, cz))
    return wall, win, lat


def footlights(y=-6.55, z=FLOOR + 0.10, n=9, span=5.4, energy=2.4):
    """Row of little glowing paper bulbs along the stage edge."""
    M = _mats()
    g = G.Geo('footlight_bulbs')
    em = C.emissive('m_footlight_glow', (1.0, 0.55, 0.26), 14.0)
    for i in range(n):
        x = -span / 2 + i * span / (n - 1)
        g.sphere(0.030, (x, y, z), M['gold'])
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.055, location=(x, y, z))
        o = bpy.context.object
        o.name = f'footlight_glow_{i}'
        o.data.materials.append(em)
        o.visible_shadow = False
        L = C.light(f'foot_{i}', 'POINT', loc=(x, y + 0.06, z + 0.04), energy=energy,
                    color=(1.0, 0.52, 0.24), size=0.05)
        L.data.volume_factor = 0.8
        L.data.use_shadow = False        # tiny bulb: shadow maps cost far more than they show
    ob = g.build()
    return ob


def top_batten(y=-9.0, z=FLOOR + 5.4, w=7.6, seed=2):
    """Overhead paper batten with hanging threads down to the puppet mark."""
    M = _mats()
    g = G.Geo('batten')
    g.box((w, 0.14, 0.14), (0, y, z), (0, 0, 0), M['ink'])
    g.box((w, 0.10, 0.05), (0, y, z + 0.10), (0, 0, 0), M['ink2'])
    ob = g.build()
    return ob


def threads(target=(-0.6, -11.0, FLOOR + 1.5), top_z=FLOOR + 5.4, ys=(-9.0,), xs=(-1.6, -0.6, 0.4)):
    """Thin rigging threads from batten to the puppet (visible paper-puppet logic)."""
    M = _mats()
    made = []
    for i, x in enumerate(xs):
        y = ys[0]
        p0 = Vector((x, y, top_z))
        p1 = Vector((target[0] + (x - target[0]) * 0.15, target[1], target[2] + 0.25 * i))
        d = p1 - p0
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.0045, depth=d.length, location=(p0 + p1) / 2)
        o = bpy.context.object
        o.name = f'thread_{i}'
        o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
        o.data.materials.append(M['ink2'])
        o.visible_shadow = False
        made.append(o)
    return made


def paper_lanterns(positions, color=(1.0, 0.60, 0.30), glow=9.0):
    M = _mats()
    g = G.Geo('lanterns')
    em = C.emissive('m_lantern_glow2', color, glow)
    for i, (x, y, z) in enumerate(positions):
        g.sphere(0.075, (x, y, z), M['paper_warm'])
        g.cylinder(0.004, 0.55, (x, y, z + 0.32), (0, 0, 0), M['ink2'], seg=4)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.115, location=(x, y, z))
        o = bpy.context.object
        o.name = f'lantern_glow_{i}'
        o.data.materials.append(em)
        o.visible_shadow = False
        L = C.light(f'lantern_{i}', 'POINT', loc=(x, y, z), energy=16.0, color=color, size=0.10)
        L.data.volume_factor = 1.6
        L.data.use_shadow = False        # tiny lantern: no shadow map
    ob = g.build()
    return ob


def audience_railing(y=-3.4, z=FLOOR + 0.55, w=11.0):
    """Dark paper balcony rail in the foreground; the camera looks over it (we are the audience)."""
    M = _mats()
    g = G.Geo('railing')
    g.box((w, 0.10, 0.10), (0, y, z + 0.62), (0, 0, 0), M['ink'])
    for i in range(7):
        x = -w / 2 + 0.4 + i * (w - 0.8) / 6
        g.box((0.05, 0.05, 0.62), (x, y, z + 0.31), (0, 0, 0), M['ink'])
    g.box((w, 0.6, 0.06), (0, y + 0.05, z - 0.02), (0, 0, 0), M['ink2'])
    ob = g.build()
    return ob


def distant_archive(y=-30.0, seed=7, rows=3):
    """Cheap silhouette of far shelves behind the stage wall's hole (parallax + depth)."""
    M = _mats()
    g = G.Geo('distant_archive')
    rnd = random.Random(seed)
    for r in range(rows):
        yy = y - r * 4.0
        for i in range(9):
            x = -12 + i * 3.0 + rnd.uniform(-0.6, 0.6)
            h = 5.0 + rnd.uniform(-1.5, 2.0)
            g.box((2.4, 0.25, h), (x, yy, FLOOR + h / 2), (0, 0, 0), M['ink'])
            for lv in range(4):
                zz = FLOOR + 0.8 + lv * h / 5.0
                g.box((2.2, 0.3, 0.07), (x, yy - 0.02, zz), (0, 0, 0), M['ink2'])
    ob = g.build()
    return ob


def plinth(x, y, z=FLOOR, h=0.58, w=0.72, d=0.72, gold=True, label=True):
    """A museum pedestal of folded paper: tapered shaft, dark cap, gold seam, small label."""
    M = _mats()
    g = G.Geo('plinth_%d_%d' % (int(x * 10), int(y * 10)))
    shaft_h = h - 0.10
    g.box((w * 0.90, d * 0.90, shaft_h), (x, y, z + shaft_h / 2), (0, 0, 0), M['paper'])
    # thin base shadow gap
    g.box((w * 0.80, d * 0.80, 0.035), (x, y, z + 0.018), (0, 0, 0), M['plank_dark'])
    # cap
    g.box((w, d, 0.075), (x, y, z + shaft_h + 0.0375), (0, 0, 0), M['paper_warm'])
    g.box((w + 0.03, d + 0.03, 0.028), (x, y, z + h - 0.014), (0, 0, 0), M['ink'])
    if gold:
        g.box((w + 0.05, d + 0.05, 0.010), (x, y, z + h - 0.033), (0, 0, 0), M['gold'])
    if label:
        g.box((0.26, 0.012, 0.09), (x, y + d / 2 + 0.006, z + shaft_h * 0.62), (0, 0, 0), M['paper_warm'])
    ob = g.build()
    return ob


def terminal_desk(loc=(-2.5, -10.0, FLOOR), rotz=0.16):
    """A cardboard terminal: desk + angled glowing screen + keypad + paper printout."""
    M = _mats()
    x, y, z = loc
    g = G.Geo('terminal_desk')
    # desk
    g.box((1.35, 0.72, 0.06), (x, y, z + 0.74), (0, 0, 0), M['plank'])
    for sx in (-0.58, 0.58):
        for sy in (-0.26, 0.26):
            g.box((0.07, 0.07, 0.72), (x + sx, y + sy, z + 0.36), (0, 0, 0), M['ink2'])
    # screen body, tilted back
    g.box((0.62, 0.16, 0.46), (x + 0.06, y - 0.18, z + 1.06), (math.radians(-12), 0, 0), M['ink'])
    # keypad slab
    g.box((0.52, 0.26, 0.045), (x - 0.12, y + 0.22, z + 0.79), (math.radians(-4), 0, 0), M['ink2'])
    ob = g.build()
    # glowing screen plane (faces the audience, +Y)
    g2 = G.Geo('terminal_screen')
    g2.plane(1.0, (x + 0.06, y - 0.10, z + 1.07), (math.radians(90 + 12), 0, math.pi),
             _screen_mat(), sx=0.54, sy=0.36)
    scr = g2.build()
    scr.visible_shadow = False
    # little warm lamp on the desk
    g3 = G.Geo('desk_lamp')
    g3.cylinder(0.035, 0.28, (x + 0.5, y + 0.1, z + 0.9), (0, 0, 0), M['gold'], seg=12)
    lamp = g3.build()
    return ob, scr, lamp


def _screen_mat():
    m = bpy.data.materials.new('m_terminal_screen')
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    add = nt.nodes.new('ShaderNodeMath'); add.operation = 'ADD'
    sine = nt.nodes.new('ShaderNodeMath'); sine.operation = 'SINE'
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.05, 0.20, 0.16, 1)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (0.55, 1.0, 0.82, 1)
    nt.links.new(tc.outputs['Object'], sep.inputs['Vector'])
    nt.links.new(sep.outputs['Y'], sine.inputs[0])
    nt.links.new(sine.outputs[0], mul.inputs[0])
    nt.links.new(sep.outputs['X'], mul.inputs[1])
    nt.links.new(mul.outputs[0], add.inputs[0])
    nt.links.new(add.outputs[0], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], em.inputs['Color'])
    em.inputs['Strength'].default_value = 2.2
    nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    return m


def theatre(seed=3, dress=True, floor=True):
    """Assemble the full paper theatre set. Returns a dict of important objects."""
    M = _mats()
    objs = {}
    if floor:
        objs['floor'] = stage_floor(seed=seed)
    objs['wing_L'] = curtain_wing(side=-1, x=-3.7, seed=11)
    objs['wing_R'] = curtain_wing(side=1, x=3.7, seed=13)
    objs['backdrop'] = backdrop_wall(hole=(0.0, FLOOR + 3.05, 1.70, 1.40))
    objs['distant'] = distant_archive()
    objs['batten'] = top_batten()
    objs['threads'] = threads()
    objs['railing'] = audience_railing()
    objs['footlights'] = footlights()
    objs['lanterns'] = paper_lanterns([(-2.6, -9.5, FLOOR + 3.4), (2.4, -10.5, FLOOR + 3.9),
                                       (-2.9, -14.0, FLOOR + 3.1), (2.9, -15.5, FLOOR + 3.6)])
    # specimen plinths: a shallow arc behind the playing area, empty until summoned
    objs['plinths'] = []
    for i, (px, py) in enumerate([(-3.0, -15.4), (-1.0, -15.9), (1.0, -15.9), (3.0, -15.4)]):
        objs['plinths'].append(plinth(px, py, h=0.60))
    objs['hero_plinth'] = plinth(-2.15, -13.2, h=0.52, w=0.62, d=0.62)
    objs['desk'], objs['screen'], objs['lamp'] = terminal_desk(loc=(-2.45, -10.4, FLOOR))
    if dress:
        try:
            import look2 as _l2
            objs.update(_l2.dress_all())
        except Exception as _e:
            print('look2 dressing failed: %r' % (_e,), flush=True)
    return objs
