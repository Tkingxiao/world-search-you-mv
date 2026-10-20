import json, re, os
root=r'D:\Code\Code MV\new-word.search(you)'
lrc=open(os.path.join(root,'Mili - world.search (you) ;.lrc'),encoding='utf-8').read().splitlines()
lines=[]
for ln in lrc:
    m=re.match(r'^\[(\d+):(\d+\.\d+)\]\s*(.*)$', ln.strip())
    if m:
        t=int(m.group(1))*60+float(m.group(2))
        txt=m.group(3).strip()
        lines.append((t,txt))
print('lrc timed lines:',len(lines))
for i,(t,txt) in enumerate(lines[:5]): print(i,round(t,3),repr(txt))
wt=json.load(open(os.path.join(root,'mv','ref','repo','data','word_times.json'),encoding='utf-8'))
wl=wt['lines']
print('word_times lines:',len(wl))
# compare starts
for i in range(min(len(lines),len(wl))):
    if i<8 or abs(lines[i][0]-wl[i]['start'])>0.2:
        print(i,'lrc',round(lines[i][0],3),'wt',round(wl[i]['start'],3),'nwords',len(wl[i]['words']), repr(lines[i][1])[:60])
print('last lines:')
for i in range(len(lines)-4,len(lines)):
    print(i,round(lines[i][0],3),repr(lines[i][1])[:80], '| wt:',round(wl[i]['start'],3),len(wl[i]['words']) if i<len(wl) else None)
print('duration',wt['duration'],'wt count',len(wl),'lrc count',len(lines))
