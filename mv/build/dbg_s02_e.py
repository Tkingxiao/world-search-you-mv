"""dbg_s02_e.py - three variants to pin down why glyphs look dark."""
import bpy, sys
sys.path.insert(0, r'D:\Code\Code MV\new-word.search(you)\mv\build')
for _m in ('core', 'world', 'geo', 'world_theater', 'shotkit', 'stage', 'specimens', 'char_paper', 'shot_s02'):
    sys.modules.pop(_m, None)
import shot_s02

shot_s02.build()
sc = bpy.context.scene
sc.frame_set(250)
sc.render.resolution_x = 960
sc.render.resolution_y = 540
OUT = r'D:\Code\Code MV\new-word.search(you)\mv\out\lookdev'
pg = bpy.data.objects['index_page']

# A: text emission strength 100
mat = bpy.data.materials['m_index_ink']
em = next(n for n in mat.node_tree.nodes if n.type == 'EMISSION')
em.inputs['Strength'].default_value = 100.0
sc.render.filepath = OUT + r'\dbg_s02_emis100.png'
bpy.ops.render.render(write_still=True)
print('DBG emis100')

# B: restore strength, hide page from camera only
em.inputs['Strength'].default_value = 5.0
pg.visible_camera = False
sc.render.filepath = OUT + r'\dbg_s02_pgnocam.png'
bpy.ops.render.render(write_still=True)
print('DBG pgnocam')

# C: page back to camera, move all text 1.4m toward camera
pg.visible_camera = True
for ob in bpy.data.objects:
    if ob.name.startswith('idx_'):
        ob.location.y = -10.0
sc.render.filepath = OUT + r'\dbg_s02_txtnear.png'
bpy.ops.render.render(write_still=True)
print('DBG txtnear')
print('DBG_E_DONE')
