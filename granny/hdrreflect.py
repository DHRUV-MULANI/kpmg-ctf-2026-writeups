import requests
requests.packages.urllib3.disable_warnings()
H="kicyber-2bccd62e5d76-granny-makes-food-0-0.chals.io"
URL=f"https://{H}/"
marker="MARKER9Z7Q"
hdrs=["User-Agent","Referer","X-Forwarded-For","X-Real-IP","X-Forwarded-Host","Accept-Language","Cookie","Origin","X-Custom","X-Api-Key","Authorization","X-Requested-With","Forwarded","True-Client-IP","CF-Connecting-IP","X-Original-URL","X-Rewrite-URL","Host"]
for h in hdrs:
    try:
        if h=="Host":
            r=requests.get(URL, headers={"Host":marker}, timeout=10, verify=False)
        else:
            r=requests.get(URL, headers={h:marker}, timeout=10, verify=False)
        hit = marker in r.text
        print(f"{h:22} status={r.status_code} len={len(r.content)} reflected={hit}")
        if hit:
            i=r.text.find(marker); print("   ...",r.text[max(0,i-60):i+60].replace("\n"," "))
    except Exception as e:
        print(h,"ERR",str(e)[:80])
# SSTI in host and query
for h in ["Host"]:
    r=requests.get(URL, headers={h:"{{7*7}}"}, timeout=10, verify=False)
    print(h,"ssti 49:", "49" in r.text, len(r.content))
print("DONE")
