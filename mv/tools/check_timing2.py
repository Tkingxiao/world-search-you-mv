import json, re, os
root=r'D:\Code\Code MV\new-word.search(you)'
lrc=open(os.path.join(root,'Mili - world.search (you) ;.lrc'),encoding='utf-8').read().splitlines()
lines=[]
for ln in lrc:
    m=re.match(r'^\[(\d+):(\d+\.\d+)\]\s*(.*)$', ln.strip())
    if m:
        t=int(m.group(1))*60+float(m.group(2)); txt=m.group(3).strip()
        if txt: lines.append((t,txt))
print('lrc lyric lines:',len(lines))
wt=json.load(open(os.path.join(root,'mv','ref','repo','data','word_times.json'),encoding='utf-8'))['lines']
print('word lines:',len(wt))
bad=0
for i,(t,txt) in enumerate(lines):
    n=len(txt.split())
    w=wt[i] if i<len(wt) else None
    if w is None or abs(t-w['start'])>0.35 or len(w['words'])!=n:
        bad+=1
        print(f'MISMATCH {i}: lrc {t:.3f} "/{txt}/" n={n} | wt {w["start"] if w else None:.3f} nw={len(w["words"]) if w else None}')
print('mismatches',bad)
# print section map
for i,(t,txt) in enumerate(lines):
    print(f'{i:02d} {t:7.3f} {len(txt.split()):2d} {txt}')
