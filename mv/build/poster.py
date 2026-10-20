"""mv/build/poster.py - key visual poster for Mili <world.search(you);>  (v2).

Two layouts from one script:
    landscape 2560x1440  (title band in the top 15 %, credits corner bottom-right)
    portrait  1800x2700  (weight in the upper half: floor space at the bottom)

    paper theatre (world_theater.theatre) + cool bright shoji backlight
    + her illustration as a half-body paper cut-out (char atlas art)
    + warm rim light behind her (silhouette edge)
    + glowing paper-whale silhouettes
    + floating index cards with model memory filenames (Consolas, glowing)
    + falling paper scraps (bokeh) + marionette threads

Usage (headless):
    # quick landscape preview 960x540
    blender_rt_headless --script_file "...\\mv\\build\\poster.py"
    # final landscape 2560x1440
    blender_rt_headless --script_file "...\\mv\\build\\poster.py" \
        --args "--w 2560 --h 1440 --samples 32 --out poster_2560x1440.png"
    # portrait (defaults to 1800x2700 when --w/--h omitted)
    blender_rt_headless --script_file "...\\mv\\build\\poster.py" \
        --args "--portrait --samples 32 --out poster_1800x2700.png"
    # portrait preview
    ... --args "--portrait --w 600 --h 900 --out poster_v2_portrait_600x900.png"
"""
import bpy
import math
import os
import sys
import random
import time

MV = r'D:\Code\Code MV\new-word.search(you)'
sys.path.insert(0, os.path.join(MV, 'mv', 'build'))

import core as C            # noqa: E402
import geo as G             # noqa: E402
import world_theater as T   # noqa: E402
import shotkit as K         # noqa: E402

OUT_DIR = os.path.join(MV, 'mv', 'out', 'lookdev')
FLOOR = K.FLOOR
SILHOUETTE = os.path.join(MV, 'mv', 'assets', 'whale_silhouette.png')
CONSOLAS = r'C:\Windows\Fonts\consola.ttf'

FOG_DENSITY = 0.021
FOG_COLOR = (0.010, 0.045, 0.075)
AMBIENT = (0.008, 0.028, 0.042)

# --------------------------------------------------------------------------- layouts
# world +X renders on the LEFT of a -Y camera; +Y is toward the camera.
LAYOUTS = {
    'landscape': dict(
        w=2560, h=1440, lens=50.0, fstop=2.0,
        cam=(0.95, -6.95, FLOOR + 1.52),
        target=(0.44, -10.90, FLOOR + 1.73),   # aim high -> 15 % empty band on top
        char=dict(pos=(0.55, -10.90, FLOOR), height=2.15),
        shoji=dict(x=0.44, y=-13.45, z0=FLOOR + 1.05, w=3.10, h=2.24, cols=6, rows=4),
        whales=[
            ('whale_glow_halo', 1.62, (2.22, -12.82, FLOOR + 0.86), (0.26, 0.60, 1.0), 0.22),
            ('whale_glow_big', 1.45, (2.22, -12.72, FLOOR + 0.94), (0.20, 0.56, 1.0), 0.62),
            ('whale_glow_small', 0.50, (-1.55, -12.85, FLOOR + 1.92), (1.0, 0.76, 0.45), 1.02),
        ],
        cards=[
            ('first_hello.txt', (1.30, -10.35, FLOOR + 1.96), 0.56, 0.235, -7.0, 4.0),
            ('laugh_0314.txt', (0.10, -10.06, FLOOR + 1.98), 0.54, 0.228, 8.0, 3.0),
            ('see_you.txt', (1.46, -11.20, FLOOR + 2.26), 0.40, 0.170, 9.0, -4.0),
        ],
    ),
    'portrait': dict(
        w=1800, h=2700, lens=50.0, fstop=2.3,
        cam=(0.92, -6.60, FLOOR + 1.30),
        target=(0.44, -10.90, FLOOR + 1.36),
        char=dict(pos=(0.55, -10.90, FLOOR), height=2.15),
        shoji=dict(x=0.44, y=-13.50, z0=FLOOR + 1.12, w=2.70, h=2.32,
                   cols=4, rows=3, strength=1.10, cool=0.34),
        whales=[
            ('whale_glow_halo', 1.52, (1.95, -12.92, FLOOR + 0.50), (0.26, 0.60, 1.0), 0.18),
            ('whale_glow_big', 1.34, (1.95, -12.82, FLOOR + 0.56), (0.20, 0.56, 1.0), 0.58),
            ('whale_glow_small', 0.42, (-0.30, -12.55, FLOOR + 2.26), (1.0, 0.76, 0.45), 0.98),
        ],
        cards=[
            ('first_hello.txt', (1.02, -10.35, FLOOR + 1.90), 0.46, 0.200, -6.0, 3.0),
            ('laugh_0314.txt', (-0.16, -10.30, FLOOR + 1.82), 0.46, 0.200, 8.0, -4.0),
        ],
    ),
}


