"""stage.py - canonical paper-theatre stage builder shared by lookdev and the shot renderer."""
import bpy, sys, os, math, random, time
sys.path.insert(0, r'D:\Code\Code MV\new-word.search(you)\mv\build')
for _m in ('core', 'world', 'geo', 'world_theater'):
    sys.modules.pop(_m, None)
import core as C
import world_theater as T
import geo as G

FLOOR = -6.0
CHAR_LOC = (0.55, -11.2, FLOOR)


def _contact_shadow(loc, sx=1.4, sy=0.75):
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(loc[0], loc[1], FLOOR + 0.004))
    sh = bpy.context.object
    sh.name = 'contact_shadow'
    sh.scale = (sx, sy, 1)
    m = bpy.data.materials.new('m_contact')
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (0.0, 0.0, 0.0, 1)
    mix = nt.nodes.new('ShaderNodeMixShader')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    vec = nt.nodes.new('ShaderNodeVectorMath'); vec.operation = 'LENGTH'
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.04
    ramp.color_ramp.elements[0].color = (0.46, 0.46, 0.46, 1)
    ramp.color_ramp.elements[1].position = 0.50
    ramp.color_ramp.elements[1].color = (0, 0, 0, 1)
    nt.links.new(tc.outputs['Object'], vec.inputs[0])
    nt.links.new(vec.outputs['Value'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], mix.inputs[0])
    nt.links.new(tr.outputs['BSDF'], mix.inputs[1])
    nt.links.new(em.outputs['Emission'], mix.inputs[2])
    nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
    m.surface_render_method = 'BLENDED'
    sh.data.materials.append(m)
    sh.visible_shadow = False
    return sh


def build_stage(char='cheerful', window_strength=1.05):
    objs = T.theatre(seed=3)
    mat = bpy.data.materials.get('m_window')
    if mat and mat.node_tree:
        for n in mat.node_tree.nodes:
            if n.type == 'EMISSION':
                n.inputs['Strength'].default_value = window_strength
    front, cmat, back = C.paper_cutout(os.path.join(C.TEX, 'galgame', 'whale-%s.webp' % char),
                                       height=1.75, loc=CHAR_LOC,
                                       emission_strength=0.05, name='whale_paper')
    objs['char'] = front
    objs['char_back'] = back
    objs['char_mat'] = cmat
    objs['contact'] = _contact_shadow(CHAR_LOC)
    return objs


def foreground_papers(seed=7, n=20):
    """Out-of-focus paper scraps floating between the audience and the stage -> depth."""
    M = T._mats()
    rnd = random.Random(seed)
    em = C.emissive('m_fg_scrap', (0.42, 0.36, 0.27), 0.9)
    em2 = C.emissive('m_fg_scrap2', (0.20, 0.30, 0.40), 0.7)
    g = G.Geo('fg_papers')
    for i in range(n):
        side = 1.0 if rnd.random() < 0.5 else -1.0
        x = side * rnd.uniform(1.05, 4.1)
        y = rnd.uniform(-6.8, -5.0)
        z = FLOOR + rnd.uniform(0.30, 1.85)
        w = rnd.uniform(0.09, 0.22)
        h = w * rnd.uniform(0.7, 1.5)
        g.plane(1.0, (x, y, z), (rnd.uniform(-0.7, 0.7), rnd.uniform(-1.0, 1.0), rnd.uniform(0, 6.28)),
                em if i % 3 else em2, sx=w, sy=h)
    ob = g.build()
    ob.visible_shadow = False
    return ob


