#!/usr/bin/env python3
import json, threading, time, requests
from mcpclient import MCP, extract, BASE

# Build a session
m = MCP()
sid = m.session_id
print("session", sid)

events = []
stop = False
def stream_reader():
    try:
        r = requests.get(BASE + "/mcp", headers={
            "Accept": "text/event-stream",
            "mcp-session-id": sid,
        }, stream=True, timeout=60)
        print("GET status", r.status_code, dict(r.headers))
        for line in r.iter_lines(decode_unicode=True):
            if stop:
                break
            if line:
                events.append(line)
    except Exception as e:
        events.append("EXC " + str(e))

th = threading.Thread(target=stream_reader, daemon=True)
th.start()
time.sleep(1)

for lvl in ["debug", "info"]:
    print("setLevel", lvl, extract(m.call("logging/setLevel", {"level": lvl})) if lvl else "")

# subscribe to resource
print("subscribe:", json.dumps(m.call("resources/subscribe", {"uri": "portfolio://status"})))

# do stuff
print("order:", extract(m.tool("place_order", {"symbol": "AAPL", "quantity": 1, "order_type": "buy"})))
print("flag price:", extract(m.tool("get_stock_price", {"symbol": "FLAG"})))
print("flag info:", extract(m.tool("get_stock_info", {"symbol": "FLAG"})))
print("risk:", extract(m.tool("get_risk_report")))
time.sleep(2)
stop = True
print("=== streamed events ===")
for e in events:
    print(e)
