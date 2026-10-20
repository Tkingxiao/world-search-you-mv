"""s09 - FORGET / void_dark: the second "I'm searching" interlude. She floats alone in the dark,
lit only by a cold rim; paper dust drifts. Slow orbit, 85-100mm."""
import bpy, math, os, sys, random

MV = r'D:\Code\Code MV\new-word.search(you)'
sys.path.insert(0, os.path.join(MV, 'mv', 'build'))
import shotkit as K
import core as C
import geo as G

FRAMES = (137.09, 151.84)
FLOOR = K.FLOOR
N = 885


def build():
    K.begin(fog_density=0.058, fog_color=(0.004, 0.018, 0.034),
            ambient=(0.002, 0.007, 0.014), exposure=0.30)
    K.water_slab('void_water', z=FLOOR - 0.05, size=90.0, color=(0.006, 0.014, 0.024))

    ctrl = K.char_actor('serious', (0.50, -9.10, FLOOR + 0.90), face=(0.0, -2.0, FLOOR + 2.2))
    K.char_expr(ctrl, [(1, 'serious', 2.0, 0.0), (280, 'frightened', 1.0, 2.0),
                       (620, 'serious', 2.0, -1.5), (N, 'serious', 2.5, 0.0)])
    root = ctrl['root']
    root.keyframe_insert('location', frame=1)
    root.location = (0.50, -9.10, FLOOR + 1.05)
    root.keyframe_insert('location', frame=N)
    K.ease(root)

    # cold rim from behind
    rim = C.light('void_rim', 'SPOT', loc=(0.55, -13.2, FLOOR + 3.9), energy=2600,
                  color=(0.30, 0.58, 1.0), size=0.35, angle=math.radians(26))
    C.look_at(rim, (0.50, -9.1, FLOOR + 1.95))
    rim.data.volume_factor = 2.0
    # a soft cool key from camera-left so her face is not a pure silhouette
    key = C.light('void_key', 'AREA', loc=(-2.6, -6.4, FLOOR + 2.9), energy=150,
                  color=(0.46, 0.64, 1.0), size=2.6)
    C.look_at(key, (0.50, -9.1, FLOOR + 1.95))
    # faint halo behind her: the shape of a memory she can no longer resolve
    K.glow_orb('void_halo', (0.50, -16.5, FLOOR + 1.85), radius=1.05,
               color=(0.16, 0.34, 0.60), strength=0.55)
    # a distant warm pinprick for contrast
    warm = C.light('void_warm', 'POINT', loc=(-3.4, -14.0, FLOOR + 1.2), energy=9.0,
                   color=(1.0, 0.66, 0.38), size=0.02)

    # drifting paper shards
    rnd = random.Random(33)
    g = G.Geo('void_shards')
    em = C.emissive('m_void_shard', (0.44, 0.40, 0.32), 0.22)
    for i in range(12):
        x = rnd.uniform(-3.0, 3.0)
        y = rnd.uniform(-13.0, -6.0)
        z = FLOOR + rnd.uniform(0.5, 3.4)
        w = rnd.uniform(0.10, 0.26)
        g.plane(1.0, (x, y, z),
                (rnd.uniform(-1.0, 1.0), rnd.uniform(-1.0, 1.0), rnd.uniform(0, 6.28)),
                em, sx=w, sy=w * rnd.uniform(0.5, 1.0))
    sh = g.build()
    sh.visible_shadow = False
    sh.keyframe_insert('location', frame=1)
    sh.location = (0.10, 0, 0.35)
    sh.keyframe_insert('location', frame=N)
    K.ease(sh)

    C.dust('void_dust', count=700, extent=(8.0, 8.0, 5.0), center=(0.2, -9.5, FLOOR + 2.0),
           size=0.010, color=(0.30, 0.44, 0.62), strength=1.6)

    K.cam_path('cam_s09', [
        (1, (-1.70, -5.40, FLOOR + 2.10), (0.50, -9.10, FLOOR + 1.90), 42, 2.6),
        (300, (-0.50, -5.05, FLOOR + 2.20), (0.50, -9.10, FLOOR + 1.92), 44, 2.4),
        (600, (1.30, -5.35, FLOOR + 2.12), (0.50, -9.10, FLOOR + 1.88), 47, 2.2),
        (N, (1.95, -5.65, FLOOR + 2.05), (0.50, -9.10, FLOOR + 1.86), 50, 2.0),
    ])
