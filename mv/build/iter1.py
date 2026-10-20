"""iter1.py - in-place lookdev tweaks on the GUI scene, then render a 960x540 check frame."""
import bpy, os, math, time, sys
sys.path.insert(0, r'D:\Code\Code MV\new-word.search(you)\mv\build')
for _m in ('core', 'world', 'geo'):
    sys.modules.pop(_m, None)
import core as C
import world as W
import geo as G
FLOOR = -6.0
OUT = r'D:\Code\Code MV\new-word.search(you)\mv\out\lookdev'
sc = bpy.context.scene

# ---- 1. denser fog so the light shafts actually read
w = bpy.data.worlds['mv_world']
nt = w.node_tree
for n in nt.nodes:
    if n.type == 'VOLUME_SCATTER':
        n.inputs['Density'].default_value = 0.032
        n.inputs['Color'].default_value = (0.010, 0.050, 0.085, 1)
        n.inputs['Anisotropy'].default_value = 0.45

# ---- 2. much stronger volumetric shafts + one extra behind the character
for ob in list(bpy.data.objects):
    if ob.type == 'LIGHT' and ob.name.startswith('shaft'):
        ob.data.energy = 16000.0
        ob.data.volume_factor = 6.0
        ob.data.spot_size = math.radians(17.0)
W.shaft('shaft_char', top=(-1.2, -11.8, 8.4), bottom=(-1.05, -9.2, FLOOR + 0.05),
        color=(1.0, 0.72, 0.45), strength=1.6, angle_deg=14.0)

# ---- 3. bell jar: nearly invisible glass, no shadow
for ob in bpy.data.objects:
    if ob.name.startswith('bell_jar'):
        m = ob.data.materials[0]
        bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        bsdf.inputs['Alpha'].default_value = 0.045
        m.use_transparent_shadow = False
        ob.visible_shadow = False

# ---- 4. fake contact shadow under the paper cut-out
for ob in list(bpy.data.objects):
    if ob.name in ('contact_shadow',):
        bpy.data.objects.remove(ob, do_unlink=True)
bpy.ops.mesh.primitive_plane_add(size=1.0, location=(-1.05, -9.2, FLOOR + 0.006))
sh = bpy.context.object
sh.name = 'contact_shadow'
sh.scale = (1.5, 0.75, 1)
m = bpy.data.materials.new('m_contact')
m.use_nodes = True
nt = m.node_tree
nt.nodes.clear()
out = nt.nodes.new('ShaderNodeOutputMaterial')
tr = nt.nodes.new('ShaderNodeBsdfTransparent')
em = nt.nodes.new('ShaderNodeEmission')
em.inputs['Color'].default_value = (0.0, 0.0, 0.0, 1)
em.inputs['Strength'].default_value = 0.0
mix = nt.nodes.new('ShaderNodeMixShader')
tc = nt.nodes.new('ShaderNodeTexCoord')
vec = nt.nodes.new('ShaderNodeVectorMath'); vec.operation = 'LENGTH'
ramp = nt.nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = 0.05
ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
ramp.color_ramp.elements[1].position = 0.45
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

# ---- 5. hanging index sheet: bring it closer / lower so it reads in the wide frame
for ob in list(bpy.data.objects):
    if ob.name.startswith('index_sheet') or ob.name.startswith('thread_'):
        bpy.data.objects.remove(ob, do_unlink=True)
W.hanging_index_sheet(loc=(-1.55, -13.6, -1.15), rotz=0.16, w=2.4, h=3.1)
L = C.light('sheet_fill', 'AREA', loc=(-1.4, -11.6, -0.6), energy=90, color=(1.0, 0.86, 0.68), size=2.0)
C.look_at(L, (-1.55, -13.6, -1.15))

# ---- 6. hanging paper lanterns: glowing warm dots for depth
lan = C.paper('m_lantern', base=(0.95, 0.72, 0.42), rough=0.5)
g = G.Geo('lanterns')
for i in range(9):
    side = -1 if i % 2 else 1
    x = side * (2.15 + (i % 3) * 0.12)
    y = -6.0 - i * 2.2
    z = FLOOR + 2.4 + (i % 4) * 0.9
    g.sphere(0.055, (x, y, z), lan)
lan_ob = g.build()
lan_ob.visible_shadow = False
em = C.emissive('m_lantern_glow', (1.0, 0.62, 0.30), 6.0)
for i in range(9):
    side = -1 if i % 2 else 1
    x = side * (2.15 + (i % 3) * 0.12)
    y = -6.0 - i * 2.2
    z = FLOOR + 2.4 + (i % 4) * 0.9
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.09, location=(x, y, z))
    o = bpy.context.object
    o.name = f'lantern_glow_{i}'
    o.data.materials.append(em)
    o.visible_shadow = False

# ---- 7. floor pool of warm light near the character
L = C.light('floor_pool', 'POINT', loc=(-1.1, -8.6, FLOOR + 0.15), energy=45, color=(1.0, 0.55, 0.28), size=0.6)
L.data.volume_factor = 2.0

# ---- render check frame
sc.render.resolution_x = 960
sc.render.resolution_y = 540
sc.render.resolution_percentage = 100
sc.render.filepath = os.path.join(OUT, 'wide_960_b.png')
t = time.time()
bpy.ops.render.render(write_still=True)
print('ITER_RENDER_OK %.2fs' % (time.time() - t), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(C.MV, 'lookdev.blend'))
