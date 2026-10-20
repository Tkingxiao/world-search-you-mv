import json, os, urllib.request, sys
PROXY = 'http://127.0.0.1:7890'
opener = urllib.request.build_opener(urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY}))
opener.addheaders = [('User-Agent','dsh-mv/1.0')]
def get(url):
    with opener.open(url, timeout=60) as r:
        return r.read()
def tree(repo):
    out = {}
    try:
        data = json.loads(get(f'https://api.github.com/repos/{repo}/git/trees/HEAD?recursive=1'))
        out['tree'] = [(e['path'], e['size'] if 'size' in e else 0) for e in data.get('tree',[]) if e['type']=='blob']
        out['truncated'] = data.get('truncated')
    except Exception as e:
        out['error'] = repr(e)
    return out
for repo in ['Small-tailqwq/dsh-deep-whale','JAdpp/dsh-whale-galgame']:
    t = tree(repo)
    print('==', repo, 'error' if 'error' in t else len(t['tree']))
    if 'tree' in t:
        for p,s in t['tree']:
            if any(p.lower().endswith(x) for x in ('.png','.webp','.jpg','.md','.txt','.svg')):
                print(f'{s:9d} {p}')
    json.dump(t, open(os.path.join(r'D:\Code\Code MV\new-word.search(you)\mv\ref', repo.split('/')[1]+'_tree.json'),'w',encoding='utf-8'), ensure_ascii=False, indent=1)
