#!/usr/bin/env python3
"""Burst >19 concurrent orders; inspect EVERY response for vault contamination."""
import json, threading, time, re, sys
from mcpclient import MCP, extract

NLEG = int(sys.argv[1]) if len(sys.argv)>1 else 30
NFLAG = 5

m = MCP()
pf = json.loads(extract(m.tool("get_portfolio")))
have = pf.get("positions",{}).get("AAPL",{}).get("shares",0)
if have < NLEG:
    print("buy", NLEG-have, extract(m.tool("place_order",{"symbol":"AAPL","quantity":NLEG-have,"order_type":"buy"},timeout=120))[:80])

N = NLEG + NFLAG
pool = []
for _ in range(N):
    for attempt in range(5):
        try:
            pool.append(MCP()); break
        except Exception as e:
            print("session init retry:", str(e)[:60]); time.sleep(2)
if len(pool) < N:
    print("only got", len(pool), "sessions"); N = len(pool); NLEG = min(NLEG, N); NFLAG = N-NLEG
barrier = threading.Barrier(N+1)
outs = [None]*N

def worker(i):
    barrier.wait()
    if i < NLEG:
        outs[i] = extract(pool[i].tool("place_order", {"symbol":"AAPL","quantity":1,"order_type":"sell"}, timeout=90))
    else:
        outs[i] = extract(pool[i].tool("place_order", {"symbol":"FLAG","quantity":1,"order_type":"buy"}, timeout=90))

mon_stop=[False]; peak=[]
def monitor():
    mm=MCP()
    while not mon_stop[0]:
        try:
            raw = extract(mm.tool("get_risk_report"))
            d=json.loads(raw)
            if d.get("settlements_inflight",0) >= 19:
                peak.append(raw)
        except Exception: pass

ths=[threading.Thread(target=worker,args=(i,)) for i in range(N)]
mon=threading.Thread(target=monitor,daemon=True)
for t in ths: t.start()
mon.start()
time.sleep(0.3)
barrier.wait()
for t in ths: t.join()
mon_stop[0]=True
time.sleep(0.3)

bad=0
for i,o in enumerate(outs):
    if o is None: continue
    if "KPMG" in (o or ""):
        print("!!! FLAG LEAK", o[:300]); bad+=1
    if i < NLEG:
        try:
            d=json.loads(o); od=d["order"]
            if od.get("symbol")!="AAPL" or not (100 < float(od.get("price",0)) < 300):
                print("!!! ANOMALOUS ORDER", o[:250]); bad+=1
        except Exception:
            print("!!! NON-JSON ORDER", o[:250]); bad+=1
    else:
        if "RESTRICTED" not in o:
            print("!!! FLAG ORDER ACCEPTED", o[:300]); bad+=1
print("anomalies:", bad)
print("peak risk samples (>=19 inflight):")
for p in set(peak):
    print("   ", p)
print("final risk:", extract(m.tool("get_risk_report")))
print("final portfolio:", extract(m.tool("get_portfolio")))
