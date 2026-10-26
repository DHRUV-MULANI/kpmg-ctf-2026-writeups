import requests, time, concurrent.futures as cf
requests.packages.urllib3.disable_warnings()
H="kicyber-2bccd62e5d76-granny-makes-food-0-0.chals.io"
URL=f"https://{H}/"
def worker(n):
    s=requests.Session(); s.verify=False
    for _ in range(n):
        try: s.get(URL, timeout=10)
        except Exception as e: return str(e)
    return "ok"
t=time.time()
with cf.ThreadPoolExecutor(max_workers=50) as ex:
    res=list(ex.map(worker, [4]*50))
print("200 reqs in %.2fs"%(time.time()-t), set(res))
