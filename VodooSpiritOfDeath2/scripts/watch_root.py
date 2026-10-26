#!/usr/bin/env python3
"""Watch for periodic root processes for ~70s, and check schedulers/init hooks."""
import sys
sys.path.insert(0, "/home/boss/Works/ctf/KPMG/VodooSpiritOfDeath2/artifacts")
from ssh_helper import connect, run

c = connect()
cmds = [
    "ls -la /etc/rc.local /etc/init.d /etc/cron* /var/spool/cron /var/spool/at* 2>&1 | head -40",
    "ls -la /home/maya.chen/scripts/ /home/maya.chen/.local/share/acme-agent/ 2>&1",
    "stat -c '%A %U %G %n' /home/maya.chen/scripts/rotate_logs.sh /home/maya.chen/logs/deploy.log 2>&1",
    # monitor root processes for ~70s
    "rm -f /run/lock/pslog; for i in $(seq 1 70); do "
    "ps -eo user,pid,ppid,args --no-headers 2>/dev/null | grep -vE 'sshd|ps -eo|grep -vE|seq 1 70' "
    ">> /run/lock/pslog; sleep 1; done; "
    "echo '--- unique-ish (user,cmd) seen ---'; "
    "awk '{print $1, $4, $5, $6}' /run/lock/pslog | sort | uniq -c | sort -rn | head -40",
]
for cmd in cmds:
    run(c, cmd, timeout=120)
c.close()