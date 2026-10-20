import io

# 1) render_shot.py: allow per-shot default sample count via module attr SAMPLES
p = r'D:\Code\Code MV\new-word.search(you)\mv\build\render_shot.py'
s = io.open(p, encoding='utf-8').read()
old = "        samples = int(args.get('samples', 12))"
new = "        samples = int(args.get('samples', getattr(mod, 'SAMPLES', 12)))"
assert old in s
s = s.replace(old, new)
io.open(p, 'w', encoding='utf-8').write(s)
print('render_shot.py: per-shot SAMPLES supported')

# 2) shot_s10.py: render at 10 spp (heaviest shot in the queue)
p = r'D:\Code\Code MV\new-word.search(you)\mv\build\shot_s10.py'
s = io.open(p, encoding='utf-8').read()
old = "N = 1658\n"
assert old in s
s = s.replace(old, "N = 1658\nSAMPLES = 10  # heaviest shot in the queue: 10 spp instead of 12\n", 1)
io.open(p, 'w', encoding='utf-8').write(s)
print('shot_s10.py: SAMPLES = 10')
