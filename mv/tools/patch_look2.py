"""One-shot patch: look v2 (motion blur, theatrical rig, set dressing, handheld)."""
import io
import re
import py_compile

ROOT = r'D:\Code\Code MV\new-word.search(you)\mv\build'
FIX = 0


def patch(name, old, new, count=1):
    global FIX
    p = ROOT + '\\' + name
    s = io.open(p, encoding='utf-8').read()
    if new in s:
        print('[skip] %s already patched' % name)
        return
    if old not in s:
        raise SystemExit('[FAIL] anchor not found in %s: %r' % (name, old[:60]))
    s = s.replace(old, new, count)
    io.open(p, 'w', encoding='utf-8').write(s)
    FIX += 1
    print('[ok] %s' % name)


# ---------------------------------------------------------------- core.py: motion blur
patch('core.py',
      "    sc.eevee.taa_render_samples = samples\n",
      "    sc.eevee.taa_render_samples = samples\n"
      "    # camera-move polish: motion blur on (cheap in EEVEE-Next for camera-only moves)\n"
      "    try:\n"
      "        sc.render.use_motion_blur = True\n"
      "        sc.render.motion_blur_shutter = 0.45\n"
      "    except Exception:\n"
      "        pass\n")

# ---------------------------------------------------------------- core.py: fog anisotropy
patch('core.py',
      "def fog_world(density=0.012, color=(0.02, 0.09, 0.13), ambient=(0.008, 0.03, 0.05)):",
      "def fog_world(density=0.012, color=(0.02, 0.09, 0.13), ambient=(0.008, 0.03, 0.05),\n"
      "              anisotropy=0.35):")
patch('core.py',
      "    vol.inputs['Anisotropy'].default_value = 0.35",
      "    vol.inputs['Anisotropy'].default_value = anisotropy")

# ---------------------------------------------------------------- stage.py: dressing
patch('stage.py',
      "import core as C\nimport world_theater as T\nimport geo as G\n",
      "import core as C\nimport world_theater as T\nimport geo as G\nimport look2 as L2\n")

patch('stage.py',
      "def build_stage(char='cheerful', window_strength=1.05):\n    objs = T.theatre(seed=3)\n",
      "def build_stage(char='cheerful', window_strength=1.05, dress=True):\n"
      "    objs = T.theatre(seed=3)\n"
      "    if dress:\n"
      "        objs.update(L2.dress_all())\n")

# ---------------------------------------------------------------- stage.py: lighting v2
STAGE = io.open(ROOT + '\\stage.py', encoding='utf-8').read()
m = re.search(r"def lighting\(mood='default'\):.*?(?=\ndef cameras\()", STAGE, re.S)
if not m:
    raise SystemExit('[FAIL] lighting() block not found')
