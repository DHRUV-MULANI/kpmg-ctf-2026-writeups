#!/usr/bin/env python3
import json, threading, time, sys
from mcpclient import MCP, extract

def make_sessions(n):
    sess = []
    for _ in range(n):
        try:
            sess.append(MCP())
        except Exception as e:
            print("init err", e)
    return sess

def fire(sessions, tool, argsfn, barrier, out):
    barrier.wait()
    for i, s in enumerate(sessions):
        try:
            r = s.tool(tool, argsfn(i), timeout=60)
            out[i] = extract(r)
        except Exception as e:
            out[i] = "EXC " + str(e)

def race(tool, argsfn, n=25):
    sess = make_sessions(n)
    barrier = threading.Barrier(n + 1)
    out = [None]*n
    ths = [threading.Thread(target=fire, args=( [sess[i]], tool, lambda i=i: argsfn(i), barrier, out)) for i in range(n)]
    for t in ths: t.start()
    time.sleep(0.5)
    t0 = time.time()
    barrier.wait()
    for t in ths: t.join()
    print("elapsed %.2fs" % (time.time()-t0))
    return out

if __name__ == "__main__":
    m = MCP()
    print("before:", extract(m.tool("get_portfolio")))
    print("buy 1 AAPL:", extract(m.tool("place_order", {"symbol":"AAPL","quantity":1,"order_type":"buy"})))
    print("after buy:", extract(m.tool("get_portfolio")))
    print("=== concurrent SELL AAPL x1 ===")
    outs = race("place_order", lambda i: {"symbol":"AAPL","quantity":1,"order_type":"sell"}, n=25)
    for o in outs:
        print("  ", o[:160])
    print("after race:", extract(m.tool("get_portfolio")))
    print("risk:", extract(m.tool("get_risk_report")))
