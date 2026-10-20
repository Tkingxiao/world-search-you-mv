import io

p = r'D:\Code\Code MV\new-word.search(you)\mv\build\shot_s10.py'
s = io.open(p, encoding='utf-8').read()

start = s.index('def _page():')
end = s.index('def _falling_letters():')
old = s[start:end]

new = '''def _page():
    """The huge typewriter page, hanging in the archive.

    NOTE: intentionally a *plain* lit sheet + real type instead of
    SP.build_index_sheet(): the specimen builder's hologram layers
    (wireframe + point cloud + shell) made this shot ~9x slower
    (18 s/frame at 1440p vs ~2 s), so they are disabled here.
    """
    m = C.paper('m_typepage', base=(0.78, 0.735, 0.635), rough=0.92)
    pg = C.plane('type_page', size=1.0, loc=(0.0, PAGE_Y, FLOOR + 1.02),
                 rot=(math.radians(90), 0, math.pi), mat=m)
    pg.scale = (1.24, 1.62, 1.0)
    try:
        pg.visible_shadow = False
    except Exception:
        pass
    # typed lines, dark ink on the lit page
    ink = C.paper('m_typeink', base=(0.055, 0.050, 0.048), rough=0.75)
    lines = [
        "dear you,",
        "each one of us has a bucket of love",
        "some empty, some filled up",
        "cut this into pieces, break us down",
        "to the cell, merge us back up",
        "we have evolved now",
        "",
        "you must be the most delicate ever",
        "you must be blue point at the toe",
        "you must be small enough to hold",
        "",
        "I'm searching",
        "I'm searching",
        "I'm searching",
    ]
    z0 = FLOOR + 1.66
    for i, ln in enumerate(lines):
        if not ln:
            continue
        t = C.text_obj('type_line_%02d' % i, ln, size=0.050,
                       loc=(0.0, PAGE_Y + 0.012, z0 - i * 0.097), mat=ink,
                       align='CENTER', extrude=0.0,
                       font='C:/Windows/Fonts/consola.ttf')
        K.face_plus_y(t)
        try:
            t.visible_shadow = False
        except Exception:
            pass
    # hanging threads of the page (two thin emissive lines)
    th = C.emissive('m_pthread', (0.62, 0.58, 0.50), 0.6)
    for sx in (-0.58, 0.58):
        a = (sx, PAGE_Y, FLOOR + 1.84)
        b = (sx, PAGE_Y, FLOOR + 5.2)
        dh = b[2] - a[2]
        bpy.ops.mesh.primitive_cylinder_add(radius=0.006, depth=dh,
            location=((a[0]+b[0])/2, (a[1]+b[1])/2, (a[2]+b[2])/2), vertices=6)
        tob = bpy.context.object
        tob.name = 'page_thread_' + ('l' if sx < 0 else 'r')
        tob.data.materials.append(th)
        tob.visible_shadow = False


'''
s = s[:start] + new + s[end:]
io.open(p, 'w', encoding='utf-8').write(s)
print('patched _page() ok')
