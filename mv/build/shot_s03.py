"""s03 - SORT / bubble_shaft: she floats up through a column of memory bubbles."""
import bpy, math, os, sys, random

MV = r'D:\Code\Code MV\new-word.search(you)'
sys.path.insert(0, os.path.join(MV, 'mv', 'build'))
import shotkit as K
import core as C
import world_theater as T
import geo as G

FRAMES = (14.36, 28.32)
FLOOR = K.FLOOR
CHAR = (0.55, -11.2, FLOOR)


def _bubble(name, loc, r, seed):
    """Thin glass bubble with a warm rim."""
    m = C.glass('m_bubble_%s' % name, base=(0.75, 0.86, 1.0), rough=0.02)
    m.surface_render_method = 'BLENDED'
    bsdf = C._bsdf(m.node_tree)
    bsdf.inputs['Alpha'].default_value = 0.16
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=24, ring_count=16)
    ob = bpy.context.object
    ob.name = name
    ob.data.materials.append(m)
    ob.visible_shadow = False
    return ob


def _photo_bubble(name, loc, r, seed):
    b = _bubble(name, loc, r, seed)
    # a tiny memory photo inside
    rnd = random.Random(seed)
    pm = C.emissive('m_photo_%s' % name, (0.85, 0.72, 0.52), 1.4)
    ph = C.plane(name + '_photo', size=1.0, loc=(loc[0], loc[1], loc[2]),
                 rot=(math.radians(90), 0, rnd.uniform(-0.4, 0.4)), mat=pm)
    ph.scale = (r * 0.95, r * 0.7, 1)
    ph.parent = b
    ph.location = (0, 0, 0)
    ph.visible_shadow = False
    return b


def build():
    K.begin(fog_density=0.026, fog_color=(0.008, 0.035, 0.062),
            exposure=0.22)
    T.theatre(seed=3)
    K.S.foreground_papers(seed=11, n=10)
    # character
    ctrl = K.char_actor('starry', loc=CHAR, height=1.75,
                        face=(CHAR[0] + 0.2, CHAR[1] + 3.0, CHAR[2] + 1.1))
    K.char_expr(ctrl, [(1, 'starry'), (242, 'cheerful'), (578, 'serious')])
    # she rises slowly
    root = ctrl['root']
    z0 = CHAR[2]
    root.location = (CHAR[0], CHAR[1], z0)
    root.keyframe_insert('location', frame=1)
    root.location = (CHAR[0] + 0.10, CHAR[1], z0 + 0.55)
    root.keyframe_insert('location', frame=838)
    K.ease(root)

    # memory bubbles rising through the shaft
    rnd = random.Random(4)
    bubs = []
    for i in range(16):
        x = rnd.uniform(-1.9, 1.9)
        y = rnd.uniform(-13.4, -9.4)
        z = FLOOR + rnd.uniform(0.2, 4.2)
        r = rnd.uniform(0.10, 0.30)
        b = _photo_bubble('bub_%02d' % i, (x, y, z), r, 100 + i)
        bubs.append((b, rnd.uniform(0.35, 0.85), rnd.uniform(0.0, 6.28)))
    for (b, sp, ph) in bubs:
        z = b.location.z
        b.keyframe_insert('location', frame=1)
        b.location = (b.location.x + 0.10 * math.sin(ph),
                      b.location.y, z + sp * 14.0)
        b.keyframe_insert('location', frame=838)
        b.keyframe_insert('rotation_euler', frame=1)
        b.rotation_euler = (0, 0, ph + 1.2)
        b.keyframe_insert('rotation_euler', frame=838)
        K.ease(b)

    # lights: warm key, cold rim, window spill
    K.S.lighting('default')
    L = C.light('bub_top', 'SPOT', loc=(0.9, -9.4, FLOOR + 7.2), energy=2600,
                color=(0.55, 0.78, 1.0), size=0.3, angle=math.radians(16))
    C.look_at(L, (0.6, -11.0, FLOOR + 0.4))
    L.data.volume_factor = 3.2

    # camera: low 28mm, tracks up with her
    K.cam_path('cam_s03', [
        (1, (0.35, -5.2, FLOOR + 0.22), (0.55, -11.2, FLOOR + 0.85), 28, 4.0),
        (420, (0.62, -5.9, FLOOR + 0.75), (0.60, -11.2, FLOOR + 1.25), 30, 3.2),
        (838, (0.70, -6.6, FLOOR + 1.15), (0.55, -11.2, FLOOR + 1.55), 32, 2.8),
    ])

