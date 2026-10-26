#!/usr/bin/env python3
"""Login to portal as derek.ross and enumerate authenticated routes."""
import sys
sys.path.insert(0, "/home/boss/Works/ctf/KPMG/VodooSpiritOfDeath2/artifacts")
from ssh_helper import connect, run

c = connect()
cmds = [
    "curl -s -m 8 -c /run/lock/acme.cookies -b /run/lock/acme.cookies "
    "-X POST http://127.0.0.1:5000/login -d 'username=derek.ross&password=DerekOps%232026' "
    "-i | head -20",
    "curl -s -m 8 -b /run/lock/acme.cookies http://127.0.0.1:5000/dashboard | head -80",
    "curl -s -m 8 -b /run/lock/acme.cookies http://127.0.0.1:5000/chat | head -100",
    "curl -s -m 8 -b /run/lock/acme.cookies 'http://127.0.0.1:5000/chat/search?q=test' | head -40",
    "curl -s -m 8 -b /run/lock/acme.cookies http://127.0.0.1:5000/employees | head -40",
    "curl -s -m 8 -b /run/lock/acme.cookies http://127.0.0.1:5000/accounts | head -40",
]
for cmd in cmds:
    run(c, cmd)
c.close()