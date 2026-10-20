# -*- coding: utf-8 -*-
p = r'D:\Code\Code MV\new-word.search(you)\mv\build\world_theater.py'
s = open(p, encoding='utf-8').read()

s = s.replace("""        plank=C.paper('m_plank', base=(0.33, 0.28, 0.22), rough=0.82),
        plank_dark=C.paper('m_plank_dark', base=(0.055, 0.048, 0.040), rough=0.9),
        ink=C.paper('m_theater_ink', base=(0.020, 0.020, 0.024), rough=0.92),
        ink2=C.paper('m_theater_ink2', base=(0.045, 0.042, 0.040), rough=0.9),
        paper=C.paper('m_theater_paper', base=(0.72, 0.68, 0.58), rough=0.8),
        paper_warm=C.paper('m_theater_paper_warm', base=(0.78, 0.66, 0.48), rough=0.8),
        gold=C.paper('m_theater_gold', base=(0.78, 0.58, 0.22), rough=0.45),""",
"""        plank=C.paper('m_plank', base=(0.175, 0.150, 0.120), rough=0.85),
        plank_dark=C.paper('m_plank_dark', base=(0.040, 0.036, 0.030), rough=0.9),
        ink=C.paper('m_theater_ink', base=(0.016, 0.016, 0.019), rough=0.92),
        ink2=C.paper('m_theater_ink2', base=(0.038, 0.036, 0.034), rough=0.9),
        ink3=C.paper('m_theater_ink3', base=(0.070, 0.066, 0.060), rough=0.88),
        paper=C.paper('m_theater_paper', base=(0.62, 0.57, 0.47), rough=0.8),
        paper_warm=C.paper('m_theater_paper_warm', base=(0.72, 0.60, 0.42), rough=0.8),
        gold=C.paper('m_theater_gold', base=(0.82, 0.60, 0.20), rough=0.32),""")

s = s.replace("""    # outer frame
    g2.box((w + 0.16, 0.06, 0.10), (loc[0], fy, loc[2] + h / 2), (0, 0, 0), M['ink'])
    g2.box((w + 0.16, 0.06, 0.10), (loc[0], fy, loc[2] - h / 2), (0, 0, 0), M['ink'])
    g2.box((0.10, 0.06, h + 0.16), (loc[0] - w / 2, fy, loc[2]), (0, 0, 0), M['ink'])
    g2.box((0.10, 0.06, h + 0.16), (loc[0] + w / 2, fy, loc[2]), (0, 0, 0), M['ink'])""",
"""    # outer frame (gold) + dark reveal so the opening reads as a cut in the wall
    g2.box((w + 0.22, 0.05, 0.07), (loc[0], fy + 0.02, loc[2] + h / 2), (0, 0, 0), M['gold'])
    g2.box((w + 0.22, 0.05, 0.07), (loc[0], fy + 0.02, loc[2] - h / 2), (0, 0, 0), M['gold'])
    g2.box((0.07, 0.05, h + 0.22), (loc[0] - w / 2, fy + 0.02, loc[2]), (0, 0, 0), M['gold'])
    g2.box((0.07, 0.05, h + 0.22), (loc[0] + w / 2, fy + 0.02, loc[2]), (0, 0, 0), M['gold'])
    g2.box((w + 0.10, 0.08, 0.16), (loc[0], fy, loc[2] + h / 2 + 0.11), (0, 0, 0), M['ink'])
    g2.box((w + 0.10, 0.08, 0.16), (loc[0], fy, loc[2] - h / 2 - 0.11), (0, 0, 0), M['ink'])""")

s = s.replace("""    g.box((left_w, 0.12, h), (-w / 2 + left_w / 2, y, z + h / 2), (0, 0, 0), M['ink2'])
    g.box((right_w, 0.12, h), (cx + hw + right_w / 2, y, z + h / 2), (0, 0, 0), M['ink2'])
    g.box((2 * hw, 0.12, (z + h) - (cz + hh)), (cx, y, ((cz + hh) + (z + h)) / 2), (0, 0, 0), M['ink2'])
    g.box((2 * hw, 0.12, (cz - hh) - z), (cx, y, ((cz - hh) + z) / 2), (0, 0, 0), M['ink2'])""",
"""    g.box((left_w, 0.12, h), (-w / 2 + left_w / 2, y, z + h / 2), (0, 0, 0), M['ink3'])
    g.box((right_w, 0.12, h), (cx + hw + right_w / 2, y, z + h / 2), (0, 0, 0), M['ink3'])
    g.box((2 * hw, 0.12, (z + h) - (cz + hh)), (cx, y, ((cz + hh) + (z + h)) / 2), (0, 0, 0), M['ink3'])
    g.box((2 * hw, 0.12, (cz - hh) - z), (cx, y, ((cz - hh) + z) / 2), (0, 0, 0), M['ink3'])
    # vertical paper panel seams for scale
    for i in range(-6, 7):
        sx = i * 2.0
        if abs(sx - cx) < hw + 0.2:
            continue
        g.box((0.035, 0.02, h), (sx, y + 0.07, z + h / 2), (0, 0, 0), M['ink2'])""")

# smaller / higher window
s = s.replace("objs['backdrop'] = backdrop_wall(hole=(0.0, FLOOR + 2.85, 1.95, 1.55))",
              "objs['backdrop'] = backdrop_wall(hole=(0.0, FLOOR + 3.05, 1.70, 1.40))")

# plinth arc: 4 aligned plinths + 1 hero plinth nearer the character
s = s.replace("""    objs['plinths'] = []
    for i, (px, py) in enumerate([(-3.1, -14.6), (-1.85, -15.3), (-0.6, -15.7),
                                  (0.65, -15.7), (1.9, -15.3), (3.15, -14.6)]):
        objs['plinths'].append(plinth(px, py, h=0.62 + 0.05 * (i % 2)))""",
"""    objs['plinths'] = []
    for i, (px, py) in enumerate([(-3.0, -15.4), (-1.0, -15.9), (1.0, -15.9), (3.0, -15.4)]):
        objs['plinths'].append(plinth(px, py, h=0.60))
    objs['hero_plinth'] = plinth(-2.15, -13.2, h=0.52, w=0.62, d=0.62)""")

# terminal desk: move to stage-left, facing audience
s = s.replace("objs['desk'], objs['screen'], objs['lamp'] = terminal_desk()",
              "objs['desk'], objs['screen'], objs['lamp'] = terminal_desk(loc=(-2.45, -10.4, FLOOR))")

open(p, 'w', encoding='utf-8').write(s)
print('patched')
