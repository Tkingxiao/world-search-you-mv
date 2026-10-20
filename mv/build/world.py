"""world.py - sets for the sunken paper archive (lead's pipeline).
All builders use geo.Geo so each set is 5-30 objects total (EEVEE sync friendly).
"""
import bpy, bmesh, math, random
from mathutils import Vector, Euler
import core as C
import geo as G


def _papers():
    return dict(
        shelf=C.paper('m_shelf', base=(0.115, 0.105, 0.092), rough=0.86),
        shelf_dark=C.paper('m_shelf_dark', base=(0.055, 0.052, 0.048), rough=0.9),
        file=C.paper('m_file', base=(0.52, 0.49, 0.41), rough=0.82),
        file_dark=C.paper('m_file_dark', base=(0.10, 0.10, 0.095), rough=0.88),
        sheet=C.paper('m_sheet', base=(0.70, 0.66, 0.56), rough=0.78),
        sheet_warm=C.paper('m_sheet_warm', base=(0.74, 0.64, 0.50), rough=0.8),
        stone=C.paper('m_stone', base=(0.035, 0.040, 0.040), rough=0.62),
        plinth=C.paper('m_plinth', base=(0.40, 0.375, 0.32), rough=0.84),
        tab_r=C.paper('m_tab_r', base=(0.72, 0.075, 0.055), rough=0.75),
        tab_b=C.paper('m_tab_b', base=(0.045, 0.13, 0.72), rough=0.75),
        tab_y=C.paper('m_tab_y', base=(0.86, 0.60, 0.075), rough=0.75),
    )


def _rack(g, P, x, y, z0, h, w, d, rotz, seed):
    rnd = random.Random(seed)
    ca, sa = math.cos(rotz), math.sin(rotz)
    def T(fx, fy):
        return (x + fx * ca - fy * sa, y + fx * sa + fy * ca)
    # posts
    for i in range(4):
        px = (-1 + i * 2 / 3) * (w / 2)
        wx, wy = T(px, 0)
        g.box((0.075, d, h), (wx, wy, z0 + h / 2), (0, 0, rotz), P['shelf'])
    nlev = 8
    tabs = (P['tab_r'], P['tab_b'], P['tab_y'])
    for lv in range(nlev):
        z = z0 + 0.3 + lv * (h - 0.5) / (nlev - 1)
        g.box((w, d, 0.05), (x, y, z), (0, 0, rotz), P['shelf'])
        n = rnd.randint(3, 7)
        for _ in range(n):
            fw = rnd.uniform(0.10, 0.22)
            fh = rnd.uniform(0.28, 0.55)
            fx = rnd.uniform(-w / 2 + 0.16, w / 2 - 0.16)
            fy = rnd.uniform(-d / 2 + 0.14, d / 2 - 0.16)
            wx, wy = T(fx, fy)
            g.box((fw, rnd.uniform(0.13, 0.24), fh), (wx, wy, z + 0.028 + fh / 2),
                  (0, 0, rotz + rnd.uniform(-0.04, 0.04)),
                  P['file'] if rnd.random() > 0.32 else P['file_dark'])
        # a few coloured index tabs peeking above the files
        if rnd.random() > 0.25:
            fx = rnd.uniform(-w / 2 + 0.2, w / 2 - 0.2)
            wx, wy = T(fx, rnd.uniform(-d / 2 + 0.16, d / 2 - 0.16))
            g.box((0.05, 0.10, 0.05), (wx, wy, z + 0.42), (0, 0, rotz + rnd.uniform(-0.1, 0.1)),
                  rnd.choice(tabs))


def papercraft_table(size=0.34, loc=(0, 0, 0), rotz=0.0):
    """A folded-paper table model - the first specimen (lyric: 'If you turn into a table')."""
    P = _papers()
    g = G.Geo('specimen_table')
    s = size
    top = C.paper('m_spec_table_top', base=(0.86, 0.82, 0.71), rough=0.8)
    g.box((s, s * 0.62, 0.035), (0, 0, s * 0.52), (0, 0, rotz), top)
    for sx in (-1, 1):
        for sy in (-1, 1):
            g.box((0.03, 0.03, s * 0.5), (sx * s * 0.40, sy * s * 0.22, s * 0.25), (0, 0, rotz), P['sheet_warm'])
    ob = g.build()
    ob.location = loc
    return ob


def bell_jar(r=0.26, h=0.52, loc=(0, 0, 0)):
    """Thin transparent display dome (alpha-blended, no refraction - EEVEE friendly)."""
    m = bpy.data.materials.new('m_bell')
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    bsdf.inputs['Base Color'].default_value = (0.85, 0.93, 1.0, 1)
    bsdf.inputs['Roughness'].default_value = 0.05
    bsdf.inputs['Alpha'].default_value = 0.10
    m.surface_render_method = 'BLENDED'
    g = G.Geo('bell_jar')
    g.cylinder(r, h, (0, 0, h / 2), (0, 0, 0), m, seg=32)
    ob = g.build()
    ob.location = loc
    return ob


