#!/usr/bin/env python3
import sys
sys.path.insert(0, "/home/boss/Works/ctf/KPMG/VodooSpiritOfDeath2/artifacts")
from ssh_helper import connect, run

c = connect()
cmds = [
    "ls -laR /var/lib/acme 2>&1",
    "cat /var/lib/acme/.maya-home-baseline.list 2>&1 | head",
    "ls -la /var/log/ 2>&1",
    "cat /var/log/portal.log 2>&1 | head -40",
    "cat /var/log/portal.err 2>&1 | head -40",
    "cat /var/log/acme-fs-guard.log 2>&1 | tail -20",
    "cat /var/log/supervisor/* 2>&1 | tail -40",
    "ls -la / 2>&1",
    "find / -xdev -iname '*hax*' -o -xdev -iname '*samedit*' -o -xdev -iname '*spoiler*' -o -xdev -iname '*hint*' 2>/dev/null | head",
]
for cmd in cmds:
    run(c, cmd, timeout=60)
c.close()