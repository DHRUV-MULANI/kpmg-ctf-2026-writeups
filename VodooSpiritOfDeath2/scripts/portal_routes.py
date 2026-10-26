#!/usr/bin/env python3
"""Enumerate portal routes with a small wordlist, logged in as derek.ross."""
import sys
sys.path.insert(0, "/home/boss/Works/ctf/KPMG/VodooSpiritOfDeath2/artifacts")
from ssh_helper import connect, run

WORDS = """
admin api v1 api/v1 export reports report payroll settings config debug dev test
status health ping metrics logs log console jobs job queue run exec shell cmd
upload files file download static templates source src app.py routes endpoints
users user me profile account employee employees chat messages search graphql
action actions approve review generate export_csv csv backup restore sync agents
agent refresh check version license keys key auth token oauth sso invite register
""".split()

c = connect()
path = "/run/lock/routes.txt"
cmd = (
    "for p in " + " ".join(WORDS) + "; do "
    "  code=$(curl -s -m 4 -o /dev/null -w '%{http_code}' -b /run/lock/acme.cookies "
    "             http://127.0.0.1:5000/$p); "
    "  echo \"$code /$p\"; "
    "done"
)
run(c, "rm -f " + path)
run(c, cmd)
c.close()