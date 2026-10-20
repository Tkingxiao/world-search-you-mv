"""s04 - SORT / theater: close on a glass memory jar; the memory lifts out, drifts to her face,
then rises away into the dark. Camera: macro -> follow the orb -> settle on her watching it go."""
import bpy, math, os, sys, random
from mathutils import Vector

MV = r'D:\Code\Code MV\new-word.search(you)'
sys.path.insert(0, os.path.join(MV, 'mv', 'build'))
import shotkit as K
import core as C
import world_theater as T
import stage as S
import geo as G

FRAMES = (28.32, 40.86)
FLOOR = K.FLOOR
N = 753

JAR = (-0.95, -9.55)
JAR_Z = FLOOR + 0.86
CHAR = (0.62, -11.00)


def _jar(loc):
    """Small glass bell jar on a paper pedestal, with a glowing memory inside."""
    g = G.Geo('jar_glass')
    glass = C.glass('m_jar_glass', base=(0.66, 0.80, 0.92), rough=0.08)
    try:
        glass.node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value = 0.13
    except Exception:
        bsdf = C._bsdf(glass.node_tree)
        bsdf.inputs['Alpha'].default_value = 0.13
    g.cylinder(r=0.185, h=0.46, loc=(loc[0], loc[1], loc[2] + 0.23), mat=glass, seg=24)
    jar = g.build()
    jar.visible_shadow = False
    paper = C.paper('m_jar_base', base=(0.60, 0.52, 0.38), rough=0.85)
    gb = G.Geo('jar_base')
    gb.cylinder(r=0.215, h=0.045, loc=(loc[0], loc[1], loc[2] + 0.022), mat=paper, seg=24)
    gb.cylinder(r=0.205, h=0.05, loc=(loc[0], loc[1], loc[2] + 0.47), mat=paper, seg=24)
    gb.build()
    orb = K.glow_orb('memory_orb', (loc[0], loc[1], loc[2] + 0.13), radius=0.035,
                     color=(1.0, 0.82, 0.52), strength=4.5)
    return jar, orb


def build():
    K.begin(fog_density=0.013, fog_color=(0.008, 0.030, 0.052),
            ambient=(0.005, 0.014, 0.024), exposure=0.18)
    T.theatre(seed=3)
    try:
        m = bpy.data.materials['m_window']
        C._bsdf(m.node_tree).inputs['Emission Strength'].default_value = 0.70
    except Exception:
        pass
    S.lighting('default')
    S.foreground_papers(seed=7, n=12)

    ctrl = K.char_actor('shy', (CHAR[0], CHAR[1], FLOOR))
    K.char_expr(ctrl, [(1, 'shy', 2.0, 0.0), (300, 'serious', 3.5, 1.5),
                       (560, 'cheerful', 2.0, -1.0), (N, 'serious', 2.5, 0.0)])
    K.char_pose(ctrl, [(1, None, (2.0, 0.0), 1.0),
                       (300, (CHAR[0], CHAR[1], FLOOR + 0.05), (3.5, 1.5), 1.0),
                       (N, (CHAR[0], CHAR[1], FLOOR), (2.5, 0.0), 1.0)])

    # tall museum pedestal + jar
    T.plinth(JAR[0], JAR[1], h=0.86, w=0.56, d=0.56, gold=False, label=False)
    jar, orb = _jar((JAR[0], JAR[1], JAR_Z))
    # warm practical so the glass catches a highlight
    pl = C.light('jar_pool', 'POINT', loc=(JAR[0] - 0.55, JAR[1] + 0.45, FLOOR + 1.45),
                 energy=22, color=(1.0, 0.72, 0.46), size=0.06)
    C.light('jar_back', 'POINT', loc=(JAR[0] + 0.30, JAR[1] - 0.55, FLOOR + 1.35),
            energy=12, color=(0.55, 0.75, 1.0), size=0.05)

    # the memory rises out of the jar, drifts to her, then up into the dark
    orb.keyframe_insert('location', frame=1)
    orb.location = (JAR[0], JAR[1], JAR_Z + 0.55)
    orb.keyframe_insert('location', frame=180)
    orb.location = (JAR[0] + 0.22, JAR[1] - 0.65, FLOOR + 1.50)
    orb.keyframe_insert('location', frame=300)
    orb.location = (0.14, -10.75, FLOOR + 1.60)
    orb.keyframe_insert('location', frame=430)
    orb.location = (CHAR[0] - 0.10, CHAR[1] + 0.02, FLOOR + 1.86)
    orb.keyframe_insert('location', frame=560)
    orb.location = (1.10, -11.55, FLOOR + 3.45)
    orb.keyframe_insert('location', frame=N)
    K.ease(orb)

    # camera: macro on the jar -> follow the orb up -> settle on her watching it go
    K.cam_path('cam_s04', [
        (1, (-1.00, -8.20, FLOOR + 1.15), (JAR[0], JAR[1], FLOOR + 1.08), 55, 2.0),
        (150, (-0.95, -8.30, FLOOR + 1.28), (JAR[0], JAR[1], FLOOR + 1.12), 50, 2.2),
        (300, (-0.70, -8.45, FLOOR + 1.42), (-0.62, -10.10, FLOOR + 1.50), 45, 2.2),
        (430, (-0.05, -8.10, FLOOR + 1.50), (0.22, -10.70, FLOOR + 1.55), 40, 2.4),
        (580, (0.55, -7.35, FLOOR + 1.55), (CHAR[0], CHAR[1], FLOOR + 1.30), 38, 2.5),
        (N, (1.15, -7.60, FLOOR + 1.62), (CHAR[0], CHAR[1], FLOOR + 1.32), 35, 2.6),
    ])
