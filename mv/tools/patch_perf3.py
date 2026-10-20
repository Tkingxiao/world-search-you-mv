import io
p = r'mv\build\stage.py'
s = io.open(p, encoding='utf-8').read()
pairs = [
("""        C.look_at(L, (CHAR_LOC[0], CHAR_LOC[1], FLOOR + 1.0))
        L = C.light('top_shaft'""",
 """        C.look_at(L, (CHAR_LOC[0], CHAR_LOC[1], FLOOR + 1.0))
        L.data.use_shadow = False        # wide soft fill: shadow map costs more than it shows
        L = C.light('top_shaft'"""),
("""        C.look_at(L, (0.0, -11.0, FLOOR + 1.0))
        L = C.light('desk_pool'""",
 """        C.look_at(L, (0.0, -11.0, FLOOR + 1.0))
        L.data.use_shadow = False        # window spill: soft, no shadow map needed
        L = C.light('desk_pool'"""),
("""        C.look_at(L, (0.0, -21.0, FLOOR + 3.4))
    C.dust(""",
 """        C.look_at(L, (0.0, -21.0, FLOOR + 3.4))
        L.data.use_shadow = False        # wall wash: soft, no shadow map needed
    C.dust("""),
]
for old, new in pairs:
    assert old in s, 'missing %r' % old[:60]
    s = s.replace(old, new)
io.open(p, 'w', encoding='utf-8').write(s)
print('stage.py patched')
