"""set_theater.py - build the full paper theatre set in the GUI, render 3 check frames, save lookdev.blend."""
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
sc.view_settings.exposure = 0.25
C.fog_world(density=0.018, color=(0.010, 0.048, 0.080), ambient=(0.004, 0.014, 0.026))

objs = T.theatre(seed=3)

# ---- character puppet, standing just right of her desk
CHAR = (0.55, -11.2, FLOOR)
front, cmat, back = C.paper_cutout(os.path.join(C.TEX, 'galgame', 'whale-cheerful.webp'),
                                   height=1.75, loc=CHAR,
                                   emission_strength=0.06, name='whale_paper')

# contact shadow
bpy.ops.mesh.primitive_plane_add(size=1.0, location=(CHAR[0], CHAR[1], FLOOR + 0.004))
sh = bpy.context.object
sh.name = 'contact_shadow'
sh.scale = (1.4, 0.75, 1)
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

# ---- lighting: warm key from front-left, cold rim from behind-right, soft blue fill
tgt = bpy.data.objects.new('key_tgt', None); bpy.context.collection.objects.link(tgt)
tgt.location = (CHAR[0], CHAR[1], FLOOR + 1.1)
L = C.light('stage_key', 'SPOT', loc=(CHAR[0] - 3.4, CHAR[1] + 3.4, FLOOR + 4.6), energy=3200,
            color=(1.0, 0.66, 0.40), size=0.25, angle=math.radians(40), target=tgt)
L.data.volume_factor = 2.2
L = C.light('stage_rim', 'SPOT', loc=(CHAR[0] + 1.8, CHAR[1] - 4.2, FLOOR + 3.8), energy=3000,
            color=(0.18, 0.52, 1.0), size=0.2, angle=math.radians(26))
C.look_at(L, (CHAR[0], CHAR[1], FLOOR + 1.2))
L.data.volume_factor = 2.6
L = C.light('stage_fill', 'AREA', loc=(CHAR[0] + 3.2, CHAR[1] + 4.6, FLOOR + 2.6), energy=140,
            color=(0.50, 0.70, 1.0), size=3.5)
C.look_at(L, (CHAR[0], CHAR[1], FLOOR + 1.0))
# cool top shaft through haze
L = C.light('top_shaft', 'SPOT', loc=(CHAR[0], CHAR[1], FLOOR + 8.5), energy=7000,
            color=(0.42, 0.70, 1.0), size=0.2, angle=math.radians(15))
C.look_at(L, (CHAR[0], CHAR[1], FLOOR))
L.data.volume_factor = 3.2
# warm pool in front of the desk
L = C.light('desk_pool', 'POINT', loc=(-2.4, -9.4, FLOOR + 1.5), energy=90,
            color=(1.0, 0.62, 0.34), size=0.35)
L.data.volume_factor = 1.2
# faint window light spill
L = C.light('window_spill', 'AREA', loc=(0.0, -20.4, FLOOR + 2.9), energy=420,
            color=(0.62, 0.80, 1.0), size=4.0)
C.look_at(L, (0.0, -11.0, FLOOR + 1.0))
C.dust('dust', count=800, extent=(9, 13, 7), center=(0, -12, FLOOR + 3.0), size=0.007,
       color=(0.60, 0.85, 1.0), strength=2.2)

# ---- cameras
cams = {}
cams['wide'] = C.camera('cam_wide', lens=40, loc=(0.9, -2.6, FLOOR + 1.55),
                        target=(-0.1, -11.6, FLOOR + 1.30), dof=True, fstop=2.8)
cams['three_q'] = C.camera('cam_three_q', lens=55, loc=(-4.6, -7.4, FLOOR + 1.75),
                           target=(0.4, -11.6, FLOOR + 1.25), dof=True, fstop=2.2)
cams['close'] = C.camera('cam_close', lens=85, loc=(-0.8, -7.0, FLOOR + 1.45),
                         target=(0.55, -11.2, FLOOR + 1.15), dof=True, fstop=1.8)
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
for name, cam in cams.items():
    sc.camera = cam
    sc.frame_set(1)
    sc.render.filepath = os.path.join(OUT, 'set_%s_960.png' % name)
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print('RENDER %s %.2fs' % (name, time.time() - t), flush=True)
sc.camera = cams['wide']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(C.MV, 'lookdev.blend'))
print('SET_OK objs=%d' % len(bpy.data.objects), flush=True)