def lighting(mood='default'):
    """Paper-theatre rig v3: the proven v1 balance plus a real window shaft,
    a warm floor pool and a low bounce card (set dressing lives in look2.py)."""
    t = bpy.data.objects.new('key_tgt', None)
    bpy.context.collection.objects.link(t)
    t.location = (CHAR_LOC[0], CHAR_LOC[1], FLOOR + 1.15)

    # --- KEY: warm, hard, the only subject shadow
    L = C.light('stage_key2', 'SPOT', loc=(-2.30, -7.20, FLOOR + 4.40), energy=3100,
                color=(1.0, 0.70, 0.46), size=0.28, angle=math.radians(31), target=t)
    L.data.volume_factor = 2.4

    # --- RIM: cold kicker from behind
    L = C.light('stage_rim2', 'SPOT', loc=(1.50, -15.40, FLOOR + 3.60), energy=5600,
                color=(0.20, 0.54, 1.0), size=0.20, angle=math.radians(20))
    C.look_at(L, (CHAR_LOC[0], CHAR_LOC[1], FLOOR + 1.25))
    L.data.volume_factor = 3.4

    # --- FILL: soft cool front fill
    L = C.light('stage_fill2', 'AREA', loc=(CHAR_LOC[0] + 3.6, CHAR_LOC[1] + 5.2, FLOOR + 2.4),
                energy=90, color=(0.45, 0.66, 1.0), size=3.5)
    C.look_at(L, (CHAR_LOC[0], CHAR_LOC[1], FLOOR + 1.0))
    L.data.use_shadow = False

    # --- TOP SHAFT: cool beam down onto the mark
    L = C.light('stage_shaft2', 'SPOT', loc=(1.05, -9.80, FLOOR + 7.60), energy=3800,
                color=(0.44, 0.72, 1.0), size=0.20, angle=math.radians(11))
    C.look_at(L, (0.95, -10.9, FLOOR))
    L.data.volume_factor = 3.8

    # --- WINDOW SHAFT: from just in front of the shoji, low into the house
    L = C.light('window_beam2', 'SPOT', loc=(0.0, -20.35, FLOOR + 3.00), energy=2400,
                color=(0.56, 0.79, 1.0), size=0.85, angle=math.radians(44))
    C.look_at(L, (0.30, -8.8, FLOOR + 0.30))
    L.data.volume_factor = 3.0

    # --- WARM FLOOR POOL: the pool the puppet plays in
    L = C.light('floor_pool2', 'POINT', loc=(0.95, -9.30, FLOOR + 0.50), energy=160,
                color=(1.0, 0.62, 0.34), size=1.10)
    L.data.volume_factor = 1.3
    L.data.use_shadow = False

    # --- BOUNCE CARD: low warm bounce from camera left
    L = C.light('bounce2', 'AREA', loc=(-2.6, -9.0, FLOOR + 0.70), energy=80,
                color=(1.0, 0.66, 0.42), size=2.0)
    C.look_at(L, (CHAR_LOC[0], CHAR_LOC[1], FLOOR + 1.35))
    L.data.use_shadow = False

    # --- WINDOW SPILL: cool ambience out of the shoji
    L = C.light('window_spill2', 'AREA', loc=(0.0, -20.0, FLOOR + 3.0), energy=210,
                color=(0.60, 0.80, 1.0), size=4.2)
    C.look_at(L, (0.0, -11.5, FLOOR + 1.2))
    L.data.use_shadow = False

    # --- WALL WASH: makes the paper panels read
    L = C.light('wall_wash2', 'AREA', loc=(0.0, -15.8, FLOOR + 4.6), energy=52,
                color=(0.40, 0.58, 0.95), size=6.5)
    C.look_at(L, (0.0, -21.0, FLOOR + 3.4))
    L.data.use_shadow = False

    # --- practical terminal glow
    L = C.light('desk_pool2', 'POINT', loc=(-2.35, -10.1, FLOOR + 1.15), energy=55,
                color=(0.35, 1.0, 0.72), size=0.28)
    L.data.volume_factor = 0.8
    L.data.use_shadow = False

    C.dust('dust', count=1600, extent=(10, 14, 7.5), center=(0.2, -12.0, FLOOR + 3.0),
           size=0.006, color=(0.72, 0.88, 1.0), strength=2.6)

    atmosphere_extras()




