"""dbg_s02_d.py - z-order experiments on index page vs text."""
import bpy, sys, math
sys.path.insert(0, r'D:\Code\Code MV\new-word.search(you)\mv\build')
for _m in ('core', 'world', 'geo', 'world_theater', 'shotkit', 'stage', 'specimens', 'char_paper', 'shot_s02'):
    sys.modules.pop(_m, None)
import shot_s02
import core as C

shot_s02.build()
sc = bpy.context.scene
sc.frame_set(250)
sc.render.resolution_x = 960
sc.render.resolution_y = 540
OUT = r'D:\Code\Code MV\new-word.search(you)\mv\out\lookdev'
pg = bpy.data.objects['index_page']

# A: page moved 1.2m further away
pg.location.y = -12.6
sc.render.filepath = OUT + r'\dbg_s02_pgfar.png'
bpy.ops.render.render(write_still=True)
print('DBG pgfar')

# B: page back to original, but material = pure black emission (opaque dark)
pg.location.y = -11.40
m = bpy.data.materials['m_index_page']
nt = m.node_tree
nt.nodes.clear()
out = nt.nodes.new('ShaderNodeOutputMaterial')
em = nt.nodes.new('ShaderNodeEmission')
em.inputs['Color'].default_value = (0.0, 0.0, 0.0, 1)
em.inputs['Strength'].default_value = 1.0
nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
sc.render.filepath = OUT + r'\dbg_s02_pgblack.png'
bpy.ops.render.render(write_still=True)
print('DBG pgblack')
print('DBG_D_DONE')
