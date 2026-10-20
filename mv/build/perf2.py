"""perf2.py - 1440p perf matrix: samples / volumetrics / output format."""
import bpy, time, os, json

sc = bpy.context.scene
OUT = r'D:\Code\Code MV\new-word.search(you)\mv\out\perf'
os.makedirs(OUT, exist_ok=True)
sc.render.resolution_x = 2560
sc.render.resolution_y = 1440
sc.render.resolution_percentage = 100
try:
    sc.eevee.shadow_pool_size = 4096
    print('shadow_pool_size set to', sc.eevee.shadow_pool_size, flush=True)
except Exception as e:
    print('shadow pool err', e, flush=True)
cam = bpy.data.objects.get('cam_wide')
if cam:
    sc.camera = cam

def timeit(n=2):
    ts = []
    for i in range(n):
        sc.frame_set(i + 1)
        t = time.time()
        bpy.ops.render.render(write_still=False)
        ts.append(round(time.time() - t, 3))
    return ts

res = {}
# PNG baseline @12 samples, fog on
sc.eevee.taa_render_samples = 12
sc.render.image_settings.file_format = 'PNG'
sc.render.filepath = os.path.join(OUT, 'x.png')
res['png_s12_fog'] = timeit()

# fog off: unlink volume from world output
w = sc.world
nt = w.node_tree
vol_links = [l for l in nt.links if l.to_socket.name == 'Volume']
for l in vol_links:
    nt.links.remove(l)
res['png_s12_nofog'] = timeit()

# restore fog
out_node = [n for n in nt.nodes if n.type == 'OUTPUT_WORLD'][0]
# find volume node
vol_node = None
for n in nt.nodes:
    if n.type == 'VOLUME_SCATTER':
        vol_node = n
        break
if vol_node:
    nt.links.new(vol_node.outputs['Volume'], out_node.inputs['Volume'])

# ffmpeg mp4 output @12 samples fog on
sc.render.image_settings.file_format = 'FFMPEG'
sc.render.ffmpeg.format = 'MPEG4'
sc.render.ffmpeg.codec = 'H264'
sc.render.ffmpeg.constant_rate_factor = 'HIGH'
sc.render.ffmpeg.ffmpeg_preset = 'GOOD'
sc.render.ffmpeg.gopsize = 30
sc.render.filepath = os.path.join(OUT, 'perf_out.mp4')
ts = []
sc.frame_start = 1
sc.frame_end = 2
t = time.time()
bpy.ops.render.render(animation=True)
ts.append(round(time.time() - t, 3))
res['mp4_s12_fog_2f'] = ts
print('PERF2 ' + json.dumps(res), flush=True)
