#!/usr/bin/env python3
"""Race several legit symbols together and check each order response for contamination."""
import json, threading, time, re
from mcpclient import MCP, extract

REQ = [("AAPL", "buy"), ("MSFT", "buy"), ("GOOGL", "buy"), ("TSLA", "buy"), ("FLAG", "buy")]

def main(rounds=10):
    m = MCP()
    pool = [MCP() for _ in range(len(REQ))]
    anomalies = []
    for r in range(rounds):
        barrier = threading.Barrier(len(REQ) + 1)
        outs = [None]*len(REQ)
        def worker(i):
            barrier.wait()
            sym, typ = REQ[i]
            try:
                outs[i] = extract(pool[i].tool("place_order", {"symbol":sym,"quantity":1,"order_type":typ}, timeout=60))
            except Exception as e:
                outs[i] = "EXC "+str(e)
        ths = [threading.Thread(target=worker, args=(i,)) for i in range(len(REQ))]
        for t in ths: t.start()
        time.sleep(0.3)
        barrier.wait()
        for t in ths: t.join()
        for i, o in enumerate(outs):
            req_sym = REQ[i][0]
            print(f"r{r} req={req_sym:6s} -> {(o or '')[:170]}")
            if o and o.strip().startswith("{"):
                try:
                    d = json.loads(o)
                    od = d.get("order", {})
                    if od.get("symbol") != req_sym:
                        anomalies.append((req_sym, o)); print("   *** SYMBOL MISMATCH", o)
                except Exception as e:
                    print("   parse err", e)
            if o and ("KPMG" in o):
                anomalies.append((req_sym, o)); print("   *** FLAG LEAK", o)
    print("anomalies:", len(anomalies))
    print("portfolio:", extract(m.tool("get_portfolio")))

if __name__ == "__main__":
    main()
