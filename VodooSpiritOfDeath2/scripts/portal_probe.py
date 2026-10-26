#!/usr/bin/env python3
"""Probe the root Flask portal on 127.0.0.1:5000 from inside the box."""
import sys
sys.path.insert(0, "/home/boss/Works/ctf/KPMG/VodooSpiritOfDeath2/artifacts")
from ssh_helper import connect, run

c = connect()
cmds = [
    "curl -s -m 8 -i http://127.0.0.1:5000/ | head -60",
    "curl -s -m 8 http://127.0.0.1:5000/robots.txt",
    "curl -s -m 8 -i http://127.0.0.1:5000/login",
    "curl -s -m 8 -i http://127.0.0.1:5000/static/../app.py",
    "curl -s -m 8 -i http://127.0.0.1:5000/console",
    "curl -s -m 8 -i http://127.0.0.1:5000/health",
    "curl -s -m 8 -i http://127.0.0.1:5000/api",
]
for cmd in cmds:
    run(c, cmd)
c.close()