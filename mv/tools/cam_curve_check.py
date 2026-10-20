"""Numerically check that a shot's camera motion is smooth (no handheld noise left).

Builds the shot (no rendering), steps the scene frame by frame and reports the
first/second differences of the camera position + rotation. A residual high-frequency
component would show up as a large second difference (jerk) relative to the first.

Usage:
  blender -b --factory-startup -P mv/tools/cam_curve_check.py -- --shot s03 --frames 1 240
"""
import argparse
import math
import os
import sys

import bpy
from mathutils import Vector

MV = r'D:\Code\Code MV\new-word.search(you)'
sys.path.insert(0, os.path.join(MV, 'mv', 'build'))

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument('--shot', required=True)
ap.add_argument('--frames', nargs=2, type=int, default=[1, 240])
a = ap.parse_args(argv)

for _m in list(sys.modules):
    if _m in ('shotkit',) or _m.startswith('shot_'):
        sys.modules.pop(_m, None)
import importlib
mod = importlib.import_module('shot_' + a.shot)
mod.build()
sc = bpy.context.scene
cam = sc.camera
assert cam is not None, 'no scene camera'

f0, f1 = a.frames
locs, quats = [], []
for f in range(f0, f1 + 1):
    sc.frame_set(f)
    mw = cam.matrix_world.copy()
    locs.append(mw.to_translation())
    quats.append(mw.to_quaternion())

dl = [ (locs[i] - locs[i - 1]).length for i in range(1, len(locs)) ]
dq = [ quats[i].rotation_difference(quats[i - 1]).angle for i in range(1, len(quats)) ]
# second difference = residual high-frequency component
jl = [ abs(dl[i] - dl[i - 1]) for i in range(1, len(dl)) ]
jq = [ abs(dq[i] - dq[i - 1]) for i in range(1, len(dq)) ]


def stats(v):
    s = sorted(v)
    n = len(s)
    return (sum(s) / n, s[int(n * 0.95)] if n > 1 else s[0], s[-1])


ml, p95l, mxl = stats(jl)
mq, p95q, mxq = stats(jq)
print('CAM_CHECK %s frames=%d..%d' % (a.shot, f0, f1), flush=True)
print('  step_loc  mean=%.5f p95=%.5f max=%.5f m' % stats(dl), flush=True)
print('  step_rot  mean=%.6f p95=%.6f max=%.6f rad' % stats(dq), flush=True)
print('  jerk_loc  mean=%.6f p95=%.6f max=%.6f m  (should be << step)' % (ml, p95l, mxl), flush=True)
print('  jerk_rot  mean=%.7f p95=%.7f max=%.7f rad' % (mq, p95q, mxq), flush=True)
ratio = (p95l / p95l) if p95l else 0
print('  VERDICT %s' % ('SMOOTH' if (p95l < 0.004 and p95q < 0.002) else 'JITTERY'), flush=True)
