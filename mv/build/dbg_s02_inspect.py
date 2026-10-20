"""dbg_s02_inspect.py - build s02 and dump index page / text object state."""
import bpy, sys, math
sys.path.insert(0, r'D:\Code\Code MV\new-word.search(you)\mv\build')
for _m in ('core', 'world', 'geo', 'world_theater', 'shotkit', 'stage', 'specimens', 'char_paper', 'shot_s02'):
    sys.modules.pop(_m, None)
import shot_s02

shot_s02.build()
print('=== OBJECTS near index page ===')
for ob in bpy.data.objects:
    if ob.name.startswith('idx_') or ob.name == 'index_page':
        mw = ob.matrix_world
        mats = [m.name if m else None for m in ob.data.materials] if hasattr(ob.data, 'materials') else []
        print('OBJ %-12s loc=(%.2f,%.2f,%.2f) mwY=%.2f mats=%s hide=%s vis_shadow=%s type=%s'
              % (ob.name, ob.location.x, ob.location.y, ob.location.z,
                 mw.translation.y, mats, ob.hide_render, ob.visible_shadow, ob.type))
print('=== MATERIAL m_index_ink ===')
m = bpy.data.materials.get('m_index_ink')
if m and m.node_tree:
    for n in m.node_tree.nodes:
        print('  node', n.type, n.name)
        if n.type == 'EMISSION':
            print('    color', tuple(n.inputs['Color'].default_value), 'strength', n.inputs['Strength'].default_value)
print('=== MATERIAL m_index_page ===')
m2 = bpy.data.materials.get('m_index_page')
if m2 and m2.node_tree:
    for n in m2.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            print('    base', tuple(n.inputs['Base Color'].default_value), 'emis', tuple(n.inputs['Emission Color'].default_value),
                  'emisS', n.inputs['Emission Strength'].default_value)
print('=== lights ===')
for ob in bpy.data.objects:
    if ob.type == 'LIGHT':
        print('LIGHT %-12s %s energy=%.1f' % (ob.name, ob.data.type, ob.data.energy))
print('DBG_INSPECT_DONE')
