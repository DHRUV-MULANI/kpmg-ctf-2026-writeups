import requests, hashlib
requests.packages.urllib3.disable_warnings()
H="kicyber-2bccd62e5d76-granny-makes-food-0-0.chals.io"
URL=f"https://{H}/"
base=requests.get(URL, timeout=15, verify=False)
bm=hashlib.md5(base.content).hexdigest()
queries=["","debug","admin","flag","sour","pickle","challenge","competition","granny","source","best","item","user","user=granny","user=admin","user=granny&password=x","granny=1","sour=1","challenge=1","competition=1","mode=1","admin=1","flag=1","debug=1","reveal=1","find=1","secret=1","maintenance=1","env=1","help=1","?","x","x=1","giveflag=1","eat=1","food=1","recipe=1","items=1","app=1"]
for q in queries:
    try:
        r=requests.get(URL, params={q.split("=")[0]: q.split("=",1)[1] if "=" in q else ""}, timeout=12, verify=False) if "=" in q else requests.get(URL+"?"+q, timeout=12, verify=False)
        m=hashlib.md5(r.content).hexdigest()
        tag = "*** DIFF ***" if (m!=bm or r.status_code!=200 or len(r.content)!=len(base.content)) else ""
        print(f"?{q!r} {r.status_code} {len(r.content)} {tag}")
    except Exception as e:
        print(f"?{q!r} ERR {e}")
