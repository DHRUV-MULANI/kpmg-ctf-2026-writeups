#!/usr/bin/env python3
"""Inspect portal pages for parameters / injection surface (derek.ross session)."""
import sys
sys.path.insert(0, "/home/boss/Works/ctf/KPMG/VodooSpiritOfDeath2/artifacts")
from ssh_helper import connect, run

c = connect()
b = "-b /run/lock/acme.cookies"
cmds = [
    # full search results body for reflection/injection tests
    "curl -s -m 8 " + b + " 'http://127.0.0.1:5000/chat/search?q=%%7B%%7B7*7%%7D%%7D' | grep -A3 -B3 -i 'result\\|7*7\\|49' | head -40",
    "curl -s -m 8 " + b + " 'http://127.0.0.1:5000/chat/dm-derek-maya' | head -120",
    "curl -s -m 8 " + b + " 'http://127.0.0.1:5000/employees' | head -120",
    "curl -s -m 8 " + b + " 'http://127.0.0.1:5000/accounts' | head -120",
    # look for params
    "curl -s -m 8 -i " + b + " 'http://127.0.0.1:5000/employees/1' | head -12",
    "curl -s -m 8 -i " + b + " 'http://127.0.0.1:5000/chat/search?q=a' -w '\\nHTTP/%{http_code}\\n' | tail -60",
]
for cmd in cmds:
    run(c, cmd)
c.close()