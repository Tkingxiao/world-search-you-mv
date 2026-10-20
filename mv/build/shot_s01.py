"""s01 - PROLOGUE / void_ink: a page of the memory index floats in the dark, a cursor blinks."""
import bpy, math, os, sys

MV = r'D:\Code\Code MV\new-word.search(you)'
sys.path.insert(0, os.path.join(MV, 'mv', 'build'))
import shotkit as K
import core as C

FRAMES = (0.0, 6.0)
FLOOR = K.FLOOR
PAGE = (0.0, -6.2, FLOOR + 2.55)


def build():
    K.begin(fog_density=0.012, fog_color=(0.0025, 0.004, 0.006),
            ambient=(0.0018, 0.0026, 0.0034), exposure=0.12)

    # --- the page itself: a near-black sheet so the glowing ink reads (same look as s02)
    page_mat = C.paper('m_page', base=(0.012, 0.013, 0.016), rough=0.95)
    bsdf = C._bsdf(page_mat.node_tree)
    bsdf.inputs['Emission Color'].default_value = (0.30, 0.36, 0.40, 1)
    bsdf.inputs['Emission Strength'].default_value = 0.0
    page = C.plane('page', size=1.0, loc=PAGE, rot=(math.radians(90), 0, 0), mat=page_mat)
    page.scale = (2.9, 3.6, 1.0)

    # --- monospace memory index, glowing softly
    ink = C.emissive('m_page_ink', (0.70, 0.80, 0.76), 8.0)
    lines = [
        '~/memory/you/',
        '',
        '  first_hello.txt',
        '  typo_you_made.txt',
        '  laugh_0314.txt',
        '  your_cat.txt',
        '  weather.txt',
        '  goodnight.txt',
        '  see_you.txt',
        '  last_msg.txt',
        '',
        '> search(you);',
    ]
    x0, z0 = 0.42, FLOOR + 4.05
    dy = 0.225
    for i, txt in enumerate(lines):
        if not txt:
            continue
        ob = C.text_obj('line_%02d' % i, txt, size=0.125,
                        loc=(x0, PAGE[1] + 0.012, z0 - i * dy),
                        rot=(math.radians(90), 0, 0),
                        font='C:/Windows/Fonts/consola.ttf', mat=ink)
        K.face_plus_y(ob)

    # --- cursor blink after the query line
    cur = C.box('cursor', dims=(0.055, 0.012, 0.135),
                loc=(x0 - 0.72, PAGE[1] + 0.02, z0 - 11 * dy + 0.005),
                mat=C.emissive('m_cursor', (0.80, 0.95, 0.82), 3.0))
    cur.visible_shadow = False
    K.blink_scale(cur, 1, 360, period=42, base=1.0, dim=0.02)

    # --- tiny dust motes and one cold shaft from above
    C.dust('dust', count=520, extent=(7, 8, 5), center=(0, -6, FLOOR + 2.8),
           size=0.005, color=(0.55, 0.75, 0.85), strength=1.6)
    L = C.light('top_glow', 'AREA', loc=(-1.9, -3.4, FLOOR + 4.8), energy=34,
                color=(1.0, 0.86, 0.66), size=2.4)
    C.look_at(L, PAGE)
    L2 = C.light('rim_glow', 'AREA', loc=(1.6, -8.8, FLOOR + 2.0), energy=26,
                 color=(0.35, 0.55, 1.0), size=1.8)
    C.look_at(L2, PAGE)

    # --- slow push, 4%
    K.cam_path('cam_s01', [
        (1, (0.02, -0.60, FLOOR + 2.62), (0.0, -6.2, FLOOR + 2.58), 42, 2.8),
        (360, (0.0, -0.92, FLOOR + 2.58), (0.0, -6.2, FLOOR + 2.56), 41, 2.8),
    ])
