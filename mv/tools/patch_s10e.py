import io

p = r'D:\Code\Code MV\new-word.search(you)\mv\build\shot_s10.py'
s = io.open(p, encoding='utf-8').read()

reps = [
    # page shifted to screen right (world -X) so she is not hidden by it
    ("    pg = C.plane('type_page', size=1.0, loc=(0.0, PAGE_Y, FLOOR + 1.34),\n"
     "                 rot=(math.radians(90), 0, math.pi), mat=m)\n"
     "    pg.scale = (2.02, 2.62, 1.0)",
     "    pg = C.plane('type_page', size=1.0, loc=(PAGE_X, PAGE_Y, FLOOR + 1.34),\n"
     "                 rot=(math.radians(90), 0, math.pi), mat=m)\n"
     "    pg.scale = (2.02, 2.62, 1.0)"),
    ("PAGE_Y = -13.60", "PAGE_Y = -13.60\nPAGE_X = -1.05"),
    # typed lines follow the page
    ("        t = C.text_obj('type_line_%02d' % i, ln, size=0.074,\n"
     "                       loc=(0.0, PAGE_Y + 0.012, z0 - i * 0.158), mat=ink,",
     "        t = C.text_obj('type_line_%02d' % i, ln, size=0.074,\n"
     "                       loc=(PAGE_X, PAGE_Y + 0.012, z0 - i * 0.158), mat=ink,"),
    # threads follow the page
    ("    for sx in (-0.92, 0.92):", "    for sx in (PAGE_X - 0.92, PAGE_X + 0.92):"),
    # a dedicated soft light for the hanging page (no shadow: cheap)
    ("    spot.data.volume_factor = 0.9",
     "    spot.data.volume_factor = 0.9\n"
     "    pl = C.light('type_pagelight', 'AREA', loc=(PAGE_X, PAGE_Y + 2.6, FLOOR + 2.6),\n"
     "                 energy=260, color=(1.0, 0.86, 0.66), size=3.4)\n"
     "    C.look_at(pl, (PAGE_X, PAGE_Y, FLOOR + 1.30))\n"
     "    try:\n"
     "        pl.data.use_shadow = False\n"
     "    except Exception:\n"
     "        pass"),
]

for old, new in reps:
    assert old in s, 'missing %r' % old[:70]
    s = s.replace(old, new)

io.open(p, 'w', encoding='utf-8').write(s)
print('s10 page offset + page light')
