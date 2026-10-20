"""theater_test.py - build the paper theatre set in the GUI and render a 960x540 check."""
import bpy, sys, os, math, time
sys.path.insert(0, r'D:\Code\Code MV\new-word.search(you)\mv\build')
for _m in ('core', 'world', 'geo', 'world_theater'):
    sys.modules.pop(_m, None)
import core as C
import world_theater as T
FLOOR = -6.0
OUT = r'D:\Code\Code MV\new-word.search(you)\mv\out\lookdev'
os.makedirs(OUT, exist_ok=True)
sc = C.reset_soft()
C.setup_render(samples=24, w=2560, h=1440, glare=True)
sc.view_settings.exposure = 0.20
C.fog_world(density=0.020, color=(0.010, 0.048, 0.080), ambient=(0.004, 0.014, 0.026))

objs = T.theatre(seed=3)

# ---- character puppet
front, cmat, back = C.paper_cutout(os.path.join(C.TEX, 'galgame', 'whale-cheerful.webp'),
                                   height=1.75, loc=(0.0, -11.0, FLOOR),
                                   emission_strength=0.06, name='whale_paper')
# contact shadow
bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0.0, -11.0, FLOOR + 0.004))
sh = bpy.context.object
sh.name = 'contact_shadow'
sh.scale = (1.5, 0.8, 1)
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
ramp.color_ramp.elements[0].position = 0.05
ramp.color_ramp.elements[0].color = (0.85, 0.85, 0.85, 1)
ramp.color_ramp.elements[1].position = 0.42
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

# ---- stage lighting: warm front spot, cold back rim, soft fill
tgt = bpy.data.objects.new('key_tgt', None); bpy.context.collection.objects.link(tgt)
tgt.location = (0.0, -11.0, FLOOR + 1.1)
L = C.light('stage_key', 'SPOT', loc=(-2.6, -7.6, FLOOR + 4.4), energy=2600,
            color=(1.0, 0.70, 0.45), size=0.3, angle=math.radians(36), target=tgt)
L.data.volume_factor = 1.4
L = C.light('stage_rim', 'SPOT', loc=(1.4, -15.0, FLOOR + 3.6), energy=2600,
            color=(0.20, 0.55, 1.0), size=0.2, angle=math.radians(30))
C.look_at(L, (0.0, -11.0, FLOOR + 1.2))
L.data.volume_factor = 1.8
L = C.light('stage_fill', 'AREA', loc=(2.8, -5.4, FLOOR + 2.6), energy=120,
            color=(0.55, 0.72, 1.0), size=3.0)
C.look_at(L, (0.0, -11.0, FLOOR + 1.0))
# top cold shaft through haze
T_shaft = C.light('top_shaft', 'SPOT', loc=(0.2, -11.0, FLOOR + 8.0), energy=9000,
                  color=(0.45, 0.72, 1.0), size=0.2, angle=math.radians(16))
C.look_at(T_shaft, (0.0, -11.0, FLOOR))
T_shaft.data.volume_factor = 4.0
C.dust('dust', count=700, extent=(9, 12, 7), center=(0, -11, FLOOR + 3.2), size=0.007,
       color=(0.60, 0.85, 1.0), strength=2.5)

# ---- camera: from the balcony, looking down at the puppet
cam = C.camera('cam_theatre', lens=42, loc=(-0.25, -2.6, FLOOR + 2.05),
               target=(0.0, -11.0, FLOOR + 0.95), dof=True, fstop=2.4)
sc.camera = cam
sc.frame_set(1)

for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'RENDERED'
                space.overlay.show_overlays = False
                space.region_3d.view_perspective = 'CAMERA'

sc.render.resolution_x = 960
sc.render.resolution_y = 540
sc.render.resolution_percentage = 100
sc.render.filepath = os.path.join(OUT, 'theater_960.png')
t = time.time()
bpy.ops.render.render(write_still=True)
print('THEATER_RENDER_OK %.2fs objs=%d' % (time.time() - t, len(bpy.data.objects)), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(C.MV, 'lookdev.blend'))
