"""Measure depsgraph evaluation cost of a shot build (no render).

usage (headless): blender -b --factory-startup -P mv/build/probe_eval.py -- --shot s05
"""
import bpy, sys, os, time

MV = r'D:\Code\Code MV\new-word.search(you)'
sys.path.insert(0, os.path.join(MV, 'mv', 'build'))

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

shot = args.get('shot', 's05')
import importlib
mod = importlib.import_module('shot_' + shot)
t = time.time()
mod.build()
print('BUILD %.2fs' % (time.time() - t), flush=True)

deps = bpy.context.evaluated_depsgraph_get()
print('objects=%d meshes=%d curves=%d lights=%d' % (
    len(bpy.data.objects), len(bpy.data.meshes), len(bpy.data.curves),
    len(bpy.data.lights)), flush=True)
tris = 0
for o in bpy.data.objects:
    if o.type == 'MESH':
        tris += sum(len(p.vertices) - 2 for p in o.data.polygons)
print('base_tris=%d' % tris, flush=True)

# measure evaluated geometry cost
for k in range(3):
    t = time.time()
    deps.update()
    n = len(deps.objects)
    ev = 0
    for obj in deps.objects:
        if obj.type == 'MESH' and obj.data is not None:
            ev += len(obj.data.loop_triangles) if hasattr(obj.data, 'loop_triangles') else 0
    print('eval %d: %.1f ms objects=%d' % (k, (time.time() - t) * 1000, n), flush=True)

# measure frame_set cost over 5 frames
sc = bpy.context.scene
t = time.time()
for fr in range(1, 7):
    sc.frame_set(fr)
    deps.update()
print('frame_set+eval avg: %.1f ms/frame' % ((time.time() - t) * 1000 / 6.0), flush=True)

mods = 0
for o in bpy.data.objects:
    mods += len(o.modifiers)
print('total_modifiers=%d' % mods, flush=True)
