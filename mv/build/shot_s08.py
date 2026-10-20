"""s08 - FORGET: the hall, FLOWER then HUMAN.

The flower is the only warm colour in the hall.  Then she walks to the human
hologram, reaches out - and her paper hand passes through the scan: the ring
slides across her card and the hologram stutters.  She is only a plane; she
cannot touch anything real.
"""
import bpy, math, os, sys

MV = r'D:\Code\Code MV\new-word.search(you)'
sys.path.insert(0, os.path.join(MV, 'mv', 'build'))
import shotkit as K
import core as C
import stage as S
import specimens as SP
import shot_s05 as H

FRAMES = (109.72, 137.09)
FLOOR = K.FLOOR
N = int(round(FRAMES[1] * K.FPS)) - int(round(FRAMES[0] * K.FPS))

# She starts at the right edge (off-frame while the flower beats are clean), then
# walks INTO the human scan: the human hologram is the only pedestal-less
# specimen (life-size, floating), so her flat paper body can intersect it -
# "she is only a plane".
CHAR = (2.15, -11.10, FLOOR)
FLOWER = (-3.00, -13.50)
HUMAN = (0.45, -13.00)
REACH = (1.15, -13.00, FLOOR)


def build():
    K.begin(fog_density=0.022, fog_color=(0.009, 0.032, 0.052),
            ambient=(0.005, 0.015, 0.026), exposure=0.24)
    H._build_hall(seed=5)
    H._hall_lights()

    fcoll = H._place(SP.build_flower, FLOWER, rotz=6.0,
                     style=dict(point_count=460, wire_ratio=0.46,
                                wire_thickness=0.0026, shell_alpha=0.06))
    # no plinth, life size, floating 12cm: the one specimen that is a person.
    # label on the far side so it does not hide behind her paper body.
    hcoll = H._place(SP.build_human, HUMAN, rotz=-4.0, scale=1.6, shadow=False,
                     style=dict(plinth=False, label_side='left', point_count=470,
                                wire_ratio=0.45, wire_thickness=0.0032,
                                shell_alpha=0.07))
    hroot = SP.root_of(hcoll)
    if hroot is not None:
        hroot.location.z = FLOOR + 0.12
    pad = C.emissive('human_scan_pad', (0.20, 0.62, 1.0), 0.85)
    C.plane('human_scan_pad', 1.55, (HUMAN[0], HUMAN[1], FLOOR + 0.012),
            (0.0, 0.0, 0.0), pad)
    ring_c = "#598fb0"
    SP.animate_scan(fcoll, period=3.2, frame_start=1, frame_end=N, color=ring_c)
    # ring is timed so it sweeps across her card exactly when she reaches (f1300)
    SP.animate_scan(hcoll, period=8.34, frame_start=900, frame_end=N, color=ring_c)
    H._label_light(fcoll, 0, 6.0)
    H._label_light(hcoll, 1, 8.0)

    f_shaft = H._shaft('flower_shaft', FLOWER, energy=2600.0, angle=20.0)
    h_shaft = H._shaft('human_shaft', HUMAN, energy=400.0)
    H._energy(f_shaft, [(1, 2600), (700, 3200), (900, 1000), (N, 700)])
    H._energy(h_shaft, [(1, 400), (900, 900), (1150, 2800), (1480, 3600), (N, 1000)])

    # hologram stutters where her hand passes through (multiplicative: keep the
    # builder's real scale, do NOT overwrite it with 1.0)
    if hroot is not None:
        s0 = float(hroot.scale[0])
        for f, s in [(1, 1.0), (1300, 1.0), (1320, 1.014), (1340, 0.992),
                     (1362, 1.010), (1390, 1.0), (N, 1.0)]:
            hroot.scale = (s0 * s, s0 * s, s0 * s)
            hroot.keyframe_insert('scale', frame=f)
        K.ease(hroot)

    ctrl = K.char_actor('shy', CHAR)
    # NOTE: 'maid' (the 9th atlas pose) samples the neighbouring cell's bottom
    # strip above the head - shared-asset bug, reported to the Lead.  Use
    # 'exasperated' (both hands out) for the reaching beat instead.
    K.char_expr(ctrl, [
        (1, 'shy', 3.0, -1.0),
        (420, 'cheerful', 3.0, 0.5),
        (780, 'shy', 3.5, -0.5),
        (1080, 'exasperated', 2.5, 0.0),   # reaching for the hologram
        (1300, 'exasperated', 2.0, 0.0),
        (1400, 'frightened', 2.0, -0.5),   # her hand passes through
        (N, 'shy', 3.5, -0.5),
    ])
    K.char_pose(ctrl, [
        (1, CHAR, None, None),
        (420, (0.30, -11.75, FLOOR), None, None),
        (700, (0.15, -12.00, FLOOR), None, None),
        (1050, (0.55, -12.40, FLOOR), None, None),
        (1300, REACH, None, None),
        (N, REACH, None, None),
    ])

    # flower medium -> her -> walk to the human -> hand at the scan -> her face
    cam = K.cam_path('cam_s08', [
        (1, (1.55, -7.55, FLOOR + 1.88), (-2.65, -13.40, FLOOR + 1.10), 35, 3.2),
        (220, (1.35, -7.70, FLOOR + 1.84), (-2.30, -13.30, FLOOR + 1.12), 36, 3.1),
        (430, (0.85, -7.95, FLOOR + 1.78), (-1.35, -13.10, FLOOR + 1.18), 40, 2.8),
        (620, (0.55, -8.02, FLOOR + 1.75), (-0.55, -12.60, FLOOR + 1.24), 45, 2.5),
        (780, (0.30, -8.05, FLOOR + 1.72), (0.30, -11.80, FLOOR + 1.32), 50, 2.2),
        (1120, (0.55, -8.25, FLOOR + 1.72), (0.60, -12.90, FLOOR + 1.22), 45, 2.4),
        (1400, (1.05, -8.20, FLOOR + 1.68), (0.78, -13.00, FLOOR + 1.02), 50, 2.2),
        (N, (1.18, -8.45, FLOOR + 1.64), (0.72, -13.00, FLOOR + 0.98), 55, 2.2),
    ])
    K.add_handheld(cam, amp=0.012, scale=1.3, seed=11)
    return {'flower': fcoll, 'human': hcoll}
