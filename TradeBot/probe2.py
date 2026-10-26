#!/usr/bin/env python3
import json, threading, time
from mcpclient import MCP, extract

m = MCP()

print("=== fuzz resource URIs ===")
uris = ["portfolio://status", "flag://flag", "vault://flag", "vault://status", "reserve://flag",
        "stock://FLAG", "stock://flag", "instrument://FLAG", "flags://all", "admin://flag",
        "secret://flag", "file:///flag", "file:///flag.txt", "config://flag", "tradebot://flag",
        "portfolio://flag", "portfolio://status/flag", "FLAG", "flag"]
for u in uris:
    try:
        r = m.call("resources/read", {"uri": u})
        txt = json.dumps(r)
        if "error" in txt and "not found" in txt.lower():
            continue
        print(f"  {u} -> {txt[:300]}")
    except Exception as e:
        print(f"  {u} EXC {e}")

print("\n=== observe engine phases during an order ===")
m2 = MCP()
res = {}
def do_order():
    res['r'] = m2.tool("place_order", {"symbol": "AAPL", "quantity": 1, "order_type": "buy"})
t = threading.Thread(target=do_order)
t.start()
start = time.time()
while t.is_alive():
    try:
        rr = extract(m.tool("get_risk_report"))
        print("  t=%.2f %s" % (time.time()-start, rr))
    except Exception as e:
        print("err", e)
    time.sleep(0.15)
t.join()
print("final order:", extract(res['r']))
