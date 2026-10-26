import requests, concurrent.futures as cf, itertools
requests.packages.urllib3.disable_warnings()
IP="143.244.222.115"
HOST="kicyber-2bccd62e5d76-granny-makes-food-0-0.chals.io"
URL=f"https://{IP}/"
words="challenge competition compete cookoff bakeoff showdown battle duel fight versus vs faceoff granny grandma grannysfood grannymakesfood food foods meal meals dish dishes recipe recipes menu order orders cook bake eat cooking kitchen pantry chef cookie cookies cake bread soup pickle pickles sour sours sourdough souritem souritems sourfood signin sign_in sign-in logon authenticate auth portal dashboard home welcome index main app api v1 v2 admin private secret flag secretportal adminportal try harder number1".split()
ex=[("",),(".html",),(".php",),(".py",),(".json",),(".txt",),("/",)]
paths=set()
for w in words:
    for e in ex:
        paths.add(w+e[0])
        paths.add(w[0].upper()+w[1:]+e[0])
S=requests.Session(); S.verify=False
base=requests.get(URL,headers={"Host":HOST},timeout=15,verify=False).status_code
def t(path):
    try:
        r=requests.get(URL+f"/{path}",headers={"Host":HOST},timeout=15,verify=False)
        if r.status_code!=404:
            return ("GET",path,r.status_code,len(r.content))
    except Exception as e: return ("ERR",path,str(e)[:40])
    try:
        r=requests.post(URL+f"/{path}",headers={"Host":HOST},data="user=admin",timeout=15,verify=False)
        if r.status_code not in (404,405):
            return ("POST",path,r.status_code,len(r.content))
    except Exception as e: return ("ERR-POST",path,str(e)[:40])
    return None
outs=[]
with cf.ThreadPoolExecutor(max_workers=40) as ex:
    for r in ex.map(t,list(paths)):
        if r: outs.append(r)
print("THEMED RESULTS:", outs[:50])
print("total paths", len(paths))
