"""gui_build.py - build the archive set live inside the GUI Blender (watch-along).
Floor is at z = -6. Everything sits on it.
"""
import bpy, sys, os, math, random
sys.path.insert(0, r'D:\Code\Code MV\new-word.search(you)\mv\build')
for _m in ('core', 'world', 'geo'):
    sys.modules.pop(_m, None)
import core as C
import world as W
import geo as G
from mathutils import Vector

OUT = os.path.join(C.MV, 'out', 'lookdev')
os.makedirs(OUT, exist_ok=True)
random.seed(11)
FLOOR = -6.0

sc = C.reset_soft()
C.setup_render(samples=32, w=2560, h=1440, glare=True)
sc.view_settings.exposure = 0.55
C.fog_world(density=0.015, color=(0.008, 0.045, 0.072), ambient=(0.004, 0.016, 0.030))

# ---------------- world
W.seabed(120, FLOOR - 0.02)
W.archive_aisle(seed=2)
W.loose_sheets(24, seed=9)
W.water_surface(z=9.0, size=160, strength=0.5)
W.caustic_floor(size=30, z=FLOOR + 0.045, strength=0.10)
W.hanging_index_sheet(loc=(-2.85, -16.5, -0.8), rotz=0.22, w=2.4, h=3.1)

lamp_pos = []
for i in range(7):
    y = -5.0 - i * 3.4
    for sx in (-1, 1):
        lamp_pos.append((sx * 2.30, y + random.uniform(-0.2, 0.2), -0.9 + random.uniform(-0.2, 0.2)))
W.practical_lamps(lamp_pos, color=(1.0, 0.52, 0.24), energy=9.0, size=0.05)
for i in range(0, 7, 2):
    C.light(f'lamp_L{i}', 'POINT', loc=(2.30, -5.0 - i * 3.4, -0.9), energy=34, color=(1.0, 0.48, 0.22), size=0.25)
    C.light(f'lamp_R{i}', 'POINT', loc=(-2.30, -5.0 - i * 3.4, -0.9), energy=34, color=(1.0, 0.48, 0.22), size=0.25)

for i, (x, y) in enumerate([(0.5, -9.5), (-1.4, -14.5), (1.6, -20.0)]):
    W.shaft(f'shaft{i}', top=(x, y, 8.8), bottom=(x + 0.5, y + 0.3, FLOOR + 0.05),
            color=(1.0, 0.66, 0.38), strength=0.5, angle_deg=13.0)

# ---------------- specimen 01: the table under glass, on a plinth
P = dict(plinth=C.paper('m_plinth2', base=(0.36, 0.335, 0.29)),
         table=C.paper('m_spec2', base=(0.78, 0.74, 0.63)))
C.box('plinth', (0.95, 0.85, 1.05), loc=(0.95, -9.6, FLOOR + 0.525), mat=P['plinth'])
C.box('plinth_cap', (1.03, 0.93, 0.05), loc=(0.95, -9.6, FLOOR + 1.075), mat=P['table'])
W.papercraft_table(size=0.30, loc=(0.95, -9.6, FLOOR + 1.10), rotz=0.18)
W.bell_jar(r=0.27, h=0.50, loc=(0.95, -9.6, FLOOR + 1.10))
C.text_obj('plaque_title', 'SPECIMEN 01', size=0.085, loc=(0.95, -9.16, FLOOR + 0.72),
           rot=(math.radians(90), 0, math.pi), font='C:/Windows/Fonts/georgia.ttf',
           mat=C.text_mat('m_plaque_ink', (0.02, 0.02, 0.025)))
C.text_obj('plaque_sub', 'TABLE / sim 0.31', size=0.040, loc=(0.95, -9.16, FLOOR + 0.63),
           rot=(math.radians(90), 0, math.pi), font='C:/Windows/Fonts/consola.ttf',
           mat=C.text_mat('m_plaque_ink2', (0.05, 0.05, 0.055)))

# ---------------- character: paper cut-out of the official art
front, cmat, back = C.paper_cutout(os.path.join(C.TEX, 'galgame', 'whale-cheerful.webp'),
                                   height=1.74, loc=(-1.05, -9.2, FLOOR),
                                   emission_strength=0.10, name='whale_paper')
front.rotation_euler.z += math.radians(6)
back.rotation_euler.z += math.radians(6)

# ---------------- floating paper strips inside the light
g = G.Geo('paper_motes')
strip_mat = C.paper('m_strip', base=(0.85, 0.80, 0.68), rough=0.6)
for i in range(60):
    x = random.uniform(-1.2, 1.6)
    y = random.uniform(-12.5, -7.5)
    z = random.uniform(FLOOR + 0.3, FLOOR + 5.5)
    g.plane(random.uniform(0.02, 0.06), (x, y, z),
            (random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(0, 6.28)), strip_mat)
g.build()

# ---------------- lights
W.aisle_lights(target=(0.0, -9.6, FLOOR + 1.6), z0=FLOOR)
tgt = bpy.data.objects.new('key2_tgt', None); bpy.context.collection.objects.link(tgt)
tgt.location = (0.3, -9.7, FLOOR + 1.3)
L = C.light('key2', 'SPOT', loc=(2.2, -6.6, 2.0), energy=5200, color=(1.0, 0.70, 0.46),
            size=0.25, angle=math.radians(34), target=tgt)
L.data.volume_factor = 1.2
# character rim (cyan from behind-left)
L = C.light('char_rim', 'AREA', loc=(-2.2, -11.6, FLOOR + 2.6), energy=260, color=(0.12, 0.48, 1.0), size=1.6)
C.look_at(L, (-1.05, -9.2, FLOOR + 1.2))
# character key (warm, low, from camera-left)
L = C.light('char_key', 'AREA', loc=(-2.6, -6.6, FLOOR + 2.2), energy=220, color=(1.0, 0.78, 0.58), size=2.2)
C.look_at(L, (-1.05, -9.2, FLOOR + 1.0))
# index sheet reading light
L = C.light('sheet_light', 'SPOT', loc=(-1.0, -12.4, FLOOR + 6.8), energy=180, color=(1.0, 0.82, 0.62),
            size=0.4, angle=math.radians(50))
C.look_at(L, (-2.85, -16.5, FLOOR + 5.2))
C.dust('dust', count=900, extent=(9, 14, 8), center=(0, -11, FLOOR + 4.0), size=0.008,
       color=(0.55, 0.85, 1.0), strength=3.0)

# ---------------- camera: wide establishing shot down the aisle
cam = C.camera('cam_wide', lens=38, loc=(0.15, -4.2, FLOOR + 2.9),
               target=(0.30, -9.6, FLOOR + 1.35), dof=True, fstop=2.8)
sc.camera = cam
sc.frame_set(1)

# ---------------- viewport: camera view, RENDERED shading so we see real light
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'RENDERED'
                space.overlay.show_overlays = False
                space.region_3d.view_perspective = 'CAMERA'
                space.region_3d.view_camera_zoom = 6

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(C.MV, 'lookdev.blend'))
print('GUI_BUILD_OK objects', len(bpy.data.objects), flush=True)
