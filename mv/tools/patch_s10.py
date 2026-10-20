import io

p = r'D:\Code\Code MV\new-word.search(you)\mv\build\shot_s10.py'
s = io.open(p, encoding='utf-8').read()

s2 = s.replace(
    "K.begin(samples=12, fog_density=0.030,\n"
    "            fog_color=(0.030, 0.055, 0.080), ambient=(0.020, 0.030, 0.042),\n"
    "            exposure=0.0)",
    "K.begin(samples=12, fog_density=0.014,\n"
    "            fog_color=(0.030, 0.055, 0.080), ambient=(0.020, 0.030, 0.042),\n"
    "            exposure=0.02)")
assert s2 != s, 'begin block not replaced'
s = s2

s2 = s.replace("spot.data.volume_factor = 2.2", "spot.data.volume_factor = 0.9")
assert s2 != s, 'volume_factor not replaced'
s = s2

s2 = s.replace(
    "    try:\n        T.theatre(seed=3)",
    "    # cheap volumetrics (s10 is the heaviest shot in the queue)\n"
    "    try:\n"
    "        bpy.context.scene.eevee.volumetric_samples = 24\n"
    "        bpy.context.scene.eevee.volumetric_start = 0.05\n"
    "    except Exception:\n"
    "        pass\n\n"
    "    try:\n        T.theatre(seed=3)")
assert s2 != s, 'volumetric block not inserted'
s = s2

io.open(p, 'w', encoding='utf-8').write(s)
print('patched shot_s10.py')
