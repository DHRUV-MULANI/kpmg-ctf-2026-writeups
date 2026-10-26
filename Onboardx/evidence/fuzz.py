import requests, sys, concurrent.futures, urllib3
urllib3.disable_warnings()
base="https://kicyber-00f338d978e5-onboardx-0-0.chals.io"
tok=None
for line in open("/tmp/opencode/cj.txt"):
    if line.startswith("#"): continue
    p=line.split()
    if len(p)>=7 and p[5]=="token": tok=p[6]
cookies={"token": tok}

def probe(w):
    p = "/"+w if not w.startswith("/") else w
    try:
        r=requests.get(base+p, cookies=cookies, timeout=8, allow_redirects=False, verify=False)
        return p, r.status_code, len(r.content)
    except Exception as e:
        return p, "ERR", str(e)[:40]

words=[l.strip() for l in open(sys.argv[1]) if l.strip() and not l.startswith("#")]
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=24) as ex:
    for p,c,s in ex.map(probe, words, chunksize=1):
        if c != 404 and not (c==302):
            print(f"{c} [{s}] {p}", flush=True)
print("DONE")