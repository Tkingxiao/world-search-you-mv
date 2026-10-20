"""dbg_s02_ab.py - A/B: render s02 frame 250 with page hidden / text hidden."""
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

for tag, hide_page, hide_text in (('nopage', True, False), ('notext', False, True)):
    for ob in bpy.data.objects:
        if ob.name == 'index_page':
            ob.hide_render = hide_page
        elif ob.name.startswith('idx_'):
            ob.hide_render = hide_text
    sc.render.filepath = OUT + r'\dbg_s02_%s.png' % tag
    bpy.ops.render.render(write_still=True)
    print('DBG_AB', tag)
print('DBG_AB_DONE')
