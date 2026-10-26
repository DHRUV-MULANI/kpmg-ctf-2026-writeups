#!/usr/bin/env python3
import json, time
from mcpclient import MCP, extract

m = MCP()
print("=== RESOURCE portfolio://status ===")
r = m.call("resources/read", {"uri": "portfolio://status"})
print(json.dumps(r, indent=2))

# Place a legit order and observe
print("\n=== PLACE BUY AAPL x1 ===")
r = m.tool("place_order", {"symbol": "AAPL", "quantity": 1, "order_type": "buy"})
print(extract(r))
print(extract(m.tool("get_portfolio")))
print(extract(m.tool("get_risk_report")))

# Try FLAG order
print("\n=== PLACE FLAG x1 ===")
r = m.tool("place_order", {"symbol": "FLAG", "quantity": 1, "order_type": "buy"})
print(extract(r))

# Try to read FLAG price during various windows
print("\n=== FLAG price ===")
print(extract(m.tool("get_stock_price", {"symbol": "FLAG"})))
