"""gui_show.py - build the paper-theatre stage inside the live GUI Blender so the
user can watch the set in the viewport (GUI session only; headless renders use
render_shot.py).  Run via blender_rt_do(file=...).
"""
import bpy
import os
import sys

MV = r'D:\Code\Code MV\new-word.search(you)'
sys.path.insert(0, os.path.join(MV, 'mv', 'build'))
for _m in ('core', 'world', 'geo', 'stage', 'world_theater', 'shotkit',
           'char_paper', 'specimens'):
    sys.modules.pop(_m, None)

import core as C  # noqa: E402

C.reset_soft()
C.setup_render(samples=8, w=2560, h=1440)

import stage as S  # noqa: E402

sc = bpy.context.scene
S.build_stage(char='cheerful', window_strength=1.05)
S.foreground_papers()
S.lighting('default')
cams = S.cameras()
cam = cams['wide']
sc.camera = cam
sc.frame_set(1)

# point the user's viewport at the shot camera, shaded like the render
for area in bpy.context.screen.areas:
    if area.type != 'VIEW_3D':
        continue
    sp = area.spaces[0]
    sp.region_3d.view_perspective = 'CAMERA'
    try:
        sp.shading.type = 'RENDERED'
        sp.shading.use_scene_lights = True
        sp.shading.use_scene_world = True
    except Exception:
        pass
    try:
        sp.use_screen_render = False
    except Exception:
        pass

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(MV, 'mv', 'lookdev.blend'))
print('GUI SCENE READY objects=%d lights=%d' % (
    len(bpy.data.objects), len(bpy.data.lights)))
