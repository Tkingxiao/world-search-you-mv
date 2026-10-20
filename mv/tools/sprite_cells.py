import os
import numpy as np
from PIL import Image, ImageDraw
root = r'D:\Code\Code MV\new-word.search(you)\mv\ref\art\galgame'
out = r'D:\Code\Code MV\new-word.search(you)\mv\ref\art\sprite_cells'
os.makedirs(out, exist_ok=True)
im = Image.open(root + r'\pet-spritesheet.webp').convert('RGBA')
CW, CH = 192, 208
cols, rows = 8, 11
filled = []
for r in range(rows):
    for c in range(cols):
        box = (c*CW, r*CH, (c+1)*CW, (r+1)*CH)
        cell = im.crop(box)
        a = np.array(cell)[:,:,3]
        if (a>8).sum() > 100:
            filled.append((r,c))
print('filled cells', len(filled))
# contact: each cell scaled 0.55 -> 106x114, with label
sc = 0.6
cw, ch = int(CW*sc), int(CH*sc)
sheet = Image.new('RGB', (cols*cw, rows*ch), (16,18,24))
d = ImageDraw.Draw(sheet)
for (r,c) in filled:
    cell = im.crop((c*CW, r*CH, (c+1)*CW, (r+1)*CH)).resize((cw,ch), Image.LANCZOS)
    sheet.paste(cell, (c*cw, r*ch), cell)
    d.text((c*cw+4, r*ch+2), f'{r},{c}', fill=(255,120,120))
sheet.save(os.path.join(out, '_contact.png'))
print('contact', sheet.size)
# save each cell upscaled x2 for later use
for (r,c) in filled:
    cell = im.crop((c*CW, r*CH, (c+1)*CW, (r+1)*CH))
    bb = cell.split()[-1].getbbox()
    cell = cell.crop(bb)
    cell.save(os.path.join(out, f'{r}_{c}.png'))
print('saved cells')
