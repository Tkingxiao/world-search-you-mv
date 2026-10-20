import os
from PIL import Image
root = r'D:\Code\Code MV\new-word.search(you)\mv\ref\art\galgame'
for fn in sorted(os.listdir(root)):
    if not fn.lower().endswith(('.webp','.png','.jpg')): continue
    p = os.path.join(root, fn)
    im = Image.open(p)
    info = f'{fn:28s} {im.size} {im.mode}'
    if im.mode in ('RGBA','LA'):
        a = im.split()[-1]
        bbox = a.getbbox()
        info += f' alpha_bbox={bbox}'
        # alpha min/max
        info += f' alpha_range={a.getextrema()}'
    print(info)
