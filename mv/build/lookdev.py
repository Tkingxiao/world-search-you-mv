"""lookdev.py - look development v3: sunken paper archive + character card.
blender -b --factory-startup -P lookdev.py
"""
import bpy, sys, os, math, random, time
sys.path.insert(0, r'D:\Code\Code MV\new-word.search(you)\mv\build')
import core as C
import world as W
from mathutils import Vector

OUT = os.path.join(C.MV, 'out', 'lookdev')
os.makedirs(OUT, exist_ok=True)
random.seed(11)
t0 = time.time()

sc = C.reset()
C.setup_render(samples=24, w=960, h=540, glare=True)
print('RENDER_SETUP', round(time.time() - t0, 2), flush=True)

# ---------------------------------------------------------------- world
C.fog_world(density=0.016, color=(0.010, 0.052, 0.080), ambient=(0.004, 0.016, 0.028))
W.seabed(120, -6.02)
W.archive_aisle(seed=2)
W.loose_sheets(24, seed=9)
W.water_surface(z=9.0, size=160, strength=0.9)
W.caustic_floor(size=30, z=-5.955, strength=0.09)
W.hanging_index_sheet(loc=(0.05, -12.5, 2.35), rotz=0.05, w=2.6, h=3.3)

# practical lanterns along the aisle + their real point lights
lamp_pos = []
for i in range(7):
    y = -5.0 - i * 3.4
    for sx in (-1, 1):
        lamp_pos.append((sx * 2.45, y + random.uniform(-0.2, 0.2), 1.55 + random.uniform(-0.15, 0.15)))
W.practical_lamps(lamp_pos, color=(1.0, 0.52, 0.24), energy=9.0, size=0.05)
for i in range(0, 7, 2):
    L = C.light(f'lamp_L{i}', 'POINT', loc=(2.45, -5.0 - i * 3.4, 1.55), energy=22, color=(1.0, 0.48, 0.22), size=0.25)
    L = C.light(f'lamp_R{i}', 'POINT', loc=(-2.45, -5.0 - i * 3.4, 1.55), energy=22, color=(1.0, 0.48, 0.22), size=0.25)

# light shafts from the surface
for i, (x, y) in enumerate([(0.5, -9.5), (-1.4, -14.5), (1.6, -20.0)]):
    W.shaft(f'shaft{i}', top=(x, y, 8.8), bottom=(x + 0.5, y + 0.3, -5.9),
            color=(1.0, 0.66, 0.38), strength=0.55, angle_deg=13.0)

# ---------------------------------------------------------------- subject
P = dict(
    plinth=C.paper('m_plinth2', base=(0.52, 0.49, 0.42)),
    table=C.paper('m_spec2', base=(0.83, 0.80, 0.70)),
)
plinth = C.box('plinth', (0.95, 0.85, 1.05), loc=(1.10, -6.2, -5.98 + 0.525), mat=P['plinth'])
spec = C.box('spec_table', (0.85, 0.55, 0.10), loc=(1.10, -6.2, -4.88), mat=P['table'])
# a glass case over the specimen
case = C.box('case', (0.92, 0.62, 0.5), loc=(1.10, -6.2, -4.62), mat=C.glass('m_case'))
case.display_type = 'WIRE' if False else 'TEXTURED'
card, cmat = C.illustration_card(os.path.join(C.TEX, 'galgame', 'whale-cheerful.webp'),
                                height=1.74, loc=(-0.85, -6.55, -6.0))
C.text_obj('label_name', 'TABLE', size=0.115, loc=(1.72, -6.62, -4.42),
           rot=(math.radians(90), 0, 0), font='C:/Windows/Fonts/georgia.ttf',
           mat=C.text_mat('m_label_ink', (0.03, 0.03, 0.035)))
C.text_obj('label_data', 'sim 0.31   mass 0.00 kg   fn: surface', size=0.042,
           loc=(1.72, -6.63, -4.53), rot=(math.radians(90), 0, 0),
           font='C:/Windows/Fonts/consola.ttf', mat=C.text_mat('m_label_ink2', (0.10, 0.10, 0.10)))
print('WORLD+SUBJECT', round(time.time() - t0, 2), 'objects', len(bpy.data.objects), flush=True)

# ---------------------------------------------------------------- lights
W.aisle_lights(target=(0.2, -6.0, 0.2))
# key: warm pool on the subject from upper right
tgt = bpy.data.objects.new('key2_tgt', None); bpy.context.collection.objects.link(tgt)
tgt.location = (0.3, -6.3, -0.2)
L = C.light('key2', 'SPOT', loc=(2.6, -3.0, 5.2), energy=5200, color=(1.0, 0.70, 0.46),
            size=0.25, angle=math.radians(38), target=tgt)
L.data.volume_factor = 1.2
# cool bounce from below-left to shape the paper
L = C.light('bounce', 'AREA', loc=(-2.4, -8.2, -3.4), energy=180, color=(0.18, 0.42, 0.75), size=3.0)
C.look_at(L, (0.0, -6.4, 0.0))
C.dust('dust', count=900, extent=(9, 14, 8), center=(0, -9, 1.0), size=0.008,
       color=(0.55, 0.85, 1.0), strength=3.0)
print('LIGHTS', round(time.time() - t0, 2), 'objects', len(bpy.data.objects), flush=True)

# ---------------------------------------------------------------- cameras + renders
shots = []
def look(name, cam_loc, target, lens=40, fstop=2.4):
    cam = C.camera('cam_' + name, lens=lens, loc=cam_loc, target=target, dof=True, fstop=fstop)
    shots.append((name, cam))

look('wide',   (0.05, -12.6, 1.30), (0.25, -6.3, 0.45), lens=38, fstop=2.8)
look('medium', (0.45, -9.55, 1.00), (0.35, -6.4, 0.20), lens=55, fstop=2.2)
look('close',  (-0.65, -8.15, 0.55), (-0.9, -6.6, -0.15), lens=85, fstop=1.8)
look('aisle',  (0.0, -3.4, 1.55), (0.1, -20.0, 0.9), lens=30, fstop=4.0)

for name, cam in shots:
    sc.camera = cam
    sc.render.filepath = os.path.join(OUT, f'look3_{name}.png')
    ts = time.time()
    bpy.ops.render.render(write_still=True)
    print('RENDERED', name, round(time.time() - ts, 2), 's', flush=True)
print('DONE', round(time.time() - t0, 1), flush=True)
