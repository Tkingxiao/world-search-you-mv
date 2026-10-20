"""Attach look v2 dressing to T.theatre() itself so every shot inherits it."""
import io
import py_compile

ROOT = r'D:\Code\Code MV\new-word.search(you)\mv\build'

# --- world_theater: theatre(dress=True) adds the v2 set pieces
p = ROOT + r'\world_theater.py'
s = io.open(p, encoding='utf-8').read()
if 'import look2 as _l2' not in s:
    old = "def theatre(seed=3):\n"
    new = ("def theatre(seed=3, dress=True):\n")
    assert old in s
    s = s.replace(old, new, 1)
    tail_anchor = "    objs['desk'], objs['screen'], objs['lamp'] = terminal_desk(loc=(-2.45, -10.4, FLOOR))\n    return objs"
    assert tail_anchor in s
    s = s.replace(tail_anchor,
                  "    objs['desk'], objs['screen'], objs['lamp'] = terminal_desk(loc=(-2.45, -10.4, FLOOR))\n"
                  "    if dress:\n"
                  "        try:\n"
                  "            import look2 as _l2\n"
                  "            objs.update(_l2.dress_all())\n"
                  "        except Exception as _e:\n"
                  "            print('look2 dressing failed: %r' % (_e,), flush=True)\n"
                  "    return objs")
    io.open(p, 'w', encoding='utf-8').write(s)
    print('[ok] world_theater.theatre(dress=True)')

# --- stage.build_stage: theatre already dresses, avoid doing it twice
p = ROOT + r'\stage.py'
s = io.open(p, encoding='utf-8').read()
if 'def build_stage(char=' in s and 'if dress:\n        objs.update(L2.dress_all())' in s:
    s = s.replace("def build_stage(char='cheerful', window_strength=1.05, dress=True):",
                  "def build_stage(char='cheerful', window_strength=1.05):")
    s = s.replace("    objs = T.theatre(seed=3)\n    if dress:\n        objs.update(L2.dress_all())\n",
                  "    objs = T.theatre(seed=3)\n")
    s = s.replace("import look2 as L2\n", "")
    io.open(p, 'w', encoding='utf-8').write(s)
    print('[ok] stage.build_stage cleaned')

for f in ('world_theater.py', 'stage.py', 'look2.py'):
    py_compile.compile(ROOT + '\\' + f, doraise=True)
print('compiled OK')
