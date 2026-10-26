import requests, concurrent.futures as cf
requests.packages.urllib3.disable_warnings()
H="kicyber-2bccd62e5d76-granny-makes-food-0-0.chals.io"
URL=f"https://{H}/"
dirs=["static","assets","js","css","img","images","fonts","media","files","public","uploads","download","src","lib","vendor","script","scripts"]
files=["app.js","main.js","index.js","config.js","config.json","settings.js","script.js","common.js","style.css","main.css","app.css","style.css.map","app.js.map","logo.png","favicon.ico","robots.txt","flag.txt","data.json","users.json","package.json","requirements.txt","app.py","source.py","README.md","info.json","config","conf","env",".env","admin.js","login.js","api.js","bundle.js","granny.js","food.js","sour.js","pickle.js","api.py","server.py","wsgi.py","gemfile","procfile","dockerfile"]
paths=[]
for d in dirs:
    for f in files:
        paths.append(f"{d}/{f}")
        paths.append(f"{d}")
def t(p):
    try:
        r=requests.get(URL+p, timeout=15, verify=False)
        if r.status_code!=404:
            return (p, r.status_code, len(r.content))
    except Exception as e:
        return (p,"ERR",str(e)[:40])
    return None
outs=[]
with cf.ThreadPoolExecutor(max_workers=40) as ex:
    for r in ex.map(t,paths):
        if r: outs.append(r)
for o in outs: print(o)
print("STATIC DONE", len(outs))
