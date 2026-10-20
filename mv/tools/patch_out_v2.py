"""Point v2 burn output at a separate file so the v1 fallback is never overwritten."""
import io
import py_compile

P = r'D:\Code\Code MV\new-word.search(you)\mv\tools\final_encode.py'
s = io.open(P, encoding='utf-8').read()
old = "OUT = os.path.join(FINAL, 'world.search(you)_final.mp4')"
new = "OUT = os.path.join(FINAL, 'world.search(you)_final_v2.mp4')"
assert old in s
s = s.replace(old, new, 1)
io.open(P, 'w', encoding='utf-8').write(s)
py_compile.compile(P, doraise=True)
print('[ok] OUT -> world.search(you)_final_v2.mp4')
