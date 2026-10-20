"""perf3.py - render N frames at 1440p to MP4; args: --start --end --tag"""
import bpy, time, os, sys, json

argv = sys.argv
args = {}
if '--' in argv:
    rest = argv[argv.index('--') + 1:]
    for i in range(0, len(rest) - 1, 2):
        args[rest[i].lstrip('-')] = rest[i + 1]
start = int(args.get('start', 1))
end = int(args.get('end', 15))
tag = args.get('tag', 'a')
OUT = r'D:\Code\Code MV\new-word.search(you)\mv\out\perf'
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
sc.render.resolution_x = 2560
sc.render.resolution_y = 1440
sc.render.resolution_percentage = 100
sc.eevee.taa_render_samples = 12
sc.render.image_settings.file_format = 'FFMPEG'
sc.render.ffmpeg.format = 'MPEG4'
sc.render.ffmpeg.codec = 'H264'
sc.render.ffmpeg.constant_rate_factor = 'HIGH'
sc.render.ffmpeg.ffmpeg_preset = 'GOOD'
sc.render.fps = 60
sc.frame_start = start
sc.frame_end = end
sc.render.filepath = os.path.join(OUT, 'cont_%s.mp4' % tag)
t = time.time()
bpy.ops.render.render(animation=True)
dt = time.time() - t
print('PERF3 ' + json.dumps({'tag': tag, 'frames': end - start + 1, 'sec': round(dt, 2),
                             'per_frame': round(dt / (end - start + 1), 3)}), flush=True)
