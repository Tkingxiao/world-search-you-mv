import io

def patch(path, pairs):
    s = io.open(path, encoding='utf-8').read()
    for old, new in pairs:
        assert old in s, 'pattern missing in %s: %r' % (path, old[:60])
        s = s.replace(old, new)
    io.open(path, 'w', encoding='utf-8').write(s)
    print('patched', path)

patch(r'mv\build\world_theater.py', [
("""        L.data.volume_factor = 0.8
    ob = g.build()
    return ob""",
 """        L.data.volume_factor = 0.8
        L.data.use_shadow = False        # tiny bulb: shadow maps cost far more than they show
    ob = g.build()
    return ob"""),
("""        L = C.light(f'lantern_{i}', 'POINT', loc=(x, y, z), energy=16.0, color=color, size=0.10)
        L.data.volume_factor = 1.6""",
 """        L = C.light(f'lantern_{i}', 'POINT', loc=(x, y, z), energy=16.0, color=color, size=0.10)
        L.data.volume_factor = 1.6
        L.data.use_shadow = False        # tiny lantern: no shadow map"""),
])

patch(r'mv\build\stage.py', [
("""        L.data.volume_factor = 0.8
        # soft wash on the back wall""",
 """        L.data.volume_factor = 0.8
        L.data.use_shadow = False        # practical lamp: skip shadow map
        # soft wash on the back wall"""),
])

patch(r'mv\build\core.py', [
("""    for attr, val in (('use_raytracing', True), ('use_shadows', True),
                      ('volumetric_tile_size', '4'), ('volumetric_samples', 48),""",
"""    # NOTE: raytraced reflections are OFF on purpose: the look is matte paper, RT added
    # almost nothing visually yet dominated per-frame cost / VRAM with several renders
    # sharing the 8 GB card.
    for attr, val in (('use_raytracing', False), ('use_shadows', True),
                      ('volumetric_tile_size', '8'), ('volumetric_samples', 32),"""),
])
