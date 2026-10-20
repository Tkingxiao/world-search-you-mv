import requests, json, os, sys
h={'User-Agent':'Mozilla/5.0','Accept':'application/vnd.github+json'}
out=r'D:\Code\Code MV\new-word.search(you)\mv\ref'
repo='MisakaZentai/world-search-you-dsh-pv'
def get(url):
    r=requests.get(url,headers=h,timeout=30); print(url, r.status_code, len(r.content)); return r
r=get(f'https://api.github.com/repos/{repo}/contents')
if r.status_code==200:
    items=r.json()
    with open(os.path.join(out,'repo_tree.json'),'w',encoding='utf-8') as f: json.dump(items,f,ensure_ascii=False,indent=1)
    for it in items: print(it['type'], it['size'], it['path'])
r2=get(f'https://raw.githubusercontent.com/{repo}/main/README.md')
if r2.status_code==200:
    open(os.path.join(out,'repo_README.md'),'w',encoding='utf-8').write(r2.text)
    print('README saved', len(r2.text))
