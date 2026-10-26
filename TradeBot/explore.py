#!/usr/bin/env python3
import json
from mcpclient import MCP, extract

m = MCP()
print("=== TOOLS ===")
r = m.tools_list()
for t in r["result"]["tools"]:
    print(t["name"], "|", t.get("description"))
    print("   schema:", json.dumps(t["inputSchema"].get("properties", {})))

print("\n=== PROMPTS ===")
print(json.dumps(m.call("prompts/list", {}), indent=2))

print("\n=== RESOURCES ===")
print(json.dumps(m.call("resources/list", {}), indent=2))

print("\n=== RESOURCE TEMPLATES ===")
print(json.dumps(m.call("resources/templates/list", {}), indent=2))

print("\n=== PUBLIC STOCKS ===")
print(extract(m.tool("list_available_stocks")))

print("\n=== RISK REPORT ===")
print(extract(m.tool("get_risk_report")))

print("\n=== PORTFOLIO ===")
print(extract(m.tool("get_portfolio")))

print("\n=== FLAG INFO ===")
print(extract(m.tool("get_stock_info", {"symbol": "FLAG"})))

print("\n=== HEALTH ===")
print(extract(m.tool("health_check")))
