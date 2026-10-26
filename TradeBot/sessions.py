#!/usr/bin/env python3
import json
from mcpclient import MCP, extract

def mk():
    return MCP()

a = mk()
b = mk()
print("A portfolio:", extract(a.tool("get_portfolio")))
print("B portfolio:", extract(b.tool("get_portfolio")))
a.tool("place_order", {"symbol": "AAPL", "quantity": 1, "order_type": "buy"})
print("A after buy:", extract(a.tool("get_portfolio")))
print("B portfolio:", extract(b.tool("get_portfolio")))
print("A risk:", extract(a.tool("get_risk_report")))
print("B risk:", extract(b.tool("get_risk_report")))
# order id namespace shared?
r = a.tool("place_order", {"symbol": "AAPL", "quantity": 1, "order_type": "buy"})
oid = json.loads(extract(r))["order"]["order_id"]
print("A order id:", oid)
print("B status of A order:", extract(b.tool("get_order_status", {"order_id": oid})))
