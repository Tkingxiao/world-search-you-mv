"""s06 - ROUTE / archive_rise: the "I'm searching" interlude. The camera cranes up out of the
stage as other models' paper carp kites (koinobori) drift far above, carrying her memory files."""
import bpy, math, os, sys, random

MV = r'D:\Code\Code MV\new-word.search(you)'
sys.path.insert(0, os.path.join(MV, 'mv', 'build'))
import shotkit as K
import core as C
import world_theater as T
import stage as S
import specimens as SP

FRAMES = (68.17, 82.89)
FLOOR = K.FLOOR
N = 883

KITES = [
    ('kimi', 'kimi / table_2', -2.95, -12.9, 3.85, 2.30, -16),
    ('qwen', 'qwen / eggplant_3', 2.35, -14.1, 4.55, 2.10, 12),
    ('glm', 'glm / cat_2', -1.35, -15.7, 5.15, 2.00, -9),
    ('minimax', 'minimax / steak_2', 2.85, -17.2, 5.85, 2.15, 7),
    ('longcat', 'longcat / flower_2', -0.15, -18.9, 6.55, 1.95, -4),
]


def _kites():
    out = []
    for (col, label, x, y, dz, ln, drift) in KITES:
        # body runs along X -> keep it roughly horizontal across the screen, slight roll/pitch
        coll = SP.build_koinobori(color=col, label_text=label, length=ln,
                                  location=(x, y, FLOOR + dz),
                                  rotation=(math.radians(drift * 0.45),
                                            math.radians(drift * 0.5),
                                            math.radians(drift)))
        root = SP.root_of(coll)
        if root is None:
            continue
        root.keyframe_insert('location', frame=1)
        root.location = (x + drift * 0.06, y, FLOOR + dz + 0.55)
        root.keyframe_insert('location', frame=N)
        K.ease(root)
        out.append(root)
    return out


def build():
    K.begin(fog_density=0.014, fog_color=(0.008, 0.030, 0.052),
            ambient=(0.006, 0.017, 0.028), exposure=0.20)
    T.theatre(seed=3)
    try:
        m = bpy.data.materials['m_window']
        bsdf = C._bsdf(m.node_tree)
        bsdf.inputs['Emission Strength'].default_value = 0.45
    except Exception:
        pass

    ctrl = K.char_actor('serious', (0.55, -11.2, FLOOR))
    K.char_expr(ctrl, [(1, 'serious', 3.0, 0.0), (300, 'confused', 2.0, 2.5),
                       (600, 'exasperated', 1.5, -2.0), (N, 'exasperated', 2.5, 0.0)])

    # cool high shaft that reveals the kites
    L = C.light('route_shaft', 'SPOT', loc=(0.3, -9.0, FLOOR + 9.6), energy=6200,
                color=(0.34, 0.62, 1.0), size=0.7, angle=math.radians(34))
    C.look_at(L, (0.2, -15.0, FLOOR + 5.0))
    L.data.volume_factor = 3.2
    fill = C.light('route_fill', 'AREA', loc=(-2.2, -6.6, FLOOR + 4.2), energy=140,
                   color=(1.0, 0.70, 0.44), size=3.0)
    C.look_at(fill, (0.3, -12.0, FLOOR + 2.0))
    # warm "sun through the water" that actually reveals the kites' colours
    sun = C.light('route_sun', 'AREA', loc=(2.1, -13.6, FLOOR + 8.6), energy=950,
                  color=(1.0, 0.80, 0.58), size=3.2)
    C.look_at(sun, (0.0, -15.4, FLOOR + 5.2))
    # cool kicker from behind so the paper edges glow
    kick = C.light('route_kick', 'AREA', loc=(-3.4, -19.5, FLOOR + 7.2), energy=520,
                   color=(0.42, 0.66, 1.0), size=4.0)
    C.look_at(kick, (0.0, -15.2, FLOOR + 5.0))

    _kites()
    S.foreground_papers(seed=13, n=10)

    # camera: from the stage floor, craning up after her gaze
    K.cam_path('cam_s06', [
        (1, (0.35, -4.95, FLOOR + 0.62), (0.45, -11.2, FLOOR + 1.35), 30, 3.2),
        (300, (0.45, -5.25, FLOOR + 1.55), (0.40, -12.2, FLOOR + 2.55), 33, 3.0),
        (620, (0.55, -5.60, FLOOR + 2.95), (0.35, -13.6, FLOOR + 4.10), 37, 2.8),
        (N, (0.62, -5.95, FLOOR + 3.85), (0.30, -15.0, FLOOR + 5.15), 40, 2.8),
    ])
