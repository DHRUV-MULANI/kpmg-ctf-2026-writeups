#!/usr/bin/env python3
"""Enumerate order ids to find any order we didn't create (e.g. engine/vault orders)."""
import json, re
from mcpclient import MCP, extract

m = MCP()
our_symbols = None
seen = {}
for n in range(0, 400):
    oid = f"ORD-{n:06d}"
    r = extract(m.tool("get_order_status", {"order_id": oid}, timeout=20))
    if "Unknown order id" in r:
        continue
    try:
        d = json.loads(r)
    except Exception:
        print("  nonjson", oid, r[:120]); continue
    sym = d.get("symbol")
    seen.setdefault(sym, []).append(oid)
    if sym not in ("AAPL","MSFT","GOOGL","AMZN","TSLA","META","NVDA","JPM","V","JNJ"):
        print("  UNUSUAL", oid, r[:200])
print("symbol counts:", {k: len(v) for k,v in seen.items()})
# also try non-numeric ids
for oid in ["ORD-FLAG","ORD-REV","ORD-VAULT","ORD-000001-REV","REV-000001","VAULT-000001","ORD-1000000","ORD-999999"]:
    r = extract(m.tool("get_order_status", {"order_id": oid}))
    if "Unknown" not in r:
        print("  UNUSUAL id", oid, r[:200])
