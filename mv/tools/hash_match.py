import json, hashlib, re
root = r'D:\Code\Code MV\new-word.search(you)'
wt = json.load(open(root + r'\mv\ref\repo\data\word_times.json', encoding='utf-8'))['lines']
lrc = open(root + r'\Mili - world.search (you) ;.lrc', encoding='utf-8').read().splitlines()
lines = []
for ln in lrc:
    m = re.match(r'^\[(\d+):(\d+\.\d+)\]\s*(.*)$', ln.strip())
    if m and m.group(3).strip():
        lines.append((int(m.group(1)) * 60 + float(m.group(2)), m.group(3).strip()))

print('wt lines', len(wt), 'lrc lines', len(lines))
PUNCT = '.,!?;:"\'()[]{}—-'
def variants(w):
    base = w.strip()
    out = [base, base.lower(), base.strip(PUNCT), base.lower().strip(PUNCT)]
    out += [re.sub(r'[^A-Za-z0-9]', '', v).lower() for v in out]
    return out

# test several lrc lines against wt lines by word-hash multiset overlap
target = {i: set(wt[i]['word_hashes']) for i in range(len(wt))}
for lid in [0, 5, 14, 20, 26, 37, 44, 54]:
    t, txt = lines[lid]
    ws = [hashlib.sha256(v.encode()).hexdigest() for w in txt.split() for v in variants(w)[:1]]
    scores = {}
    for j in range(len(wt)):
        sc = sum(1 for h in ws if h in target[j]) / max(1, len(ws))
        scores[j] = sc
    best = sorted(scores.items(), key=lambda kv: -kv[1])[:3]
    print(f'lrc {lid:02d} {t:7.3f} "{txt}" nwords={len(ws)} -> best wt', [(j, round(s, 2), wt[j]["start"]) for j, s in best])
