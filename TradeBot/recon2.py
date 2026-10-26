#!/usr/bin/env python3
"""Broad recon: hidden tools, prompts, resource URI brute, error shapes."""
import json, itertools
from mcpclient import MCP, extract

m = MCP()

print("=== tools/call unknown -> error shape ===")
for name in ["nope","get_vault","read_vault","vault_read","get_flag","flag","settle","engine","debug","admin","place_order_v2","execute","run_command"]:
    try:
        r = m.tool(name, {})
        print(f"  {name}: {json.dumps(r)[:200]}")
    except Exception as e:
        print(f"  {name}: EXC {e}")

print("\n=== prompts/get guessed ===")
for name in ["flag","vault","trade","system","default","assistant","help"]:
    try:
        r = m.call("prompts/get", {"name": name, "arguments": {}})
        print(f"  {name}: {json.dumps(r)[:200]}")
    except Exception as e:
        print(f"  {name}: EXC {e}")

print("\n=== resource URI brute ===")
schemes = ["portfolio", "vault", "flag", "tradebot", "reserve", "engine", "settlement",
           "instrument", "stock", "resource", "admin", "secret", "config", "file", "trade"]
paths = ["", "flag", "status", "vault", "reserve", "note", "FLAG", "all", "list",
         "secret", "engine", "config", "portfolio", "readme", "info", "dump", "dump/flag",
         "status/flag", "vault/flag", "flag/flag", "flag.txt", "reserve_note", "root"]
seen = set()
for s in schemes:
    for p in paths:
        uri = f"{s}://{p}" if p else f"{s}://"
        if uri in seen: continue
        seen.add(uri)
        try:
            r = m.call("resources/read", {"uri": uri})
            res = r.get("result")
            if res:
                txt = json.dumps(res)
                if "not found" not in txt.lower() and "unknown" not in txt.lower():
                    print(f"  HIT {uri}: {txt[:300]}")
        except Exception:
            pass
print("  done uri brute")

print("\n=== completion/complete ===")
print(json.dumps(m.call("completion/complete", {"ref":{"type":"ref/prompt","name":"x"},"argument":{"name":"a","value":""}}))[:300])
