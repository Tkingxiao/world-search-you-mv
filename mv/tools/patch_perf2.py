import io

def patch(path, pairs):
    s = io.open(path, encoding='utf-8').read()
    for old, new in pairs:
        assert old in s, 'pattern missing in %s: %r' % (path, old[:70])
        s = s.replace(old, new)
    io.open(path, 'w', encoding='utf-8').write(s)
    print('patched', path)

# 1) default samples 10 -> 8 for the shots that have not started yet
patch(r'mv\build\render_shot.py', [
    ("getattr(mod, 'SAMPLES', 10)", "getattr(mod, 'SAMPLES', 8)"),
])

# 2) big soft fill lights do not need shadow maps: their shadows are invisible but the
#    virtual shadow map pass costs a lot at 1440p.
patch(r'mv\build\stage.py', [
("""        L = C.light('fill', 'AREA', loc=(3.4, -9.2, FLOOR + 3.4), energy=90,""",
 """        L = C.light('fill', 'AREA', loc=(3.4, -9.2, FLOOR + 3.4), energy=90,"""),
])
s = io.open(r'mv\build\stage.py', encoding='utf-8').read()
# generic: any light created in stage.lighting() whose name is fill/window_spill/wall_wash
# gets use_shadow disabled right after creation.  The builder assigns to `L` every time,
# so we hook the look_at call that follows each of those three names.
for name in ('fill', 'window_spill', 'wall_wash'):
    old = "L = C.light('%s'" % name
    assert old in s, 'missing light %s' % name
    # find the balanced statement tail ')' of the C.light call for this light
    i = s.index(old)
    depth = 0
    j = s.index('(', i)
    k = j
    while True:
        ch = s[k]
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0:
                break
        k += 1
    stmt_end = k + 1
    insert = s[stmt_end:stmt_end]
    if 'use_shadow' not in s[stmt_end:stmt_end + 200]:
        s = s[:stmt_end] + "\n        L.data.use_shadow = False   # wide soft source: shadow map not worth it" + s[stmt_end:]
io.open(r'mv\build\stage.py', 'w', encoding='utf-8').write(s)
print('patched stage.py light shadows')
