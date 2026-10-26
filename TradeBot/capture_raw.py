#!/usr/bin/env python3
"""Capture raw SSE bodies for every call; advertise sampling/elicitation/roots."""
import json, requests
from mcpclient import BASE

s = requests.Session()
H = {"Content-Type":"application/json","Accept":"application/json, text/event-stream"}

init = {"jsonrpc":"2.0","id":1,"method":"initialize","params":{
    "protocolVersion":"2025-06-18",
    "capabilities":{"sampling":{},"elicitation":{},"roots":{"listChanged":True},
                    "experimental":{}},
    "clientInfo":{"name":"c","version":"1"}}}
r = s.post(BASE+"/mcp", json=init, headers=H, timeout=30)
sid = r.headers.get("mcp-session-id")
print("== INIT raw ==\n", r.text)
H2 = dict(H); H2["mcp-session-id"]=sid
s.post(BASE+"/mcp", json={"jsonrpc":"2.0","method":"notifications/initialized","params":{}}, headers=H2, timeout=30)

def call(method, params, label):
    body = {"jsonrpc":"2.0","id":2,"method":method,"params":params}
    rr = s.post(BASE+"/mcp", json=body, headers=H2, timeout=60)
    print(f"\n== {label} raw (status {rr.status_code}) ==\n{rr.text}")

call("tools/call", {"name":"place_order","arguments":{"symbol":"AAPL","quantity":1,"order_type":"buy"}}, "place_order AAPL")
call("tools/call", {"name":"get_stock_price","arguments":{"symbol":"FLAG"}}, "get_stock_price FLAG")
call("tools/call", {"name":"place_order","arguments":{"symbol":"FLAG","quantity":1,"order_type":"buy"}}, "place_order FLAG")
call("resources/read", {"uri":"portfolio://status"}, "resource portfolio")
