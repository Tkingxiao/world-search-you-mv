"""Set all v2 shots to 10 samples (speed) and start the scheduled render tasks."""
import io
import re
import os

MV = r'D:\Code\Code MV\new-word.search(you)'

for f in ('shot_s05.py', 'shot_s07.py', 'shot_s08.py'):
    p = os.path.join(MV, 'mv', 'build', f)
    s = io.open(p, encoding='utf-8').read()
    s = re.sub(r'^SAMPLES = 16.*$', 'SAMPLES = 10', s, count=1, flags=re.M)
    io.open(p, 'w', encoding='utf-8').write(s)
    print('[samples] %s -> 10' % f)

p = os.path.join(MV, 'mv', 'build', 'render_shot.py')
s = io.open(p, encoding='utf-8').read()
old = "getattr(mod, 'SAMPLES', 12)"
if old in s:
    s = s.replace(old, "getattr(mod, 'SAMPLES', 10)")
    io.open(p, 'w', encoding='utf-8').write(s)
    print('[samples] render_shot default -> 10')
else:
    print('[samples] render_shot default already patched')
