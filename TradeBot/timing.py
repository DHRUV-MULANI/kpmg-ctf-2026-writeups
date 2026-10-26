#!/usr/bin/env python3
import time, json
from mcpclient import MCP, extract

m = MCP()
t = time.time()
r = m.tool("place_order", {"symbol": "MSFT", "quantity": 1, "order_type": "buy"})
print("place_order took %.3fs" % (time.time() - t))
print(extract(r))
print("risk:", extract(m.tool("get_risk_report")))
oid = json.loads(extract(r))["order"]["order_id"]
print("status:", extract(m.tool("get_order_status", {"order_id": oid})))

# time an intentionally rejected order
t = time.time()
r = m.tool("place_order", {"symbol": "FLAG", "quantity": 1, "order_type": "buy"})
print("FLAG order took %.3fs" % (time.time() - t))
print(extract(r))
