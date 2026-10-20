# -*- coding: utf-8 -*-
p = r'D:\Code\Code MV\new-word.search(you)\mv\build\stage.py'
s = open(p, encoding='utf-8').read()

s = s.replace('''def foreground_papers(seed=7, n=9):
    """Out-of-focus paper sheets floating between the audience and the stage -> depth."""
    M = T._mats()
    rnd = random.Random(seed)
    g = G.Geo('fg_papers')
    for i in range(n):
        x = rnd.uniform(-3.4, 3.4)
        y = rnd.uniform(-5.6, -4.0)
        z = FLOOR + rnd.uniform(0.35, 2.4)
        w = rnd.uniform(0.18, 0.42)
        h = w * rnd.uniform(0.7, 1.4)
        g.plane(1.0, (x, y, z), (rnd.uniform(-0.6, 0.6), rnd.uniform(-0.9, 0.9), rnd.uniform(0, 6.28)),
                M['paper_warm'] if i % 3 else M['paper'], sx=w, sy=h)
    ob = g.build()
    return ob''',
'''def foreground_papers(seed=7, n=14):
    """Out-of-focus paper scraps floating between the audience and the stage -> depth."""
    M = T._mats()
    rnd = random.Random(seed)
    em = C.emissive('m_fg_scrap', (0.42, 0.36, 0.27), 0.9)
    em2 = C.emissive('m_fg_scrap2', (0.20, 0.30, 0.40), 0.7)
    g = G.Geo('fg_papers')
    for i in range(n):
        x = rnd.uniform(-3.8, 3.8)
        y = rnd.uniform(-6.6, -5.0)
        z = FLOOR + rnd.uniform(0.45, 2.9)
        w = rnd.uniform(0.09, 0.22)
        h = w * rnd.uniform(0.7, 1.5)
        g.plane(1.0, (x, y, z), (rnd.uniform(-0.7, 0.7), rnd.uniform(-1.0, 1.0), rnd.uniform(0, 6.28)),
                em if i % 3 else em2, sx=w, sy=h)
    ob = g.build()
    ob.visible_shadow = False
    return ob''')

s = s.replace("""        L = C.light('desk_pool', 'POINT', loc=(-2.35, -10.1, FLOOR + 1.15), energy=55,
                    color=(0.35, 1.0, 0.72), size=0.28)
        L.data.volume_factor = 0.8""",
"""        L = C.light('desk_pool', 'POINT', loc=(-2.35, -10.1, FLOOR + 1.15), energy=55,
                    color=(0.35, 1.0, 0.72), size=0.28)
        L.data.volume_factor = 0.8
        # soft wash on the back wall so the paper panels read
        L = C.light('wall_wash', 'AREA', loc=(0.0, -15.2, FLOOR + 4.6), energy=110,
                    color=(0.42, 0.58, 0.95), size=6.0)
        C.look_at(L, (0.0, -21.0, FLOOR + 3.4))""")

open(p, 'w', encoding='utf-8').write(s)
print('patched stage.py')
