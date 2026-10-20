"""Add depth & glow: halo card behind the puppet, accent rims, near-lens bokeh orbs."""
import io
import py_compile

P = r'D:\Code\Code MV\new-word.search(you)\mv\build\stage.py'
s = io.open(P, encoding='utf-8').read()

if 'def _glow_card' not in s:
    helper = '''

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
               4.6, 3.6, (0.10, 0.22, 0.55), strength=0.85)
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

'''
    s = s.replace('\ndef cameras():', helper + '\ndef cameras():', 1)
    # call it at the end of lighting()
    anchor = "           size=0.006, color=(0.72, 0.88, 1.0), strength=2.6)"
    assert anchor in s
    s = s.replace(anchor, anchor + "\n\n    atmosphere_extras()", 1)
    io.open(P, 'w', encoding='utf-8').write(s)
    print('[ok] stage.py atmosphere_extras')
else:
    print('[skip] already present')

py_compile.compile(P, doraise=True)
print('compiled OK')
