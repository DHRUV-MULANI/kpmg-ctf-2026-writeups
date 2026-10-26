import requests, concurrent.futures as cf
requests.packages.urllib3.disable_warnings()
IP="143.244.222.115"
URL="https://kicyber-2bccd62e5d76-granny-makes-food-0-0.chals.io/"
names="localhost 127.0.0.1 admin administrator internal intranet private secure admin.local localhost.localdomain granny grandma granny.local food food.local sour sour.local sourdough kitchen portal portal.local backend app api web server host docker container granny-makes-food granny-makes-food.local kicyber chals.io admin.granny.local app.local web.local api.local backend.local internal.local admin.kicyber.local".split()
def t(n):
    for path in ["/login","/"]:
        try:
            r=requests.get("https://"+n+path, headers={"Host":n}, timeout=10, verify=False)
        except Exception as e:
            return (n,path,"ERR",str(e)[:40])
        if r.status_code!=404 and not (r.status_code==200 and len(r.content)==1481):
            return (n,path,r.status_code,len(r.content))
    return None
with cf.ThreadPoolExecutor(max_workers=20) as ex:
    for r in ex.map(t,names):
        if r: print("VHOST-DIFF",r)
print("VHOST DONE")