if 'stage_key2' not in m.group(0):
    NEW_LIGHT = '''def lighting(mood='default'):
    """Cinematic paper-theatre rig v2: hard warm key, cool rim, crossing beams,
    visible volumetric shafts, practical pools and a warm bounce card."""
    t = bpy.data.objects.new('key_tgt', None)
    bpy.context.collection.objects.link(t)
    t.location = (CHAR_LOC[0], CHAR_LOC[1], FLOOR + 1.15)

    # --- KEY: warm, hard, casts the only subject shadow
    L = C.light('stage_key2', 'SPOT', loc=(-3.05, -6.55, FLOOR + 4.85), energy=3300,
                color=(1.0, 0.72, 0.48), size=0.24, angle=math.radians(30), target=t)
    L.data.volume_factor = 2.2

    # --- RIM: cold kicker from behind camera-left
    L = C.light('stage_rim2', 'SPOT', loc=(2.55, -16.6, FLOOR + 3.9), energy=7200,
                color=(0.16, 0.50, 1.0), size=0.16, angle=math.radians(21))
    C.look_at(L, (CHAR_LOC[0], CHAR_LOC[1], FLOOR + 1.30))
    L.data.volume_factor = 3.2

    # --- TOP SHAFT: cool beam straight down onto the mark
    L = C.light('stage_shaft2', 'SPOT', loc=(1.05, -10.05, FLOOR + 8.0), energy=4300,
                color=(0.42, 0.70, 1.0), size=0.16, angle=math.radians(9.5))
    C.look_at(L, (0.85, -10.9, FLOOR))
    L.data.volume_factor = 5.0

    # --- WINDOW BEAM: huge soft beam of moonlight pouring out of the shoji
    L = C.light('window_beam2', 'SPOT', loc=(0.0, -23.2, FLOOR + 3.2), energy=2600,
                color=(0.55, 0.78, 1.0), size=1.2, angle=math.radians(46))
    C.look_at(L, (0.0, -12.0, FLOOR + 0.6))
    L.data.volume_factor = 2.4

    # --- SIDE BEAM: warm cross-light from stage right, low
    L = C.light('side_beam2', 'SPOT', loc=(3.6, -8.4, FLOOR + 2.9), energy=1600,
                color=(1.0, 0.68, 0.40), size=0.22, angle=math.radians(24))
    C.look_at(L, (-0.3, -12.4, FLOOR + 1.0))
    L.data.volume_factor = 1.7

    # --- FILL: soft cool front fill (no shadow)
    L = C.light('stage_fill2', 'AREA', loc=(CHAR_LOC[0] + 3.2, CHAR_LOC[1] + 5.0, FLOOR + 2.3),
                energy=85, color=(0.42, 0.62, 1.0), size=3.2)
    C.look_at(L, (CHAR_LOC[0], CHAR_LOC[1], FLOOR + 1.0))
    L.data.use_shadow = False

    # --- BOUNCE CARD: warm floor bounce from the left (classic film trick)
    L = C.light('bounce2', 'AREA', loc=(-2.4, -9.2, FLOOR + 0.75), energy=180,
                color=(1.0, 0.64, 0.38), size=2.2)
    C.look_at(L, (CHAR_LOC[0], CHAR_LOC[1], FLOOR + 1.45))
    L.data.use_shadow = False

    # --- WINDOW SPILL: cool ambience from behind the shoji
    L = C.light('window_spill2', 'AREA', loc=(0.0, -20.0, FLOOR + 3.0), energy=420,
                color=(0.58, 0.78, 1.0), size=4.4)
    C.look_at(L, (0.0, -11.5, FLOOR + 1.2))
    L.data.use_shadow = False

    # --- WALL WASH: makes the paper panels read
    L = C.light('wall_wash2', 'AREA', loc=(0.0, -16.0, FLOOR + 4.8), energy=150,
                color=(0.36, 0.54, 1.0), size=7.0)
    C.look_at(L, (0.0, -21.2, FLOOR + 3.6))
    L.data.use_shadow = False

    # --- practical terminal glow
    L = C.light('desk_pool2', 'POINT', loc=(-2.35, -10.1, FLOOR + 1.15), energy=42,
                color=(0.32, 1.0, 0.70), size=0.26)
    L.data.volume_factor = 1.1
    L.data.use_shadow = False

    C.dust('dust', count=1700, extent=(10, 14, 7.5), center=(0.2, -12.0, FLOOR + 3.0),
           size=0.006, color=(0.72, 0.88, 1.0), strength=3.0)


'''
    STAGE = STAGE[:m.start()] + NEW_LIGHT + STAGE[m.end():]
    io.open(ROOT + '\\stage.py', 'w', encoding='utf-8').write(STAGE)
    FIX += 1
    print('[ok] stage.py lighting v2')

# ---------------------------------------------------------------- stage.py: foreground papers
patch('stage.py',
      "def foreground_papers(seed=7, n=14):",
      "def foreground_papers(seed=7, n=20):")
patch('stage.py',
      "        x = side * rnd.uniform(1.25, 3.9)",
      "        x = side * rnd.uniform(1.05, 4.1)")

# ---------------------------------------------------------------- shotkit.py: handheld
patch('shotkit.py',
      "def ease(ob):",
      '''def add_handheld(cam, amp=0.012, scale=1.6, seed=0, rot_amp=0.0045):
    """Subtle operator drift: noise modifiers on location + rotation curves.

    Gives every move a living, hand-held quality without fighting the framing.
    Call AFTER cam_path() so the modifiers ride on the baked keys.
    """
    rnd = __import__('random').Random(seed)
    ad = cam.animation_data
    if ad is None:
        return cam
    for i, fc in enumerate(ad.action.fcurves):
        mod = fc.modifiers.new('NOISE')
        mod.scale = scale * rnd.uniform(0.8, 1.25)
        mod.strength = amp if i < 3 else rot_amp
        mod.phase = rnd.uniform(0, 100)
        mod.depth = 2
    return cam


def ease(ob):''')

# ---------------------------------------------------------------- render_shot.py: samples 12
patch('render_shot.py',
      "samples = int(args.get('samples', getattr(mod, 'SAMPLES', 8)))",
      "samples = int(args.get('samples', getattr(mod, 'SAMPLES', 12)))")

for f in ('core.py', 'stage.py', 'shotkit.py', 'render_shot.py', 'look2.py'):
    py_compile.compile(ROOT + '\\' + f, doraise=True)
print('compiled OK, %d edits' % FIX)
