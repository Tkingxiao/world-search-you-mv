import io

p = r'D:\Code\Code MV\new-word.search(you)\mv\build\shot_s10.py'
s = io.open(p, encoding='utf-8').read()

reps = [
    ("    pg = C.plane('type_page', size=1.0, loc=(0.0, PAGE_Y, FLOOR + 1.02),\n"
     "                 rot=(math.radians(90), 0, math.pi), mat=m)\n"
     "    pg.scale = (1.24, 1.62, 1.0)",
     "    pg = C.plane('type_page', size=1.0, loc=(0.0, PAGE_Y, FLOOR + 1.34),\n"
     "                 rot=(math.radians(90), 0, math.pi), mat=m)\n"
     "    pg.scale = (2.02, 2.62, 1.0)"),
    ("    z0 = FLOOR + 1.66", "    z0 = FLOOR + 2.30"),
    ("        t = C.text_obj('type_line_%02d' % i, ln, size=0.050,\n"
     "                       loc=(0.0, PAGE_Y + 0.012, z0 - i * 0.097), mat=ink,",
     "        t = C.text_obj('type_line_%02d' % i, ln, size=0.074,\n"
     "                       loc=(0.0, PAGE_Y + 0.012, z0 - i * 0.158), mat=ink,"),
    ("        a = (sx, PAGE_Y, FLOOR + 1.84)\n"
     "        b = (sx, PAGE_Y, FLOOR + 5.2)",
     "        a = (sx, PAGE_Y, FLOOR + 2.66)\n"
     "        b = (sx, PAGE_Y, FLOOR + 5.6)"),
    ("    for sx in (-0.58, 0.58):", "    for sx in (-0.92, 0.92):"),
]

for old, new in reps:
    assert old in s, 'missing: %r' % old[:60]
    s = s.replace(old, new)

io.open(p, 'w', encoding='utf-8').write(s)
print('s10 page enlarged')
