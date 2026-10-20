"""dbg_s02_f.py - emission strength sweep on index text."""
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
mat = bpy.data.materials['m_index_ink']
em = next(n for n in mat.node_tree.nodes if n.type == 'EMISSION')
print('EMIS before', em.inputs['Strength'].default_value, 'blend', mat.surface_render_method, 'alpha', mat.diffuse_color[3] if hasattr(mat, 'diffuse_color') else '?')
for s in (5.0, 10.0, 20.0):
    em.inputs['Strength'].default_value = s
    sc.render.filepath = OUT + r'\dbg_s02_e%03d.png' % int(s)
    bpy.ops.render.render(write_still=True)
    print('DBG emis', s)
print('DBG_F_DONE')
