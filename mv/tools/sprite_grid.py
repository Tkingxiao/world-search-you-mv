import numpy as np
from PIL import Image
root = r'D:\Code\Code MV\new-word.search(you)\mv\ref\art\galgame'
im = Image.open(root + r'\pet-spritesheet.webp').convert('RGBA')
a = np.array(im)[:,:,3] > 8
H, W = a.shape
col = a.sum(axis=0); row = a.sum(axis=1)
def gaps(v, thresh=0):
    g=[]; s=None
    for i,x in enumerate(v):
        if x<=thresh and s is None: s=i
        elif x>thresh and s is not None: g.append((s,i-1)); s=None
    if s is not None: g.append((s,len(v)-1))
    return [x for x in g if x[1]-x[0]>=4]
cg = gaps(col); rg = gaps(row)
print('W,H', W, H)
print('col gaps', cg[:20])
print('row gaps', rg[:30])
# segment cells by gutters
def bounds(g, n):
    b=[0]
    for s,e in g: b += [s, e+1]
    b += [n]
    b=sorted(set(b))
    # merge: intervals between gutters
    segs=[]
    for i in range(0,len(b)-1,2):
        segs.append((b[i], b[i+1]-1))
    return segs
print('col segs', bounds(cg, W))
print('row segs', bounds(rg, H))
