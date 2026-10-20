"""dbg_page.py - isolate the index page + text to debug dark-on-light text."""
import bpy, sys, math
sys.path.insert(0, r'D:\Code\Code MV\new-word.search(you)\mv\build')
for _m in ('core', 'world', 'geo', 'world_theater', 'shotkit'):
    sys.modules.pop(_m, None)
import core as C
import shotkit as K

FLOOR = -6.0
NAMES = ['first_hello.txt', 'typo_you_made.txt', 'laugh_0314.txt', 'your_cat.txt',
         'weather.txt', 'goodnight.txt', 'see_you.txt', 'last_msg.txt']


def main():
    K.begin(fog_density=0.0, exposure=0.3)
    m = C.paper('m_index_page', base=(0.045, 0.048, 0.052), rough=0.9)
    b = C._bsdf(m.node_tree)
    b.inputs['Emission Strength'].default_value = 0.02
    loc = (0.30, -11.4, FLOOR + 1.55)
    pg = C.plane('index_page', size=1.0, loc=loc, rot=(math.radians(90), 0, math.pi), mat=m)
    pg.scale = (2.35, 3.05, 1.0)
    ink = C.emissive('m_index_ink', (0.72, 0.88, 0.78), 5.0)
    lines = ['~/memory/you/'] + NAMES
    z0 = loc[2] + 1.22
    for i, txt in enumerate(lines):
        ob = C.text_obj('idx_%02d' % i, txt, size=0.125,
                        loc=(loc[0] + 0.96, loc[1] + 0.05, z0 - i * 0.275),
                        font='C:/Windows/Fonts/consola.ttf', mat=ink)
        K.face_plus_y(ob)
    L = C.light('key', 'AREA', loc=(1.0, -8.0, FLOOR + 3.0), energy=120, size=3.0,
                color=(1.0, 0.95, 0.85))
    C.look_at(L, (0.3, -11.4, FLOOR + 1.6))
    K.cam_path('cam_dbg', [(1, (0.70, -6.4, FLOOR + 1.65), (0.30, -11.4, FLOOR + 1.55), 35, 4.0)])
    sc = bpy.context.scene
    sc.render.filepath = r'D:\Code\Code MV\new-word.search(you)\mv\out\lookdev\dbg_page.png'
    sc.render.resolution_x = 960
    sc.render.resolution_y = 540
    bpy.ops.render.render(write_still=True)
    print('DBG_PAGE_DONE')


main()
