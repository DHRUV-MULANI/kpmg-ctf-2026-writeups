import requests, concurrent.futures as cf
requests.packages.urllib3.disable_warnings()
HOST="kicyber-2bccd62e5d76-granny-makes-food-0-0.chals.io"
URL=f"https://{HOST}/"
words=("login Login LOGIN LogIn login2 signin signup register sign-up sign_up create account accounts user users admin admin2 "
"challenge competition compete cookoff bakeoff showdown battle duel fight versus faceoff granny grandma grannyfood grannysfood grannymakesfood "
"food foods meal meals dish dishes recipe recipes menu order orders cook bake eat cooking kitchen pantry chef cookie cookies cake bread soup "
"pickle pickles sour sours sourdough souritem souritems sourfood sourcream vinegar kimchi ferment fermented lemon lemons grannysmith apple apples "
"portal portal2 gate gateway door vault restrict restricted secret secretadmin adminportal "
"index home main app api v1 v2 v3 flag flag.txt getflag readflag privesc debug console trace logs source src app.py wsgi.py requirements.txt config conf env .env .git static assets flag_admin"
"welcom welcome submit verify auth authenticate session token jwt apiAuth api_login api-login apilogin webhook webhooks callback cb data query search q searchpage interface portal").split()
SE={"","Login.html","/","login.html","Login.html","php","py","jsp","asp","aspx","json",".txt"}
sess=requests.Session(); sess.verify=False
seen=set()
paths=[]
for w in words:
    for suffix in SE:
        p=w+suffix
        k=p.lower()
        if k in seen: continue
        seen.add(k)
        paths.append(p.lstrip("/"))
def t(p):
    out=[]
    try:
        r=sess.get(URL+p, timeout=12)
        if r.status_code!=404: out.append(("G",p,r.status_code,len(r.content)))
    except Exception as e: out.append(("GE",p,str(e)[:60]))
    try:
        r=sess.post(URL+p, data="user=admin", timeout=12)
        if r.status_code not in (404,): out.append(("P",p,r.status_code,len(r.content),r.headers.get("Location","")))
    except Exception as e: out.append(("PE",p,str(e)[:60]))
    return out
results=[]
with cf.ThreadPoolExecutor(max_workers=30) as ex:
    for r in ex.map(t, paths):
        results += r
for r in results: print(r)
print("THEMED2 DONE total paths:",len(paths))
