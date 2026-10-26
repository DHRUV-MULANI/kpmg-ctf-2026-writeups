#!/usr/bin/env python3
"""Minimal MCP over HTTP (Streamable HTTP / SSE) client for TradeBot."""
import json
import re
import sys
import requests

BASE = "https://kicyber-ec28a209729d-tradebot-0-0.chals.io"

class MCP:
    def __init__(self, base=BASE):
        self.base = base
        self.s = requests.Session()
        self.session_id = None
        self.rid = 0
        self._init()

    def _parse_sse(self, text):
        """Return list of JSON objects from an SSE body."""
        out = []
        for line in text.splitlines():
            if line.startswith("data:"):
                data = line[5:].strip()
                try:
                    out.append(json.loads(data))
                except Exception:
                    pass
        return out

    def _init(self):
        body = {
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                       "clientInfo": {"name": "c", "version": "1"}},
        }
        r = self.s.post(self.base + "/mcp", json=body, headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }, timeout=30)
        self.session_id = r.headers.get("mcp-session-id")
        # send initialized notification
        self.notify("notifications/initialized", {})

    def headers(self):
        h = {"Content-Type": "application/json",
             "Accept": "application/json, text/event-stream"}
        if self.session_id:
            h["mcp-session-id"] = self.session_id
        return h

    def notify(self, method, params):
        body = {"jsonrpc": "2.0", "method": method, "params": params}
        return self.s.post(self.base + "/mcp", json=body, headers=self.headers(), timeout=30)

    def call(self, method, params=None, timeout=30):
        self.rid += 1
        body = {"jsonrpc": "2.0", "id": self.rid, "method": method, "params": params or {}}
        r = self.s.post(self.base + "/mcp", json=body, headers=self.headers(), timeout=timeout)
        msgs = self._parse_sse(r.text)
        for m in msgs:
            if m.get("id") == self.rid:
                return m
        return {"raw": r.text, "status": r.status_code}

    def tool(self, name, args=None, timeout=60):
        return self.call("tools/call", {"name": name, "arguments": args or {}}, timeout=timeout)

    def tools_list(self):
        return self.call("tools/list", {})


def extract(resp):
    """Pull the text payload out of a tools/call result."""
    try:
        content = resp["result"]["content"]
        parts = []
        for c in content:
            parts.append(c.get("text", ""))
        return "\n".join(parts)
    except Exception:
        return json.dumps(resp)


if __name__ == "__main__":
    m = MCP()
    r = m.tools_list()
    print(json.dumps(r, indent=2))
