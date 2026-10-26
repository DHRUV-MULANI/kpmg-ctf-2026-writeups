#!/usr/bin/env python3
"""Poll get_order_status for an in-flight (routing/fill) order using the predicted id."""
import json, threading, time, re
from mcpclient import MCP, extract

m = MCP()
# establish counter
r = extract(m.tool("place_order", {"symbol":"AAPL","quantity":1,"order_type":"buy"}, timeout=60))
print("seed order:", r)
n = int(json.loads(r)["order"]["order_id"].split("-")[1])
next_id = f"ORD-{n+1:06d}"
print("predicting next id:", next_id)

res = {}
def order():
    mm = MCP()
    res['o'] = extract(mm.tool("place_order", {"symbol":"MSFT","quantity":1,"order_type":"buy"}, timeout=60))

th = threading.Thread(target=order); th.start()
time.sleep(0.6)  # let order be created (~routing)
seen = {}
t0 = time.time()
while th.is_alive():
    try:
        rr = extract(m.tool("get_order_status", {"order_id": next_id}, timeout=20))
    except Exception as e:
        rr = "EXC "+str(e)
    if rr not in seen:
        seen[rr] = round(time.time()-t0, 2)
    time.sleep(0.03)
th.join()
print("order result:", res.get('o'))
for k,v in seen.items():
    print(f"  t={v} -> {k[:250]}")
