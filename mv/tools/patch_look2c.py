"""Lighting tune pass 2: stronger warm key + floor pool + real window shaft, calmer tags."""
import io
import py_compile

ROOT = r'D:\Code\Code MV\new-word.search(you)\mv\build'


def sub(name, old, new):
    p = ROOT + '\\' + name
    s = io.open(p, encoding='utf-8').read()
    assert old in s, '[FAIL] anchor %r in %s' % (old[:50], name)
    s = s.replace(old, new, 1)
    io.open(p, 'w', encoding='utf-8').write(s)
    print('[ok] %s' % name)


# key: hotter and wider so the paper gets that warm tungsten pool
sub('stage.py',
    "    L = C.light('stage_key2', 'SPOT', loc=(-3.05, -6.55, FLOOR + 4.85), energy=3300,\n"
    "                color=(1.0, 0.72, 0.48), size=0.24, angle=math.radians(30), target=t)\n"
    "    L.data.volume_factor = 2.2",
    "    L = C.light('stage_key2', 'SPOT', loc=(-3.05, -6.55, FLOOR + 4.85), energy=6200,\n"
    "                color=(1.0, 0.66, 0.40), size=0.24, angle=math.radians(33), target=t)\n"
    "    L.data.volume_factor = 3.0")

# window shaft: from *in front of* the shoji, into the house -> visible beam in the haze
sub('stage.py',
    "    L = C.light('window_beam2', 'SPOT', loc=(0.0, -23.2, FLOOR + 3.2), energy=2600,\n"
    "                color=(0.55, 0.78, 1.0), size=1.2, angle=math.radians(46))\n"
    "    C.look_at(L, (0.0, -12.0, FLOOR + 0.6))\n"
    "    L.data.volume_factor = 2.4",
    "    L = C.light('window_beam2', 'SPOT', loc=(0.0, -20.6, FLOOR + 3.05), energy=3600,\n"
    "                color=(0.55, 0.78, 1.0), size=0.9, angle=math.radians(42))\n"
    "    C.look_at(L, (0.25, -8.6, FLOOR + 0.35))\n"
    "    L.data.volume_factor = 4.2")

# warm floor pool in front of the playing area
sub('stage.py',
    "    # --- practicals terminal glow",
    "    # --- practicals terminal glow") if False else None
sub('stage.py',
    "    # --- practical terminal glow",
    "    # --- WARM FLOOR POOL: the light that the puppet stands in\n"
    "    L = C.light('floor_pool2', 'POINT', loc=(0.75, -8.9, FLOOR + 0.55), energy=520,\n"
    "                color=(1.0, 0.62, 0.34), size=1.30)\n"
    "    L.data.volume_factor = 1.6\n"
    "    L.data.use_shadow = False\n\n"
    "    # --- practical terminal glow")

# calmer hanging tags: higher, fewer, smaller
sub('look2.py', "def hanging_tags(seed=13, n=16):", "def hanging_tags(seed=13, n=11):")
sub('look2.py',
    "        z = FLOOR + rnd.uniform(3.2, 5.3)",
    "        z = FLOOR + rnd.uniform(4.35, 5.25)")
sub('look2.py',
    "        w = rnd.uniform(0.10, 0.19)",
    "        w = rnd.uniform(0.085, 0.15)")

for f in ('stage.py', 'look2.py'):
    py_compile.compile(ROOT + '\\' + f, doraise=True)
print('compiled OK')