# --------------------------------------------------------------------------- helpers
def _bsdf(mat):
    for n in mat.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            return n
    return None


def _unlink(nt, socket):
    for link in list(nt.links):
        if link.to_socket == socket:
            nt.links.remove(link)


def _glow(mat, tint, strength):
    """Turn a paper-cutout texture material into a clean tinted glow (silhouettes)."""
    nt = mat.node_tree
    bsdf = _bsdf(mat)
    if bsdf is None:
        return mat
    _unlink(nt, bsdf.inputs['Emission Color'])
    bsdf.inputs['Emission Color'].default_value = (*tint, 1.0)
    bsdf.inputs['Emission Strength'].default_value = strength
    _unlink(nt, bsdf.inputs['Base Color'])
    bsdf.inputs['Base Color'].default_value = (0.02, 0.025, 0.030, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.92
    try:
        mat.surface_render_method = 'BLENDED'
    except Exception:
        pass
    return mat


def _paper_glow(name, base, emission_color, emission_strength, rough=0.86):
    """Paper with a faint self-glow (index cards read even in the dark)."""
    m = C.paper(name, base=base, rough=rough, fiber=0.6)
    b = _bsdf(m)
    if b is not None:
        b.inputs['Emission Color'].default_value = (*emission_color, 1.0)
        b.inputs['Emission Strength'].default_value = emission_strength
    return m


def _shoji(cfg, name='shoji'):
    """Cool, bright paper screen behind her + thin ink mullion grid."""
    x, y, z0, w, h = cfg['x'], cfg['y'], cfg['z0'], cfg['w'], cfg['h']
    cols, rows = cfg.get('cols', 6), cfg.get('rows', 4)
    warm = C.emissive('m_shoji_warm', (1.00, 0.962, 0.898),
                      cfg.get('strength', 1.30))   # warm-white daylight paper
    warm2 = C.emissive('m_shoji_warm2', (0.70, 0.85, 1.00),
                       cfg.get('cool', 0.40))      # faint cool sky wash
    g = G.Geo(name)
    g.plane(1.0, (x, y - 0.03, z0 + h * 0.5), (math.pi / 2, 0, 0), warm, sx=w, sy=h)
    g.plane(1.0, (x, y, z0 + h * 0.5), (math.pi / 2, 0, 0), warm2, sx=w, sy=h)
    screen = g.build()
    screen.visible_shadow = False

    ink = _paper_glow('m_shoji_ink', (0.085, 0.072, 0.060), (0.03, 0.05, 0.08), 0.02,
                      rough=0.92)
    bar = 0.017                      # thin lattice
    f = G.Geo(name + '_frame')
    f.box((w + 0.10, 0.045, 0.055), (x, y + 0.02, z0 - 0.02), (0, 0, 0), ink)
    f.box((w + 0.10, 0.045, 0.055), (x, y + 0.02, z0 + h + 0.02), (0, 0, 0), ink)
    f.box((0.055, 0.045, h), (x - w * 0.5 - 0.02, y + 0.02, z0 + h * 0.5), (0, 0, 0), ink)
    f.box((0.055, 0.045, h), (x + w * 0.5 + 0.02, y + 0.02, z0 + h * 0.5), (0, 0, 0), ink)
    for k in range(1, cols):
        f.box((bar, 0.040, h), (x - w * 0.5 + w * k / float(cols), y + 0.02,
                                z0 + h * 0.5), (0, 0, 0), ink)
    for k in range(1, rows):
        f.box((w, 0.040, bar), (x, y + 0.02, z0 + h * k / float(rows)),
              (0, 0, 0), ink)
    return screen, f.build()


def _whale_silhouettes(spec):
    """Glowing paper whales behind her (one cool big + one warm small)."""
    out = []
    for name, hgt, loc, tint, strength in spec:
        front, mat, back = C.paper_cutout(SILHOUETTE, height=hgt, loc=loc, name=name,
                                         emission_strength=0.0)
        _glow(mat, tint, strength)
        if back is not None:
            bm = back.data.materials[0] if back.data.materials else None
            if bm is not None:
                _glow(bm, tuple(c * 0.35 for c in tint), strength * 0.5)
            back.visible_shadow = False
        front.visible_shadow = False
        out.append(front)
    return out


def _index_cards(spec):
    """Floating paper memory cards with typed filenames (paper + ink, camera-facing).

    Cards face +Y (toward the camera). A plane whose normal faces -Y would be lit
    by the warm rim light that sits behind the cards and would read as a blown
    white rectangle; facing the camera keeps them as quiet paper lit from our side.
    Text sits 8 mm in front of the card and is rotated (-90 deg X, 180 deg Y) so the
    glyphs read the right way round from the camera (up = +Z, reading = -X).
    """
    card_mat = C.paper('m_idx_card_paper', base=(0.640, 0.618, 0.566),
                       rough=0.88, fiber=0.7)
    ink = C.paper('m_idx_ink', base=(0.052, 0.058, 0.070), rough=0.90, fiber=0.2)
    out = []
    for i, (text, loc, cw, ch, yaw, tilt) in enumerate(spec):
        x, y, z = loc
        # plane normal -> +Y (camera side)
        rot = (-math.pi / 2 - math.radians(tilt), 0.0, math.radians(yaw))
        g = G.Geo('idx_card_%02d' % i)
        g.plane(1.0, (x, y, z), rot, card_mat, sx=cw, sy=ch)
        card = g.build()
        card.visible_shadow = False
        # fit the typed line to the card width (Consolas advance ~0.52 em)
        tsize = min(ch * 0.32, 0.88 * cw / (max(1, len(text)) * 0.52))
        tob = C.text_obj('idx_text_%02d' % i, text, size=tsize,
                         loc=(x, y + 0.008, z - tsize * 0.40),
                         rot=(-math.pi / 2, math.pi, math.radians(yaw * 0.6)),
                         font=CONSOLAS, mat=ink, align='CENTER', extrude=0.0)
        out += [card, tob]
    return out


def _threads(char, anchor_top=FLOOR + 4.35):
    """Marionette threads from above down to her head and shoulders."""
    mat = C.paper('m_thread', base=(0.075, 0.068, 0.058), rough=0.95, fiber=0.3)
    cp = char['pos']
    ch = char['height']
    g = G.Geo('puppet_threads')
    head = (cp[0], cp[1], FLOOR + ch * 0.97)
    lsh = (cp[0] - 0.27, cp[1], FLOOR + ch * 0.78)
    rsh = (cp[0] + 0.27, cp[1], FLOOR + ch * 0.78)
    for tip, dx in ((head, -0.02), (lsh, -0.34), (rsh, 0.30)):
        top = (tip[0] + dx, tip[1] + 0.05, anchor_top)
        import mathutils
        a = mathutils.Vector(top)
        b = mathutils.Vector(tip)
        d = b - a
        mid = (a + b) * 0.5
        rot = d.to_track_quat('Z', 'Y').to_euler()
        g.cylinder(0.0026, d.length, tuple(mid), tuple(rot), mat, seg=5)
    return g.build()


def _scraps(seed=11, n=24):
    """Out-of-focus paper scraps falling between the camera and her."""
    rnd = random.Random(seed)
    warm = C.emissive('m_scrap_warm', (0.56, 0.50, 0.40), 0.34)
    cold = C.emissive('m_scrap_cold', (0.18, 0.38, 0.60), 0.85)
    g = G.Geo('poster_scraps')
    for i in range(n):
        x = rnd.uniform(-2.05, 2.55)
        y = rnd.uniform(-10.05, -8.05)
        z = FLOOR + rnd.uniform(1.05, 3.0)
        w = rnd.uniform(0.022, 0.078)
        h = w * rnd.uniform(0.65, 1.6)
        g.plane(1.0, (x, y, z),
                (rnd.uniform(-0.9, 0.9), rnd.uniform(-1.2, 1.2), rnd.uniform(0, 6.28)),
                cold if i % 5 == 0 else warm, sx=w, sy=h)
    # a couple of big, very out-of-focus scraps framing the top area
    for x, y, z, w, m in ((-2.30, -8.30, FLOOR + 0.98, 0.21, warm),
                          (2.60, -8.05, FLOOR + 2.85, 0.13, warm)):
        g.plane(1.0, (x, y, z), (rnd.uniform(-0.8, 0.8), rnd.uniform(-1.0, 1.0),
                                rnd.uniform(0, 6.28)), m, sx=w, sy=w * 1.3)
    ob = g.build()
    ob.visible_shadow = False
    return ob


# --------------------------------------------------------------------------- scene
def build(layout='landscape', w=960, h=540, samples=24):
    t0 = time.time()
    L = LAYOUTS[layout]
    char = L['char']
    K.begin(samples=samples, fog_density=FOG_DENSITY, fog_color=FOG_COLOR,
            ambient=AMBIENT, exposure=0.18)
    sc = bpy.context.scene
    sc.render.resolution_x = w
    sc.render.resolution_y = h
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'

    # the paper theatre (floor, wings, backdrop, batten, railing, lanterns, desk ...)
    T.theatre(seed=3)

    _shoji(L['shoji'])
    _whale_silhouettes(L['whales'])
    _index_cards(L['cards'])

    # her: half-body paper cut-out (bust crops the feet below the frame)
    front, cmat, back = C.paper_cutout(
        os.path.join(C.TEX, 'galgame', 'whale-starry.webp'),
        height=char['height'], loc=char['pos'], name='poster_char',
        emission_strength=0.055)
    for ob in (front, back):
        if ob is not None:
            # ADD to the standing rotation: illustration_card already sets
            # rotation_euler = (90 deg, 0, 180 deg); overwriting lays her flat.
            e = ob.rotation_euler
            ob.rotation_euler = (e.x, e.y, e.z + math.radians(-9.0))

    _threads(char)
    _scraps()

    # lighting: canonical theatre rig + soft warm face fill + cold kicker
    try:
        import stage as S
        S.lighting('default')
    except Exception:
        pass

    face = bpy.data.objects.new('poster_face_tgt', None)
    bpy.context.collection.objects.link(face)
    face.location = (char['pos'][0], char['pos'][1], FLOOR + char['height'] * 0.88)
    C.light('poster_face_fill', 'AREA', loc=(-1.05, -8.20, FLOOR + 2.45),
            energy=95, color=(1.0, 0.80, 0.58), size=2.4, target=face)
    Lk = C.light('poster_back_kick', 'AREA', loc=(1.90, -13.10, FLOOR + 2.80),
                 energy=200, color=(0.26, 0.60, 1.0), size=2.0)
    C.look_at(Lk, (char['pos'][0], char['pos'][1], FLOOR + char['height'] * 0.70))

    # warm rim: sits between her and the shoji, rims her silhouette from behind
    Lr = C.light('poster_rim_warm', 'AREA', loc=(0.42, -12.10, FLOOR + 2.55),
                 energy=430, color=(1.0, 0.73, 0.46), size=1.7)
    C.look_at(Lr, (char['pos'][0], char['pos'][1] + 0.30,
                   FLOOR + char['height'] * 0.78))

    C.dust('poster_dust', count=380, extent=(5.0, 6.0, 4.6),
           center=(0.35, -10.60, FLOOR + 2.30), size=0.006,
           color=(0.62, 0.84, 1.0), strength=1.9)

    cam = C.camera('poster_cam', lens=L['lens'], loc=L['cam'], target=L['target'],
                   dof=True, fstop=L['fstop'])
    sc.camera = cam
    sc.frame_set(1)

    print('POSTER build %.2fs  layout=%s %dx%d objects=%d'
          % (time.time() - t0, layout, w, h, len(bpy.data.objects)), flush=True)
    return cam


def render(path=None, layout='landscape', w=960, h=540, samples=24):
    if not path:
        path = os.path.join(OUT_DIR, 'poster_%s_%dx%d.png' % (layout, w, h))
    elif not os.path.isabs(path):
        # relative --out names land in OUT_DIR (paths may not contain spaces
        # on the --args command line, so keep it to a bare filename)
        path = os.path.join(OUT_DIR, path)
    build(layout=layout, w=w, h=h, samples=samples)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sc = bpy.context.scene
    sc.render.filepath = path
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    print('POSTER render %s %dx%d %d spp  %.2fs -> %s'
          % (layout, w, h, samples, time.time() - t0, path), flush=True)
    return path


def _args():
    argv = sys.argv
    if '--' in argv:
        argv = argv[argv.index('--') + 1:]
    else:
        argv = []
    d = {'w': None, 'h': None, 'samples': 24, 'out': None, 'portrait': False}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '--portrait':
            d['portrait'] = True
            i += 1
        elif a in ('--w', '--h', '--samples', '--out') and i + 1 < len(argv):
            key = a[2:]
            val = argv[i + 1]
            d[key] = val if key == 'out' else int(val)
            i += 2
        else:
            i += 1
    return d


if __name__ == '__main__':
    a = _args()
    layout = 'portrait' if a['portrait'] else 'landscape'
    L = LAYOUTS[layout]
    if a['w'] and a['h']:
        w, h = a['w'], a['h']
    elif layout == 'portrait':
        w, h = L['w'], L['h']
    else:
        w, h = 960, 540          # landscape default = quick preview
    render(path=a['out'], layout=layout, w=w, h=h, samples=a['samples'])
