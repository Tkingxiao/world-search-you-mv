"""perf_1440p.py - measure 2560x1440 EEVEE render cost on the current lookdev scene."""
import bpy, time, os, json, sys

sc = bpy.context.scene
OUT = r'D:\Code\Code MV\new-word.search(you)\mv\out\perf'
os.makedirs(OUT, exist_ok=True)
sc.render.resolution_x = 2560
sc.render.resolution_y = 1440
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'
cam = bpy.data.objects.get('cam_wide')
if cam:
    sc.camera = cam

res = {}
for samples in (24, 16):
    sc.eevee.taa_render_samples = samples
    ts = []
    for i in range(3):
        sc.frame_set(i + 1)
        sc.render.filepath = os.path.join(OUT, 'perf_s%d_%d.png' % (samples, i))
        t = time.time()
        bpy.ops.render.render(write_still=True)
        ts.append(round(time.time() - t, 3))
    res['samples_%d' % samples] = ts
print('PERF ' + json.dumps(res), flush=True)
