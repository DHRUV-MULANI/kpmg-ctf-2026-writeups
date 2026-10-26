#!/usr/bin/env python3
"""Controlled saturation: many overlapping sells (>19 fills) + continuous FLAG hammer.

Hypothesis: the engine decides vault access before routing and never re-checks, so
exceeding max_concurrent_settlements breaks the "exclusive vault access" invariant,
and/or a FLAG order slips past during an active fill.
"""
import json, threading, time, sys
from mcpclient import MCP, extract

NTHREADS = int(sys.argv[1]) if len(sys.argv) > 1 else 24
DURATION = int(sys.argv[2]) if len(sys.argv) > 2 else 18

m = MCP()
# get inventory
pf = json.loads(extract(m.tool("get_portfolio")))
print("start:", pf)
need = NTHREADS * 3
have = pf.get("positions", {}).get("AAPL", {}).get("shares", 0)
if have < need:
    qty = need - have
    print("buying", qty, "AAPL:", extract(m.tool("place_order", {"symbol":"AAPL","quantity":qty,"order_type":"buy"}, timeout=120))[:120])

stop = [False]
stats = {"sell_ok":0, "sell_fail":0, "flag_hits":[], "max_inflight":0, "prices":[]}

def sell_worker(i):
    mm = MCP()
    while not stop[0]:
        try:
            r = extract(mm.tool("place_order", {"symbol":"AAPL","quantity":1,"order_type":"sell"}, timeout=60))
            if r.startswith("{"): stats["sell_ok"]+=1
            else: stats["sell_fail"]+=1
                # log unexpected
            stats.setdefault("other", []).append(r) if r.startswith("{")==False and "No position" not in r else None
        except Exception:
            stats["sell_fail"]+=1

def flag_worker():
    mm = MCP()
    while not stop[0]:
        try:
            r = extract(mm.tool("place_order", {"symbol":"FLAG","quantity":1,"order_type":"buy"}, timeout=30))
            if "RESTRICTED" not in r:
                stats["flag_hits"].append(r); print("!!! FLAG:", r)
            fp = extract(mm.tool("get_stock_price", {"symbol":"FLAG"}, timeout=30))
            if "RESTRICTED" not in fp:
                stats["flag_hits"].append(fp); print("!!! FLAGPRICE:", fp)
        except Exception:
            pass

def monitor():
    mm = MCP()
    while not stop[0]:
        try:
            rr = json.loads(extract(mm.tool("get_risk_report")))
            stats["max_inflight"] = max(stats["max_inflight"], rr.get("settlements_inflight",0))
            stats.setdefault("viol", set()).add(rr.get("integrity_violations"))
        except Exception:
            pass

ths = [threading.Thread(target=sell_worker, args=(i,), daemon=True) for i in range(NTHREADS)]
ths.append(threading.Thread(target=flag_worker, daemon=True))
ths.append(threading.Thread(target=monitor, daemon=True))
for t in ths: t.start()
time.sleep(DURATION)
stop[0] = True
time.sleep(1)
print("stats:", {k:(v if k!='other' else v[:5]) for k,v in stats.items()})
print("portfolio:", extract(m.tool("get_portfolio")))
print("risk:", extract(m.tool("get_risk_report")))