def archive_aisle(seed=0, aisle_half=2.6, rack_x=3.55, n_side=8, dy=3.25, z0=-6.0,
                  h=8.0, w=3.5, d=1.25, back_y=-30.0):
    """Central clear aisle along -Y, racks on both sides, big shelf wall at the far end."""
    rnd = random.Random(seed)
    P = _papers()
    g = G.Geo('archive_geo')
    for side in (-1, 1):
        for i in range(n_side):
            y = -4.0 - i * dy + rnd.uniform(-0.25, 0.25)
            x = side * (rack_x + rnd.uniform(-0.3, 0.3))
            _rack(g, P, x, y, z0, h + rnd.uniform(-0.5, 0.8), w + rnd.uniform(-0.3, 0.3),
                  d, side * math.radians(rnd.uniform(0.5, 2.5)), seed * 31 + side * 7 + i)
    # far wall of shelves (fills the end of the aisle)
    for i in range(-3, 4):
        _rack(g, P, i * 3.6, back_y, z0, 9.0, 3.3, 1.2, 0, seed * 13 + i)
    # a few racks further out for parallax
    for i in range(8):
        x = rnd.choice([-1, 1]) * rnd.uniform(8.5, 15)
        y = -5 - i * 4.4 + rnd.uniform(-1, 1)
        _rack(g, P, x, y, z0, 7.4, 3.8, 1.2, rnd.uniform(-0.2, 0.2), seed * 5 + i)
    ob = g.build()
    ob.name = 'paper_archive'
    return ob


def loose_sheets(n=26, seed=5, aisle_half=2.6):
    """Small drifting sheets, kept out of the camera's center line."""
    rnd = random.Random(seed)
    P = _papers()
    g = G.Geo('loose_sheets')
    for i in range(n):
        s = rnd.uniform(0.18, 0.55)
        side = rnd.choice([-1, 1])
        x = side * rnd.uniform(aisle_half + 0.4, 11.0)
        y = rnd.uniform(-22.0, -1.0)
        z = rnd.uniform(-3.6, 7.2)
        g.plane(s, (x, y, z), (rnd.uniform(-1.2, 1.2), rnd.uniform(-1.2, 1.2), rnd.uniform(0, 6.28)),
                P['sheet'] if rnd.random() > 0.35 else P['sheet_warm'])
    ob = g.build()
    ob.name = 'loose_sheets'
    return ob


def seabed(size=140, z=-6.02, base=(0.075, 0.072, 0.065), rough=0.55):
    m = C.paper('m_seabed', base=base, rough=rough)
    g = G.Geo('seabed')
    g.plane(size, (0, 0, z), (0, 0, 0), m)
    return g.build()


def water_surface(z=9.0, size=140, strength=1.6):
    m = bpy.data.materials.new('m_surface')
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    noise = nt.nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 0.25; noise.inputs['Detail'].default_value = 5; noise.inputs['Roughness'].default_value = 0.6
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (0.01, 0.10, 0.18, 1)
    ramp.color_ramp.elements[1].position = 0.7
    ramp.color_ramp.elements[1].color = (0.28, 0.62, 0.82, 1)
    nt.links.new(tc.outputs['Generated'], noise.inputs['Vector'])
    nt.links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], em.inputs['Color'])
    em.inputs['Strength'].default_value = strength
    nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    g = G.Geo('water_surface')
    g.plane(size, (0, 0, z), (0, 0, 0), m)
    return g.build()


def shaft(name, top=(0, 0, 9.0), bottom=(0, 0, -6.0), r_top=0.4, r_bot=3.0,
          color=(1.0, 0.70, 0.42), strength=1.0, samples=20, angle_deg=16.0):
    """A real volumetric light shaft: spot light from above scattering in the fog.
    (Cone meshes read as solid slabs from close range - use light, not geometry.)"""
    tgt = bpy.data.objects.new(name + '_tgt', None)
    bpy.context.collection.objects.link(tgt)
    tgt.location = bottom
    L = C.light(name, 'SPOT', loc=top, energy=strength * 9000.0, color=color,
                size=0.12, angle=math.radians(angle_deg), target=tgt)
    L.data.volume_factor = 3.0
    L.data.shadow_soft_size = 0.2
    return L


def caustic_floor(size=40, z=-5.96, color=(0.30, 0.62, 0.80), strength=0.10):
    m = bpy.data.materials.new('m_caustic')
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    noise = nt.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 1.2
    noise.inputs['Detail'].default_value = 3.0
    noise.inputs['Roughness'].default_value = 0.55
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.52
    ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    ramp.color_ramp.elements[1].position = 0.62
    ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
    nt.links.new(tc.outputs['Generated'], noise.inputs['Vector'])
    nt.links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
    mult = nt.nodes.new('ShaderNodeMath'); mult.operation = 'MULTIPLY'; mult.inputs[1].default_value = strength
    nt.links.new(ramp.outputs['Color'], mult.inputs[0])
    nt.links.new(mult.outputs['Value'], em.inputs['Strength'])
    em.inputs['Color'].default_value = (*color, 1)
    nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    g = G.Geo('caustic_floor')
    g.plane(size, (0, 0, z), (0, 0, 0), m)
    return g.build()


