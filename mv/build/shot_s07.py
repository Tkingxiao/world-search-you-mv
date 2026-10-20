"""s07 - ROUTE: the hall, two more specimens (CAT -> STEAK).

50mm medium-close alternation: cat hologram (wireframe, "purr: 0"), her face,
then the steak under a warm-gold shaft, then her face again.
"""
import bpy, math, os, sys

MV = r'D:\Code\Code MV\new-word.search(you)'
sys.path.insert(0, os.path.join(MV, 'mv', 'build'))
import shotkit as K
import core as C
import stage as S
import specimens as SP
import shot_s05 as H

FRAMES = (82.89, 109.72)
FLOOR = K.FLOOR
N = int(round(FRAMES[1] * K.FPS)) - int(round(FRAMES[0] * K.FPS))

# she starts off-frame on the steak side so the opening cat shot is clean
CHAR = (1.95, -11.50, FLOOR)
CAT = (-3.05, -13.75)
STEAK = (2.65, -13.95)


def build():
    K.begin(fog_density=0.022, fog_color=(0.009, 0.032, 0.052),
            ambient=(0.005, 0.015, 0.026), exposure=0.24)
    H._build_hall(seed=5)
    H._hall_lights()

    ccoll = H._place(SP.build_cat, CAT, rotz=8.0, style=dict(label_lines=[
        "CAT", "sim 0.22   mass 0.00 kg", "purr: 0"], point_count=460,
        wire_ratio=0.46, wire_thickness=0.0028, shell_alpha=0.06))
    scoll = H._place(SP.build_steak, STEAK, rotz=-12.0,
                     style=dict(label_side='left', point_count=420,
                                wire_ratio=0.44, wire_thickness=0.0026,
                                shell_alpha=0.06))
    ring_c = "#598fb0"
    SP.animate_scan(ccoll, period=3.0, frame_start=1, frame_end=N, color=ring_c)
    SP.animate_scan(scoll, period=2.6, frame_start=820, frame_end=N, color=ring_c)
    H._label_light(ccoll, 0, 6.0)
    H._label_light(scoll, 1, 6.0)

    c_shaft = H._shaft('cat_shaft', CAT, energy=2800.0)
    s_shaft = H._shaft('steak_shaft', STEAK, energy=500.0)
    H._energy(c_shaft, [(1, 2800), (620, 3400), (820, 950), (N, 650)])
    H._energy(s_shaft, [(1, 500), (780, 900), (960, 3200), (1400, 3600), (N, 900)])

    ctrl = K.char_actor('starry', CHAR)
    K.char_expr(ctrl, [
        (1, 'starry', 2.5, 0.5),
        (340, 'frightened', 3.5, -1.0),
        (620, 'confused', 2.5, 1.5),
        (880, 'starry', 3.0, -0.5),      # "hungry" beat (no hungry expression)
        (1180, 'serious', 2.5, 0.0),
        (1420, 'cheerful', 3.0, 1.0),
        (N, 'cheerful', 2.5, 0.5),
    ])
    K.char_pose(ctrl, [
        (1, CHAR, None, None),
        (400, (0.35, -11.35, FLOOR), None, None),
        (820, (0.60, -11.25, FLOOR), None, None),
        (1200, (0.45, -11.15, FLOOR), None, None),
        (N, (0.45, -11.15, FLOOR), None, None),
    ])

    # 50mm medium close, arc + push: cat -> her -> steak -> her
    cam = K.cam_path('cam_s07', [
        (1, (-1.05, -6.95, FLOOR + 1.82), (-2.62, -13.58, FLOOR + 1.16), 50, 2.6),
        (170, (-1.30, -7.15, FLOOR + 1.80), (-2.72, -13.62, FLOOR + 1.14), 51, 2.6),
        (400, (0.90, -7.60, FLOOR + 1.74), (0.55, -11.20, FLOOR + 1.36), 50, 2.2),
        (620, (0.25, -7.45, FLOOR + 1.76), (0.70, -11.25, FLOOR + 1.33), 50, 2.2),
        (820, (-0.55, -7.35, FLOOR + 1.76), (2.35, -13.70, FLOOR + 1.05), 48, 2.6),
        (1000, (-0.85, -7.50, FLOOR + 1.74), (2.60, -13.85, FLOOR + 1.02), 49, 2.5),
        (1200, (0.70, -7.70, FLOOR + 1.70), (0.55, -11.20, FLOOR + 1.33), 55, 2.1),
        (N, (0.80, -7.85, FLOOR + 1.68), (0.50, -11.20, FLOOR + 1.30), 58, 2.1),
    ])
    K.add_handheld(cam, amp=0.013, scale=1.2, seed=7)
    return {'cat': ccoll, 'steak': scoll}
