"""s12 - MERGE / bridge: a bucket of love on a plinth; she is cut into paper shards, the shards
become a vortex, and out of the vortex rises the paper whale (the merged self)."""
import bpy, math, os, sys, random

MV = r'D:\Code\Code MV\new-word.search(you)'
sys.path.insert(0, os.path.join(MV, 'mv', 'build'))
import shotkit as K
import core as C
import world_theater as T
import stage as S
import specimens as SP
import geo as G

FRAMES = (207.14, 233.77)
FLOOR = K.FLOOR
N = 1598
WHALE = os.path.join(MV, 'mv', 'assets', 'whale_silhouette.png')


def _dim_all(factor=0.62):
    """Scale down every light except the tiny practicals (keeps the storm from blowing out)."""
    for L in bpy.data.lights:
        if L.name.startswith(('stage_key2', 'stage_shaft2', 'stage_fill2', 'window_beam2',
                              'stage_rim2', 'bounce2', 'window_spill2', 'floor_pool2')):
            L.energy *= factor


def _bucket(loc):
    coll = SP.build_bucket(location=loc, scale=1.0)
    root = SP.root_of(coll)
    # glowing love inside the bucket
    orb = K.glow_orb('love_orb', (loc[0], loc[1], loc[2] + 0.34), radius=0.075,
                     color=(1.0, 0.72, 0.42), strength=16.0)
    orb.keyframe_insert('location', frame=1)
    orb.location = (loc[0], loc[1], loc[2] + 0.42)
    orb.keyframe_insert('location', frame=N)
    K.ease(orb)
    return root, orb


def _shred_cloud(center, seed=17):
    rnd = random.Random(seed)
    g = G.Geo('shreds')
    em = C.emissive('m_shred', (0.58, 0.52, 0.40), 0.16)
    for i in range(150):
        # thin strips, like shredded paper
        x = rnd.uniform(-0.9, 0.9)
        y = rnd.uniform(-0.9, 0.9)
        z = rnd.uniform(-1.0, 1.2)
        w = rnd.uniform(0.035, 0.085)
        h = rnd.uniform(0.18, 0.62)
        g.plane(1.0, (x, y, z),
                (rnd.uniform(-1.6, 1.6), rnd.uniform(-1.6, 1.6), rnd.uniform(0, 6.28)),
                em, sx=w, sy=h)
    ob = g.build()
    ob.location = center
    ob.visible_shadow = False
    ob.scale = (0.001, 0.001, 0.001)
    ob.keyframe_insert('scale', frame=1)
    ob.keyframe_insert('scale', frame=330)
    ob.scale = (1.0, 1.0, 1.0)
    ob.keyframe_insert('scale', frame=430)
    ob.keyframe_insert('location', frame=430)
    ob.location = (center[0], center[1], center[2] + 0.9)
    ob.keyframe_insert('location', frame=1100)
    ob.keyframe_insert('rotation_euler', frame=430)
    ob.rotation_euler = (0.0, 0.0, 0.0)
    ob.keyframe_insert('rotation_euler', frame=430)
    ob.rotation_euler = (0.2, 0.12, 5.0 * math.pi)
    ob.keyframe_insert('rotation_euler', frame=1400)
    ob.scale = (0.55, 0.55, 0.55)
    ob.keyframe_insert('scale', frame=1400)
    ob.scale = (0.28, 0.28, 0.28)
    ob.keyframe_insert('scale', frame=1520)
    ob.scale = (0.001, 0.001, 0.001)
    ob.keyframe_insert('scale', frame=1592)
    K.ease(ob)
    return ob


