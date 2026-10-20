"""Final look settings: motion blur OFF by default, glare quality MEDIUM parametrised."""
import io
import py_compile

P = r'D:\Code\Code MV\new-word.search(you)\mv\build\core.py'
s = io.open(P, encoding='utf-8').read()

old = """    try:
        import os as _os
        sc.render.use_motion_blur = _os.environ.get('MV_NO_MB', '0') != '1'
        sc.render.motion_blur_shutter = 0.45
    except Exception:
        pass"""
new = """    try:
        import os as _os
        # NOTE: EEVEE-Next motion blur is 8-10x per frame on this scene mix (BLENDED paper
        # cards + world volume), measured 24s vs 2.5s at 1440p -> OFF unless explicitly asked.
        sc.render.use_motion_blur = _os.environ.get('MV_MOTION_BLUR', '0') == '1'
        sc.render.motion_blur_shutter = 0.45
    except Exception:
        pass"""
if old in s:
    s = s.replace(old, new, 1)
    print('[ok] motion blur default off')
elif new in s:
    print('[skip] motion blur already off by default')
else:
    raise SystemExit('[FAIL] motion blur anchor not found')

old2 = "def add_glare(sc, threshold=1.0, size=8, mix=-0.55):"
new2 = "def add_glare(sc, threshold=1.0, size=8, mix=-0.55, quality='MEDIUM'):"
if old2 in s:
    s = s.replace(old2, new2, 1)
    print('[ok] add_glare quality param')
old3 = "    gl.quality = 'HIGH'"
new3 = "    gl.quality = quality"
if old3 in s:
    s = s.replace(old3, new3, 1)
    print('[ok] glare quality uses param')
io.open(P, 'w', encoding='utf-8').write(s)
py_compile.compile(P, doraise=True)
print('compiled OK')
