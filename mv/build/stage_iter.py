"""stage_iter.py - rebuild the stage with the latest tweaks and render check frames."""
import bpy, sys, os
sys.path.insert(0, r'D:\Code\Code MV\new-word.search(you)\mv\build')
for _m in ('core', 'world', 'geo', 'world_theater', 'stage'):
    sys.modules.pop(_m, None)
import core as C
import stage as S

OUT = r'D:\Code\Code MV\new-word.search(you)\mv\out\lookdev'
sc = C.reset_soft()
C.setup_render(samples=24, w=2560, h=1440, glare=True)
sc.view_settings.exposure = 0.30
C.fog_world(density=0.020, color=(0.009, 0.042, 0.075), ambient=(0.004, 0.012, 0.024))
objs = S.build_stage(char='cheerful', window_strength=1.10)
S.lighting('default')
S.foreground_papers()
cams = S.cameras()
S.render_frames(cams, ['wide', 'three_q', 'close'], OUT, tag='_v3')
sc.camera = cams['wide']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(C.MV, 'lookdev.blend'))
print('ITER_OK objs=%d' % len(bpy.data.objects), flush=True)
