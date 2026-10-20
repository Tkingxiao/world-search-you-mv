import json, re, os
root=r'D:\Code\Code MV\new-word.search(you)'
lrc=open(os.path.join(root,'Mili - world.search (you) ;.lrc'),encoding='utf-8').read().splitlines()
lines=[]
for ln in lrc:
    m=re.match(r'^\[(\d+):(\d+\.\d+)\]\s*(.*)$', ln.strip())
    if m:
        t=int(m.group(1))*60+float(m.group(2)); txt=m.group(3).strip()
        if txt: lines.append((t,txt))
wt=json.load(open(os.path.join(root,'mv','ref','repo','data','word_times.json'),encoding='utf-8'))['lines']
print('=== WORD_TIMES ===')
for i,w in enumerate(wt):
    print(f'{i:02d} {w["start"]:7.3f} {w["end"]:7.3f} nw={len(w["words"]):2d} sha={w["sha256"][:8]}')
print('=== LRC ===')
for i,(t,txt) in enumerate(lines):
    print(f'{i:02d} {t:7.3f} n={len(txt.split()):2d} {txt}')
