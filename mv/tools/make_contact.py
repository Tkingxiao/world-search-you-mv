import os
from PIL import Image
root = r'D:\Code\Code MV\new-word.search(you)\mv\ref\art\galgame'
out = r'D:\Code\Code MV\new-word.search(you)\mv\ref\art\contact'
os.makedirs(out, exist_ok=True)
exps = ['cheerful','confused','shy','starry','serious','frightened','exasperated','angry']
cell_w, cell_h = 240, 432
sheet = Image.new('RGB', (cell_w*4, cell_h*2), (18,20,26))
for i, e in enumerate(exps):
    im = Image.open(os.path.join(root, f'whale-{e}.webp')).convert('RGBA')
    im.thumbnail((cell_w-8, cell_h-8), Image.LANCZOS)
    sheet.paste(im, ((i%4)*cell_w + (cell_w-im.width)//2, (i//4)*cell_h + (cell_h-im.height)//2), im)
sheet.save(os.path.join(out, 'expressions.png'))
print('expressions sheet', sheet.size)
# spritesheet: tile it 4x6 grid previews
sp = Image.open(os.path.join(root, 'pet-spritesheet.webp')).convert('RGBA')
prev = sp.copy(); prev.thumbnail((768, 1144), Image.LANCZOS)
bg = Image.new('RGB', prev.size, (18,20,26)); bg.paste(prev, (0,0), prev)
bg.save(os.path.join(out, 'spritesheet_preview.png'))
print('sprite preview', bg.size)
for f in ['maid-left.webp']:
    im = Image.open(os.path.join(root, f)).convert('RGBA'); im.thumbnail((500,900), Image.LANCZOS)
    bg = Image.new('RGB', im.size, (18,20,26)); bg.paste(im,(0,0),im); bg.save(os.path.join(out, f.replace('.webp','.png')))
    print(f, bg.size)
