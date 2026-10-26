import requests, concurrent.futures as cf, itertools
requests.packages.urllib3.disable_warnings()
H="kicyber-2bccd62e5d76-granny-makes-food-0-0.chals.io"
URL=f"https://{H}/"
methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS","HEAD"]
paths=["","login","flag","flag.txt","auth","admin","dashboard","portal","user","users","settings","account","menu","order","sour","souritem","pickle","api","api/login","api/v1","source","app.py","debug","console","%2e","static","health","granny","food","home","index","verify","submit","secret","private","internal","config","env"]
def t(args):
    m,p=args
    try:
        r=requests.request(m, URL+p, data="user=admin", timeout=15, verify=False)
        skip = (m=="HEAD")
        if skip: return None
        if r.status_code not in (404,405,200) or (p=="" and r.status_code==200):
            return (m,p,r.status_code,len(r.content))
        if p!="" and r.status_code==200:
            return (m,p,r.status_code,len(r.content))
    except Exception as e:
        return (m,p,"ERR",str(e)[:50])
    return None
tasks=[(m,p) for m in methods for p in paths]
outs=[]
with cf.ThreadPoolExecutor(max_workers=40) as ex:
    for r in ex.map(t,tasks):
        if r: outs.append(r)
for o in outs: print(o)
print("MATRIX DONE", len(outs))
