#!/usr/bin/env python3
import json, threading, time, sys
from mcpclient import MCP, extract

FLAG_MARK = "KPMG"

def run_race(symbol="AAPL", n_flag=40, delay_start=0.8):
    res = {}
    def order_thread():
        mm = MCP()
        res['order'] = mm.tool("place_order", {"symbol": symbol, "quantity": 1, "order_type": "buy"}, timeout=60)
    t = threading.Thread(target=order_thread)
    t.start()
    time.sleep(delay_start)
    # spam FLAG requests during routing/fill
    results = []
    for i in range(n_flag):
        try:
            mm = MCP()
            r = mm.tool("place_order", {"symbol": "FLAG", "quantity": 1, "order_type": "buy"}, timeout=30)
            txt = extract(r)
            results.append(txt)
            if FLAG_MARK in txt:
                print("!!! FLAG LEAK in place_order:", txt)
        except Exception as e:
            results.append("EXC " + str(e))
        time.sleep(0.02)
    t.join()
    print("order result:", extract(res.get('order', {})))
    uniq = set(results)
    for u in uniq:
        print("  flag-resp:", u[:200], "(x%d)" % results.count(u))
    return results

if __name__ == "__main__":
    for it in range(3):
        print("===== iteration", it, "=====")
        run_race()