def _glow_card(name, loc, w, h, color, strength=1.0, rot=(math.radians(90), 0, math.pi)):
    """Soft radial glow card (BLENDED additive-looking emission) for halos / bokeh."""
    m = bpy.data.materials.get('m_' + name) or bpy.data.materials.new('m_' + name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (color[0], color[1], color[2], 1)
    em.inputs['Strength'].default_value = strength
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mix = nt.nodes.new('ShaderNodeMixShader')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    vec = nt.nodes.new('ShaderNodeVectorMath')
    vec.operation = 'LENGTH'
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
    ramp.color_ramp.elements[1].position = 0.55
    ramp.color_ramp.elements[1].color = (0, 0, 0, 1)
    nt.links.new(tc.outputs['Object'], vec.inputs[0])
    nt.links.new(vec.outputs['Value'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], mix.inputs[0])
    nt.links.new(tr.outputs['BSDF'], mix.inputs[1])
    nt.links.new(em.outputs['Emission'], mix.inputs[2])
    nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
    m.surface_render_method = 'BLENDED'
    ob = C.plane(name, size=1.0, loc=loc, rot=rot, mat=m)
    ob.scale = (w, h, 1.0)
    ob.visible_shadow = False
    return ob


def atmosphere_extras():
    """Halo behind the puppet, two coloured accent rims, near-lens bokeh orbs."""
    # halo card behind the playing area (reads as haze catching the backlight)
    _glow_card('halo_back', (CHAR_LOC[0], CHAR_LOC[1] - 3.9, FLOOR + 1.15),
               4.6, 3.6, (0.10, 0.22, 0.55), strength=0.45)
    # accent rims: magenta camera-left, cyan camera-right (thin energy, volume on)
    L = C.light('accent_warm', 'SPOT', loc=(-3.6, -13.2, FLOOR + 2.6), energy=1500,
                color=(1.0, 0.34, 0.42), size=0.16, angle=math.radians(22))
    C.look_at(L, (CHAR_LOC[0], CHAR_LOC[1] + 0.3, FLOOR + 1.1))
    L.data.volume_factor = 2.2
    L = C.light('accent_cyan', 'SPOT', loc=(3.4, -12.6, FLOOR + 2.2), energy=1300,
                color=(0.28, 0.62, 1.0), size=0.16, angle=math.radians(20))
    C.look_at(L, (CHAR_LOC[0], CHAR_LOC[1] + 0.2, FLOOR + 1.3))
    L.data.volume_factor = 2.0
    # near-lens bokeh: soft glowing orbs floating between audience and stage
    import random as _r
    rnd = _r.Random(31)
    specs = [(-2.90, -4.60, 1.55, 0.26, (1.0, 0.62, 0.34)),
             (2.55, -5.20, 1.20, 0.20, (0.36, 0.68, 1.0)),
             (-1.75, -5.35, 2.05, 0.15, (1.0, 0.74, 0.44)),
             (2.05, -4.35, 2.35, 0.12, (0.52, 0.80, 1.0)),
             (-3.25, -5.55, 0.95, 0.10, (1.0, 0.58, 0.30))]
    for i, (x, y, dz, r, col) in enumerate(specs):
        _glow_card('bokeh_%d' % i, (x, y, FLOOR + dz), r * 9.0, r * 9.0, col,
                   strength=1.25, rot=(math.radians(90), 0, 0))
    return True


def cameras():
    cams = {}
    cams['wide'] = C.camera('cam_wide', lens=36, loc=(1.10, -2.95, FLOOR + 1.62),
                            target=(-0.15, -12.0, FLOOR + 1.15), dof=True, fstop=4.0)
    cams['three_q'] = C.camera('cam_three_q', lens=60, loc=(-3.05, -8.55, FLOOR + 1.62),
                               target=(0.50, -11.40, FLOOR + 1.20), dof=True, fstop=2.2)
    cams['close'] = C.camera('cam_close', lens=100, loc=(-0.75, -7.60, FLOOR + 1.50),
                             target=(0.55, -11.20, FLOOR + 1.22), dof=True, fstop=1.8)
    cams['low'] = C.camera('cam_low', lens=28, loc=(0.15, -6.55, FLOOR + 0.30),
                           target=(0.55, -11.2, FLOOR + 1.30), dof=True, fstop=4.0)
    return cams


def viewport_setup():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'RENDERED'
                    space.overlay.show_overlays = False
                    space.region_3d.view_perspective = 'CAMERA'


def render_frames(cams, names, out_dir, w=960, h=540, tag=''):
    os.makedirs(out_dir, exist_ok=True)
    sc = bpy.context.scene
    sc.render.resolution_x = w
    sc.render.resolution_y = h
    sc.render.resolution_percentage = 100
    viewport_setup()
    for name in names:
        sc.camera = cams[name]
        sc.frame_set(1)
        sc.render.filepath = os.path.join(out_dir, 'set_%s%s_%d.png' % (name, tag, w))
        t = time.time()
        bpy.ops.render.render(write_still=True)
        print('RENDER %s %.2fs' % (name, time.time() - t), flush=True)
