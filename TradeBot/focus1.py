#!/usr/bin/env python3
import json, threading, time
from mcpclient import MCP, extract

m = MCP()
print("portfolio:", extract(m.tool("get_portfolio")))
print("risk:", extract(m.tool("get_risk_report")))

res = {}
def order():
    mm = MCP()
    res['o'] = extract(mm.tool("place_order", {"symbol":"AAPL","quantity":1,"order_type":"buy"}, timeout=60))

# monitor list + flag info during window
sightings = []
th = threading.Thread(target=order); th.start()
t0 = time.time()
while th.is_alive():
    try:
        lst = extract(m.tool("list_available_stocks"))
        has_flag = '"FLAG"' in lst.upper()
        fi = extract(m.tool("get_stock_info", {"symbol":"FLAG"}))
        fp = extract(m.tool("get_stock_price", {"symbol":"FLAG"}))
        rec = (round(time.time()-t0,2), has_flag, ("RESTRICTED" in fp), fi[:40])
        sightings.append(rec)
        if has_flag or "RESTRICTED" not in fp:
            print("  !! t=%s has_flag=%s flag_info=%s fp=%s" % rec, fp)
    except Exception as e:
        print("  err", e)
th.join()
print("order:", res.get('o'))
# summarize has_flag over time
print("has_flag any:", any(s[1] for s in sightings), "samples:", len(sightings))
for s in sightings[::5]:
    print("   ", s)
