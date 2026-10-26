#!/usr/bin/env python3
"""Saturate the settlement engine and probe the vault during overlapping fills."""
import json, threading, time, sys
from mcpclient import MCP, extract

def make_sessions(n, start=0):
    sess = []
    for _ in range(n):
        sess.append(MCP())
    return sess

class Sess:
    def __init__(self):
        self.m = MCP()
    def call(self, name, args, timeout=60):
        return extract(self.m.tool(name, args, timeout=timeout))

def main():
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    print("pre-creating", N, "sessions...")
    pool = [Sess() for _ in range(N)]
    m = MCP()
    print("before portfolio:", extract(m.tool("get_portfolio")))
    print("before risk:", extract(m.tool("get_risk_report")))

    barrier = threading.Barrier(N + 1)
    outs = [None]*N
    def worker(i):
        barrier.wait()
        try:
            outs[i] = pool[i].call("place_order", {"symbol":"AAPL","quantity":1,"order_type":"buy"})
        except Exception as e:
            outs[i] = "EXC "+str(e)
    ths = [threading.Thread(target=worker, args=(i,)) for i in range(N)]
    for t in ths: t.start()
    time.sleep(0.3)
    t0 = time.time()
    barrier.wait()

    # probe during window
    probes = []
    while any(t.is_alive() for t in ths):
        try:
            rr = extract(m.tool("get_risk_report"))
            fp = extract(m.tool("get_stock_price", {"symbol":"FLAG"}))
            probes.append((time.time()-t0, rr, fp))
        except Exception as e:
            probes.append((time.time()-t0, "EXC", str(e)))
        time.sleep(0.1)
    for t in ths: t.join()
    print("elapsed %.2f" % (time.time()-t0))
    for p in probes:
        print("  t=%.2f risk=%s flagprice=%s" % p)
    print("after portfolio:", extract(m.tool("get_portfolio")))
    print("after risk:", extract(m.tool("get_risk_report")))
    nfail = sum(1 for o in outs if o and ("reject" in o.lower() or "capacity" in o.lower() or "at capacity" in o.lower()))
    print("rejected count:", nfail)
    for o in outs:
        if o and ("reject" in o.lower() or "capacity" in o.lower()):
            print("   rej:", o[:140])

if __name__ == "__main__":
    main()
