"""cam_path: add a living handheld drift automatically (all shots inherit)."""
import io
import py_compile

P = r'D:\Code\Code MV\new-word.search(you)\mv\build\shotkit.py'
s = io.open(P, encoding='utf-8').read()
if 'add_handheld(' not in s:
    raise SystemExit('add_handheld missing')

# 1) append drift at the end of cam_path (before its return cam)
old = "    return cam\n"
cnt = s.count(old)
print('return cam occurrences:', cnt)
if cnt != 1:
    raise SystemExit('expected exactly one "return cam"')
new = ("    try:\n"
       "        add_handheld(cam, amp=0.0075, scale=1.9, seed=abs(hash(name)) % 997)\n"
       "    except Exception as _e:\n"
       "        print('handheld failed: %r' % (_e,), flush=True)\n"
       "    return cam\n")
s = s.replace(old, new, 1)
io.open(P, 'w', encoding='utf-8').write(s)
py_compile.compile(P, doraise=True)
print('[ok] cam_path now applies handheld drift')
