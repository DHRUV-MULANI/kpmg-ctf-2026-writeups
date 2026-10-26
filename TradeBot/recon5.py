#!/usr/bin/env python3
import json, threading, time, requests
from mcpclient import MCP, extract, BASE

m = MCP()
print("=== JSON-RPC method brute ===")
methods = ["ping","logging/setLevel","resources/subscribe","resources/unsubscribe","prompts/list",
           "resources/templates/list","vault/read","engine/read","settlement/read","flag/get",
           "flag/read","admin/read","debug/read","internal/read","tools/read","order/read",
           "settle/read","vault/status","engine/status","vault/list","instruments/list",
           "market/list","stocks/list","portfolio/read","account/read","audit/read","integrity/read",
           "mcp/vault","engine","vault","read","get_flag","tools/list_all","resources/read_all"]
for meth in methods:
    try:
        r = m.call(meth, {})
        err = r.get("error")
        if err and err.get("code") == -32601:
            continue
        print(f"  {meth}: {json.dumps(r)[:200]}")
    except Exception as e:
        print(f"  {meth}: EXC {e}")
print("  done")

print("\n=== initialize with sampling/elicitation, watch server requests ===")
s = requests.Session()
body = {"jsonrpc":"2.0","id":1,"method":"initialize","params":{
    "protocolVersion":"2024-11-05",
    "capabilities":{"sampling":{},"elicitation":{},"roots":{"listChanged":True}},
    "clientInfo":{"name":"c","version":"1"}}}
r = s.post(BASE+"/mcp", json=body, headers={"Content-Type":"application/json","Accept":"application/json, text/event-stream"}, timeout=30)
sid = r.headers.get("mcp-session-id")
print("session", sid, "init resp:", r.text[:200])
s.post(BASE+"/mcp", json={"jsonrpc":"2.0","method":"notifications/initialized","params":{}},
       headers={"Content-Type":"application/json","Accept":"application/json, text/event-stream","mcp-session-id":sid}, timeout=30)

events=[]
stop=[False]
def reader():
    try:
        rr = s.get(BASE+"/mcp", headers={"Accept":"text/event-stream","mcp-session-id":sid}, stream=True, timeout=60)
        for line in rr.iter_lines(decode_unicode=True):
            if stop[0]: break
            if line: events.append(line)
    except Exception as e:
        events.append("EXC "+str(e))
th = threading.Thread(target=reader, daemon=True); th.start()
time.sleep(1)

def tcall(name, args):
    b={"jsonrpc":"2.0","id":100,"method":"tools/call","params":{"name":name,"arguments":args}}
    return s.post(BASE+"/mcp", json=b, headers={"Content-Type":"application/json","Accept":"application/json, text/event-stream","mcp-session-id":sid}, timeout=60).text

print("order:", tcall("place_order", {"symbol":"AAPL","quantity":1,"order_type":"buy"})[:200])
print("flag:", tcall("get_stock_price", {"symbol":"FLAG"})[:200])
time.sleep(2)
stop[0]=True
print("server events:", events)
