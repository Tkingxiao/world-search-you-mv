"""s11 - EVERYWHERE / storm: the chorus. Paper shards and carp kites fly around her;
she stands in the gale, bending like a cut-out in the wind."""
import bpy, math, os, sys, random

MV = r'D:\Code\Code MV\new-word.search(you)'
sys.path.insert(0, os.path.join(MV, 'mv', 'build'))
import shotkit as K
import core as C
import world_theater as T
import stage as S
import specimens as SP
import geo as G

FRAMES = (179.47, 207.14)
FLOOR = K.FLOOR
N = 1660
CENTER = (0.45, -11.4, FLOOR + 1.9)


def _shard_cloud(name, count, rmin, rmax, zmin, zmax, seed, spin, color):
    rnd = random.Random(seed)
    g = G.Geo(name)
    em = C.emissive('m_' + name, color, 0.30)
    for i in range(count):
        ang = rnd.uniform(0, 6.28)
        rad = rnd.uniform(rmin, rmax)
        x = math.cos(ang) * rad
        y = math.sin(ang) * rad
        z = rnd.uniform(zmin, zmax)
        w = rnd.uniform(0.10, 0.30)
        g.plane(1.0, (x, y, z),
                (rnd.uniform(-1.4, 1.4), rnd.uniform(-1.4, 1.4), rnd.uniform(0, 6.28)),
                em, sx=w, sy=w * rnd.uniform(0.45, 1.0))
    ob = g.build()
    ob.location = CENTER
    ob.visible_shadow = False
    ob.rotation_euler = (0, 0, 0)
    ob.keyframe_insert('rotation_euler', frame=1)
    ob.rotation_euler = (0.10, 0.05, spin)
    ob.keyframe_insert('rotation_euler', frame=N)
    ob.keyframe_insert('location', frame=1)
    ob.location = (CENTER[0], CENTER[1], CENTER[2] + 0.55)
    ob.keyframe_insert('location', frame=N)
    K.ease(ob)
    return ob


def _flying_kites():
    specs = [('kimi', 'kimi / table_2', 0.0, 3.5, 2.55, 1.0),
             ('qwen', 'qwen / eggplant_3', 2.1, 4.1, 2.05, -1.2),
             ('glm', 'glm / cat_2', 4.2, 3.2, 2.75, 1.4)]
    out = []
    for (col, label, a0, rad, dz, speed) in specs:
        x = CENTER[0] + math.cos(a0) * rad
        y = CENTER[1] + math.sin(a0) * rad * 0.7
        coll = SP.build_koinobori(color=col, label_text=label, length=1.05,
                                  location=(x, y, FLOOR + dz),
                                  rotation=(0, 0, math.radians(90)))
        root = SP.root_of(coll)
        if root is None:
            continue
        for i in range(5):
            f = 1 + i * (N - 1) / 4.0
            a = a0 + speed * i * 1.35
            root.location = (CENTER[0] + math.cos(a) * rad,
                             CENTER[1] + math.sin(a) * rad * 0.7,
                             FLOOR + dz + 0.22 * math.sin(i * 1.7))
            root.rotation_euler = (0, 0, math.radians(90) + a + 1.57)
            root.keyframe_insert('location', frame=int(f))
            root.keyframe_insert('rotation_euler', frame=int(f))
        K.ease(root)
        out.append(root)
    return out


def build():
    K.begin(fog_density=0.040, fog_color=(0.010, 0.040, 0.070),
            ambient=(0.006, 0.020, 0.034), exposure=0.26)
    T.theatre(seed=3)
    try:
        m = bpy.data.materials['m_window']
        C._bsdf(m.node_tree).inputs['Emission Strength'].default_value = 2.4
    except Exception:
        pass

    ctrl = K.char_actor('serious', (0.55, -11.2, FLOOR))
    K.char_expr(ctrl, [(1, 'serious', 8.0, 0.0), (420, 'starry', 12.0, 2.0),
                       (900, 'cheerful', 9.0, -2.0), (1300, 'cheerful', 14.0, 1.0),
                       (N, 'serious', 11.0, 0.0)])
    K.char_pose(ctrl, [(1, (0.55, -11.2, FLOOR), (8.0, 0.0), 1.0),
                       (800, (0.55, -11.2, FLOOR + 0.08), (12.0, 2.0), 1.0),
                       (N, (0.55, -11.2, FLOOR + 0.02), (11.0, 0.0), 1.0)])

    _shard_cloud('storm_a', 110, 2.4, 7.5, 0.2, 3.6, 5, 2.2 * math.pi, (0.60, 0.55, 0.42))
    _shard_cloud('storm_b', 90, 4.5, 11.0, 0.8, 5.0, 9, -1.6 * math.pi, (0.52, 0.48, 0.38))
    _shard_cloud('storm_c', 70, 1.6, 5.0, 1.6, 5.2, 13, 3.0 * math.pi, (0.68, 0.62, 0.48))
    _flying_kites()
    S.foreground_papers(seed=23, n=16)

    # cold gale from behind, warm key on her
    back = C.light('storm_back', 'AREA', loc=(0.4, -16.5, FLOOR + 4.2), energy=900,
                   color=(0.36, 0.62, 1.0), size=6.0)
    C.look_at(back, (0.5, -11.0, FLOOR + 1.4))
    shaft = C.light('storm_shaft', 'SPOT', loc=(-1.6, -8.2, FLOOR + 8.4), energy=7000,
                    color=(0.42, 0.70, 1.0), size=0.8, angle=math.radians(30))
    C.look_at(shaft, (0.2, -12.0, FLOOR + 1.0))
    shaft.data.volume_factor = 3.0

    K.cam_path('cam_s11', [
        (1, (2.95, -6.05, FLOOR + 1.78), (0.35, -11.2, FLOOR + 1.55), 24, 3.2),
        (420, (2.35, -6.35, FLOOR + 1.62), (0.30, -11.2, FLOOR + 1.50), 28, 3.0),
        (860, (1.55, -7.05, FLOOR + 1.56), (0.35, -11.2, FLOOR + 1.48), 32, 2.8),
        (1260, (1.05, -7.65, FLOOR + 1.50), (0.40, -11.2, FLOOR + 1.46), 35, 2.8),
        (N, (0.90, -8.30, FLOOR + 1.46), (0.42, -11.2, FLOOR + 1.44), 38, 2.8),
    ])
