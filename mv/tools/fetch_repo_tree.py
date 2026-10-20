import requests, json, os
h={'User-Agent':'Mozilla/5.0','Accept':'application/vnd.github+json'}
out=r'D:\Code\Code MV\new-word.search(you)\mv\ref'
repo='MisakaZentai/world-search-you-dsh-pv'
r=requests.get(f'https://api.github.com/repos/{repo}/git/trees/main?recursive=1',headers=h,timeout=40)
print(r.status_code)
tree=r.json().get('tree',[])
print('files',len(tree))
open(os.path.join(out,'repo_full_tree.json'),'w',encoding='utf-8').write(json.dumps(tree,ensure_ascii=False,indent=1))
for it in tree:
    if it['type']=='blob':
        print(it.get('size'), it['path'])