def _whale():
    front, mat, back = C.paper_cutout(WHALE, height=4.2,
                                      loc=(0.55, -13.9, FLOOR - 2.5),
                                      name='merged_whale', emission_strength=0.09)
    for ob in (front, back):
        ob.keyframe_insert('location', frame=1)
        ob.keyframe_insert('location', frame=1180)
        ob.location = (ob.location.x, ob.location.y, FLOOR + 0.05 + ob.location.z - (FLOOR - 2.5))
        ob.keyframe_insert('location', frame=1520)
    K.ease(front)
    K.ease(back)
    # tint the white whale texture to warm paper so it reads as cut paper, not a lightbox
    try:
        nt = mat.node_tree
        img_n = None
        for n in nt.nodes:
            if n.type == 'TEX_IMAGE':
                img_n = n
                break
        bsdf_in = None
        for l in nt.links:
            if l.from_node.type == 'TEX_IMAGE' and l.to_node.type in ('BSDF_PRINCIPLED', 'EMISSION'):
                bsdf_in = l.to_socket
        if img_n is not None and bsdf_in is not None:
            mixn = nt.nodes.new('ShaderNodeMixRGB')
            mixn.blend_type = 'MULTIPLY'
            mixn.inputs['Fac'].default_value = 1.0
            mixn.inputs['Color2'].default_value = (0.66, 0.575, 0.46, 1.0)
            nt.links.new(img_n.outputs['Color'], mixn.inputs['Color1'])
            nt.links.new(mixn.outputs['Color'], bsdf_in)
    except Exception as _e:
        print('whale tint failed: %r' % (_e,), flush=True)

    # cold backlight behind the whale
    L = C.light('whale_back', 'AREA', loc=(0.55, -16.6, FLOOR + 2.6), energy=900,
                color=(0.46, 0.72, 1.0), size=5.0)
    C.look_at(L, (0.55, -13.4, FLOOR + 2.2))
    L2 = C.light('whale_warm', 'AREA', loc=(-1.8, -9.6, FLOOR + 2.2), energy=220,
                 color=(1.0, 0.70, 0.44), size=3.0)
    C.look_at(L2, (0.4, -13.0, FLOOR + 2.0))
    return front, mat, back


def build():
    K.begin(fog_density=0.030, fog_color=(0.009, 0.034, 0.060),
            ambient=(0.005, 0.018, 0.030), exposure=0.15)
    T.theatre(seed=3)
    S.lighting('default')
    _dim_all(0.58)

    ctrl = K.char_actor('serious', (0.55, -11.2, FLOOR))
    K.char_expr(ctrl, [(1, 'serious', 3.0, 0.0), (220, 'shy', 2.0, 1.0),
                       (N, 'serious', 1.0, 0.0)])
    root = ctrl['root']
    root.keyframe_insert('scale', frame=1)
    root.keyframe_insert('scale', frame=360)
    root.scale = (0.001, 0.001, 0.001)
    root.keyframe_insert('scale', frame=470)
    K.ease(root)

    b_root, orb = _bucket((-2.05, -11.1, FLOOR))
    if b_root is not None:
        b_root.keyframe_insert('location', frame=1)
        b_root.location = (b_root.location.x, b_root.location.y, b_root.location.z)
        b_root.keyframe_insert('location', frame=N)

    _shred_cloud((0.55, -11.2, FLOOR + 1.15))
    _whale()
    S.foreground_papers(seed=31, n=14)

    K.cam_path('cam_s12', [
        (1, (-1.30, -7.25, FLOOR + 1.55), (0.05, -11.2, FLOOR + 1.25), 40, 2.8),
        (330, (-0.30, -7.50, FLOOR + 1.55), (0.30, -11.2, FLOOR + 1.30), 46, 2.8),
        (640, (0.35, -8.10, FLOOR + 1.72), (0.45, -11.4, FLOOR + 1.50), 50, 2.8),
        (1000, (0.50, -8.60, FLOOR + 2.32), (0.50, -12.6, FLOOR + 1.30), 40, 2.8),
        (1290, (0.52, -6.60, FLOOR + 2.30), (0.52, -13.0, FLOOR + 2.05), 34, 3.0),
        (N, (0.52, -6.30, FLOOR + 2.20), (0.52, -13.0, FLOOR + 2.30), 30, 3.0),
    ])