def practical_lamps(positions, color=(1.0, 0.55, 0.28), energy=26.0, size=0.055, mat=None):
    """Small warm paper lanterns hung along the shelves - the archive is inhabited."""
    g = G.Geo('practical_lamps')
    for p in positions:
        g.sphere(size, p, mat or C.emissive('m_lamp', color, 9.0))
    return g.build()


def text_block(lines, loc, size=0.09, rot=(math.radians(90), 0, 0), font='C:/Windows/Fonts/consola.ttf',
               align='LEFT', spacing=1.0, color=(0.06, 0.06, 0.06)):
    mat = C.text_mat('m_type_ink', color, 0.0)
    objs = []
    for i, ln in enumerate(lines):
        ob = C.text_obj(f'line_{i}', ln, size=size, loc=(loc[0], loc[1] - i * size * 1.55, loc[2]),
                        rot=rot, font=font, mat=mat, align=align, spacing=spacing)
        objs.append(ob)
    return objs


def hanging_index_sheet(loc=(0, -7.0, 3.2), rotz=0.0, w=2.6, h=3.4, lines=None,
                        text_size=0.075, name='index_sheet'):
    """Large paper sheet suspended by two threads, with typewritten index."""
    P = _papers()
    sheet = C.plane(name, size=1.0, loc=loc, rot=(math.radians(90), 0, rotz),
                    mat=P['sheet_warm'])
    sheet.scale = (w, h, 1)
    # threads
    for sx in (-1, 1):
        cx = loc[0] + sx * (w / 2 - 0.12) * math.cos(rotz)
        cy = loc[1] + sx * (w / 2 - 0.12) * math.sin(rotz)
        g = G.Geo(f'thread_{sx}')
        g.cylinder(0.006, 5.0, (cx, cy, loc[2] + h / 2 + 2.5), (0, 0, 0), C.paper('m_thread', base=(0.35, 0.33, 0.30)))
        g.build()
    if lines is None:
        lines = ['MEMORY INDEX  /  ~/memory/you/',
                 'first_hello       2023-04-01   kept',
                 'typo_you_made     2023-04-02   kept',
                 'laugh_0314        2023-04-14   kept',
                 'your_cat          2023-05-01   kept',
                 'weather           2023-06-07   kept',
                 'goodnight         2023-07-19   kept',
                 'see_you           2023-08-03   kept',
                 'last_msg          2023-09-01   kept']
    tx = C.text_mat('m_index_ink', (0.10, 0.09, 0.08), 0.0)
    for i, ln in enumerate(lines):
        C.text_obj(f'{name}_t{i}', ln, size=text_size,
                   loc=(loc[0] - w / 2 + 0.14, loc[1] + 0.012, loc[2] + h / 2 - 0.24 - i * text_size * 1.7),
                   rot=(math.radians(90), 0, rotz), font='C:/Windows/Fonts/consola.ttf',
                   mat=tx, spacing=1.0)
    return sheet


def aisle_lights(target=(0, -7, 0), warm=True, z0=0.0):
    """Lighting rig for the archive aisle (z0 = floor height)."""
    lights = {}
    tz = target[2]
    # surface ambient: big soft area from above (cool)
    L = C.light('surf_amb', 'AREA', loc=(0, target[1], z0 + 14.2), energy=520, color=(0.32, 0.60, 0.95), size=16)
    L.rotation_euler = (math.radians(180), 0, 0)
    lights['surf_amb'] = L
    # warm key spot on subject
    tgt = bpy.data.objects.new('key_tgt', None)
    bpy.context.collection.objects.link(tgt)
    tgt.location = target
    L = C.light('key_spot', 'SPOT', loc=(1.6, target[1] + 3.4, z0 + 10.0), energy=4200, color=(1.0, 0.68, 0.44),
                size=0.3, angle=math.radians(40), target=tgt)
    L.data.volume_factor = 1.4
    lights['key_spot'] = L
    # cyan rim from behind-left
    L = C.light('rim', 'AREA', loc=(-3.2, target[1] - 2.6, tz + 1.6), energy=420, color=(0.10, 0.45, 1.0), size=2.4)
    L.rotation_euler = (math.radians(78), 0, math.radians(-150))
    lights['rim'] = L
    # fill from camera side
    L = C.light('fill', 'AREA', loc=(2.2, target[1] + 5.2, tz + 1.8), energy=110, color=(0.3, 0.42, 0.62), size=4.0)
    L.rotation_euler = (math.radians(80), 0, math.radians(30))
    lights['fill'] = L
    return lights
