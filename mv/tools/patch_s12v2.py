"""s12: tame the white-out (exposure, shred/whale emission, local light dim)."""
import io
import py_compile

P = r'D:\Code\Code MV\new-word.search(you)\mv\build\shot_s12.py'
s = io.open(P, encoding='utf-8').read()

# 1) dim helper
if 'def _dim_all(' not in s:
    anchor = "def _bucket(loc):"
    helper = '''def _dim_all(factor=0.62):
    """Scale down every light except the tiny practicals (keeps the storm from blowing out)."""
    for L in bpy.data.lights:
        if L.name.startswith(('stage_key2', 'stage_shaft2', 'stage_fill2', 'window_beam2',
                              'stage_rim2', 'bounce2', 'window_spill2', 'floor_pool2')):
            L.energy *= factor


def _bucket(loc):'''
    assert anchor in s
    s = s.replace(anchor, helper, 1)

# 2) exposure + dim
s = s.replace("            ambient=(0.005, 0.018, 0.030), exposure=0.26)",
              "            ambient=(0.005, 0.018, 0.030), exposure=0.15)", 1)
s = s.replace("    T.theatre(seed=3)\n    S.lighting('default')\n",
              "    T.theatre(seed=3)\n    S.lighting('default')\n    _dim_all(0.58)\n", 1)

# 3) shreds + whale emission
s = s.replace("em = C.emissive('m_shred', (0.66, 0.60, 0.46), 0.42)",
              "em = C.emissive('m_shred', (0.58, 0.52, 0.40), 0.16)", 1)
s = s.replace("name='merged_whale', emission_strength=0.22)",
              "name='merged_whale', emission_strength=0.09)", 1)
s = s.replace("L = C.light('whale_back', 'AREA', loc=(0.55, -16.6, FLOOR + 2.6), energy=1400,",
              "L = C.light('whale_back', 'AREA', loc=(0.55, -16.6, FLOOR + 2.6), energy=900,", 1)
s = s.replace("L2 = C.light('whale_warm', 'AREA', loc=(-1.8, -9.6, FLOOR + 2.2), energy=320,",
              "L2 = C.light('whale_warm', 'AREA', loc=(-1.8, -9.6, FLOOR + 2.2), energy=220,", 1)

io.open(P, 'w', encoding='utf-8').write(s)
py_compile.compile(P, doraise=True)
print('[ok] s12 tamed')

# 4) global halo a touch weaker
p2 = r'D:\Code\Code MV\new-word.search(you)\mv\build\stage.py'
s2 = io.open(p2, encoding='utf-8').read()
s2 = s2.replace("4.6, 3.6, (0.10, 0.22, 0.55), strength=0.62",
                "4.6, 3.6, (0.10, 0.22, 0.55), strength=0.45", 1)
io.open(p2, 'w', encoding='utf-8').write(s2)
py_compile.compile(p2, doraise=True)
print('[ok] halo 0.45')
