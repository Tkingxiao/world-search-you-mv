import os, urllib.request, json
PROXY = 'http://127.0.0.1:7890'
opener = urllib.request.build_opener(urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY}))
opener.addheaders = [('User-Agent','dsh-mv/1.0')]
root = r'D:\Code\Code MV\new-word.search(you)\mv\ref\art'
files = {
 'galgame': ['assets/default/whale-angry.webp','assets/default/whale-cheerful.webp','assets/default/whale-confused.webp',
             'assets/default/whale-exasperated.webp','assets/default/whale-frightened.webp','assets/default/whale-serious.webp',
             'assets/default/whale-shy.webp','assets/default/whale-starry.webp','assets/default/pet-spritesheet.webp',
             'assets/default/maid-left.webp','assets/default/palace-night.webp','assets/default/bg-deepseek-seaside-study.webp',
             'assets/default/README.md','assets/default/licenses/dsh-deep-whale-NOTICE.txt','NOTICE.md'],
}
for sub, paths in files.items():
    os.makedirs(os.path.join(root, sub), exist_ok=True)
for repo, sub in [('JAdpp/dsh-whale-galgame','galgame')]:
    for p in files[sub]:
        url = f'https://raw.githubusercontent.com/{repo}/main/{p}'
        dst = os.path.join(root, sub, os.path.basename(p))
        try:
            data = opener.open(url, timeout=120).read()
            open(dst,'wb').write(data)
            print('ok', dst, len(data))
        except Exception as e:
            print('FAIL', p, repr(e))
