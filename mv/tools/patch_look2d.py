"""Lighting pass 3: keep the proven v1 exposure, add shafts/pool/bounce carefully."""
import io
import re
import py_compile

P = r'D:\Code\Code MV\new-word.search(you)\mv\build\stage.py'
s = io.open(P, encoding='utf-8').read()

NEW = '''def lighting(mood='default'):
    """Paper-theatre rig v3: the proven v1 balance plus a real window shaft,
    a warm floor pool and a low bounce card (set dressing lives in look2.py)."""
    t = bpy.data.objects.new('key_tgt', None)
    bpy.context.collection.objects.link(t)
    t.location = (CHAR_LOC[0], CHAR_LOC[1], FLOOR + 1.15)

    # --- KEY: warm, hard, the only subject shadow
    L = C.light('stage_key2', 'SPOT', loc=(-2.30, -7.20, FLOOR + 4.40), energy=2400,
                color=(1.0, 0.70, 0.46), size=0.28, angle=math.radians(31), target=t)
    L.data.volume_factor = 2.4

    # --- RIM: cold kicker from behind
    L = C.light('stage_rim2', 'SPOT', loc=(1.50, -15.40, FLOOR + 3.60), energy=5600,
                color=(0.20, 0.54, 1.0), size=0.20, angle=math.radians(20))
    C.look_at(L, (CHAR_LOC[0], CHAR_LOC[1], FLOOR + 1.25))
    L.data.volume_factor = 3.4

    # --- FILL: soft cool front fill
    L = C.light('stage_fill2', 'AREA', loc=(CHAR_LOC[0] + 3.6, CHAR_LOC[1] + 5.2, FLOOR + 2.4),
                energy=90, color=(0.45, 0.66, 1.0), size=3.5)
    C.look_at(L, (CHAR_LOC[0], CHAR_LOC[1], FLOOR + 1.0))
    L.data.use_shadow = False

    # --- TOP SHAFT: cool beam down onto the mark
    L = C.light('stage_shaft2', 'SPOT', loc=(1.05, -9.80, FLOOR + 7.60), energy=3800,
                color=(0.44, 0.72, 1.0), size=0.20, angle=math.radians(11))
    C.look_at(L, (0.95, -10.9, FLOOR))
    L.data.volume_factor = 3.8

    # --- WINDOW SHAFT: from just in front of the shoji, low into the house
    L = C.light('window_beam2', 'SPOT', loc=(0.0, -20.35, FLOOR + 3.00), energy=2400,
                color=(0.56, 0.79, 1.0), size=0.85, angle=math.radians(44))
    C.look_at(L, (0.30, -8.8, FLOOR + 0.30))
    L.data.volume_factor = 3.0

    # --- WARM FLOOR POOL: the pool the puppet plays in
    L = C.light('floor_pool2', 'POINT', loc=(0.95, -9.30, FLOOR + 0.50), energy=160,
                color=(1.0, 0.62, 0.34), size=1.10)
    L.data.volume_factor = 1.3
    L.data.use_shadow = False

    # --- BOUNCE CARD: low warm bounce from camera left
    L = C.light('bounce2', 'AREA', loc=(-2.6, -9.0, FLOOR + 0.70), energy=80,
                color=(1.0, 0.66, 0.42), size=2.0)
    C.look_at(L, (CHAR_LOC[0], CHAR_LOC[1], FLOOR + 1.35))
    L.data.use_shadow = False

    # --- WINDOW SPILL: cool ambience out of the shoji
    L = C.light('window_spill2', 'AREA', loc=(0.0, -20.0, FLOOR + 3.0), energy=280,
                color=(0.60, 0.80, 1.0), size=4.2)
    C.look_at(L, (0.0, -11.5, FLOOR + 1.2))
    L.data.use_shadow = False

    # --- WALL WASH: makes the paper panels read
    L = C.light('wall_wash2', 'AREA', loc=(0.0, -15.8, FLOOR + 4.6), energy=115,
                color=(0.40, 0.58, 0.95), size=6.5)
    C.look_at(L, (0.0, -21.0, FLOOR + 3.4))
    L.data.use_shadow = False

    # --- practical terminal glow
    L = C.light('desk_pool2', 'POINT', loc=(-2.35, -10.1, FLOOR + 1.15), energy=55,
                color=(0.35, 1.0, 0.72), size=0.28)
    L.data.volume_factor = 0.8
    L.data.use_shadow = False

    C.dust('dust', count=1600, extent=(10, 14, 7.5), center=(0.2, -12.0, FLOOR + 3.0),
           size=0.006, color=(0.72, 0.88, 1.0), strength=2.6)


'''
m = re.search(r"def lighting\(mood='default'\):.*?(?=\ndef cameras\()", s, re.S)
assert m, 'lighting block not found'
s = s[:m.start()] + NEW + s[m.end():]
io.open(P, 'w', encoding='utf-8').write(s)
py_compile.compile(P, doraise=True)
print('lighting v3 written')
