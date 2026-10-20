import requests, os, json
h={'User-Agent':'Mozilla/5.0'}
repo='MisakaZentai/world-search-you-dsh-pv'
base=f'https://raw.githubusercontent.com/{repo}/main/'
out=r'D:\Code\Code MV\new-word.search(you)\mv\ref\repo'
files=[
 'README.md','NOTICE.md','docs/HOW_IT_WORKS.md','docs/VERIFICATION.md','docs/PV01_ASSET_SOURCES.md',
 'film/PROJECT.yaml','film/cast.py','film/interludes.py','film/tl.py','film/subs_data.py','film/subs.py',
 'film/groups/base.py','input/README.md','data/r21.json','film/prompt_ids.json','pv_text.py','tools/lyrics.py',
 'film/beatmap.py','film/assets/character/whale-cheerful.webp','film/ui/assets/her_complete.png',
 'film/ui/assets/her_bust_108.png','film/assets/film1_egg/f1_075.600.png',
 'film/timing/beats.json','data/word_times.json','data/zh_alignment.json',
]
for rel in files:
    dst=os.path.join(out,rel.replace('/',os.sep))
    os.makedirs(os.path.dirname(dst),exist_ok=True)
    try:
        r=requests.get(base+rel,headers=h,timeout=40)
        if r.status_code==200:
            open(dst,'wb').write(r.content); print('OK',len(r.content),rel)
        else: print('FAIL',r.status_code,rel)
    except Exception as e: print('ERR',rel,repr(e))
# big files
for rel in ['film/timing/audio.json','film/cache/wave_rms_1ms.npy']:
    dst=os.path.join(out,rel.replace('/',os.sep)); os.makedirs(os.path.dirname(dst),exist_ok=True)
    try:
        r=requests.get(base+rel,headers=h,timeout=120)
        print(rel, r.status_code, len(r.content))
        if r.status_code==200: open(dst,'wb').write(r.content)
    except Exception as e: print('ERR',rel,repr(e))
