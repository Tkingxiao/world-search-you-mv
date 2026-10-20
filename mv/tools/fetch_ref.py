import requests, re, sys, json, os
h={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36',
   'Accept-Language':'zh-CN,zh;q=0.9,en;q=0.8'}
out=r'D:\Code\Code MV\new-word.search(you)\mv\ref'
os.makedirs(out, exist_ok=True)
targets=[('migeci','https://www.migeci.com/geci/4291548.html'),
         ('namu','https://namu.wiki/w/world.search(you)%3B'),
         ('namu2','https://m.namu.moe/w/world.search(you)%3B'),
         ('hue_suruga','https://www.suruga-ya.com/zh-hans/product/220225266'),
         ('mili_site','https://mili.jp/')]
for name,url in targets:
    try:
        r=requests.get(url,headers=h,timeout=30)
        print(name, r.status_code, len(r.text), r.url)
        with open(os.path.join(out,name+'.html'),'w',encoding='utf-8') as f:
            f.write(r.text)
    except Exception as e:
        print(name,'ERR',repr(e))
