"""render_shot.py - build & render one shot module.

Usage (via blender_rt_headless --script_file this --args "..."):
  --shot s06                       # full 1080p60 10spp mp4 -> mv/out/shots/s06.mp4
  --shot s06 --still 120 --png mv/out/lookdev/s06_a.png
  --shot s06 --frames 1 240        # override frame range
  --shot s06 --blend               # also save mv/out/shots/s06.blend

The film render profile is fixed: 1920x1080 / 60fps / 10 samples.
"""
import bpy, sys, os, time, importlib, json

MV = r'D:\Code\Code MV\new-word.search(you)'
BUILD = os.path.join(MV, 'mv', 'build')
if BUILD not in sys.path:
    sys.path.insert(0, BUILD)

argv = sys.argv
args = {}
if '--' in argv:
    rest = argv[argv.index('--') + 1:]
    i = 0
    while i < len(rest):
        k = rest[i].lstrip('-')
        if i + 1 < len(rest) and not rest[i + 1].startswith('--'):
            args[k] = rest[i + 1]
            i += 2
        else:
            args[k] = '1'
            i += 1

shot = args.get('shot', 's01')
print('RENDER_SHOT %s args=%s' % (shot, json.dumps(args)), flush=True)

for _m in list(sys.modules):
    if _m in ('shotkit',) or _m.startswith('shot_'):
        sys.modules.pop(_m, None)
import shotkit as K

mod = importlib.import_module('shot_' + shot)
t0 = time.time()
mod.build()
print('BUILD_DONE %.1fs' % (time.time() - t0), flush=True)

f0, f1 = 1, int(round(mod.FRAMES[1] * K.FPS)) - int(round(mod.FRAMES[0] * K.FPS))
if 'frames' in args:
    f0, f1 = int(args['frames']), int(args.get('frames2', f1))

if 'still' in args or 'stills' in args:
    sc = bpy.context.scene
    sc.render.resolution_x = K.W
    sc.render.resolution_y = K.H
    sc.render.resolution_percentage = 100
    sc.eevee.taa_render_samples = K.SAMPLES
    sc.render.image_settings.file_format = 'PNG'
    if 'stills' in args:
        frames = [int(x) for x in str(args['stills']).split(',') if x.strip()]
        outs = [os.path.join(MV, 'mv', 'out', 'lookdev', '%s_f%04d.png' % (shot, f))
                for f in frames]
    else:
        frames = [int(args['still'])]
        outs = [args.get('png', os.path.join(MV, 'mv', 'out', 'lookdev', shot + '.png'))]
    for fr, out in zip(frames, outs):
        sc.frame_set(fr)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        sc.render.filepath = out
        t = time.time()
        bpy.ops.render.render(write_still=True)
        print('STILL %s %.1fs' % (out, time.time() - t), flush=True)
elif 'blend' in args:
    K.save_blend(os.path.join(MV, 'mv', 'out', 'shots', shot + '.blend'))
else:
    out = os.path.join(K.OUT, shot + '.mp4')
    K.render_mp4(out, f0, f1, w=K.W, h=K.H, samples=K.SAMPLES)
