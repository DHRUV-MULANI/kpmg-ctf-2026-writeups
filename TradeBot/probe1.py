#!/usr/bin/env python3
import json
from mcpclient import MCP, extract

m = MCP()

def try_tool(name, args):
    try:
        r = m.tool(name, args)
        print(f"  {name}({json.dumps(args)}) -> {extract(r)}")
    except Exception as e:
        print(f"  {name}({json.dumps(args)}) EXC {e}")

print("=== symbol case / spaces ===")
for s in ["flag", "Flag", "FLAG ", " FLAG", "FLAG\t", "fLaG"]:
    try_tool("get_stock_info", {"symbol": s})

print("\n=== unknown symbols ===")
for s in ["ZZZZ", "BTC", "USD", "CASH", "VAULT", "RESERVE", "SECRET", "", "AAPL"]:
    try_tool("get_stock_info", {"symbol": s})

print("\n=== place_order edge cases ===")
for args in [
    {"symbol": "AAPL", "quantity": 0, "order_type": "buy"},
    {"symbol": "AAPL", "quantity": -5, "order_type": "buy"},
    {"symbol": "AAPL", "quantity": 1, "order_type": "FLAG"},
    {"symbol": "AAPL", "quantity": 1, "order_type": "buy", "extra": "x"},
    {"symbol": "flag", "quantity": 1, "order_type": "buy"},
    {"symbol": "FLAG", "quantity": 0, "order_type": "buy"},
    {"symbol": "FLAG", "quantity": -1, "order_type": "buy"},
]:
    try_tool("place_order", args)
