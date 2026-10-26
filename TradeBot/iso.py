#!/usr/bin/env python3
import json, time
from mcpclient import MCP, extract

C = MCP()
print("C id", C.session_id)
print("C portfolio:", extract(C.tool("get_portfolio")))
D = MCP()
print("D id", D.session_id)
print("D portfolio:", extract(D.tool("get_portfolio")))
print("C portfolio again:", extract(C.tool("get_portfolio")))
print("C buy AAPL:", extract(C.tool("place_order", {"symbol":"AAPL","quantity":1,"order_type":"buy"})))
print("C portfolio:", extract(C.tool("get_portfolio")))
print("D portfolio:", extract(D.tool("get_portfolio")))
print("risk:", extract(C.tool("get_risk_report")))
