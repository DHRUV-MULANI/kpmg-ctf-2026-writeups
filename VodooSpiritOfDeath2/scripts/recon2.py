#!/usr/bin/env python3
import sys
sys.path.insert(0, "/home/boss/Works/ctf/KPMG/VodooSpiritOfDeath2/artifacts")
from ssh_helper import connect, run

c = connect()
cmds = [
    "cat /entrypoint.sh 2>&1",
    "cat /etc/supervisor/conf.d/supervisord.conf 2>&1",
    "cat /usr/local/bin/acme-fs-guard.sh 2>&1",
    "ls -la /opt/portal/ 2>&1; ls -la /opt/ 2>&1",
    "cat /home/maya.chen/.local/share/acme-agent/.vault/user.txt 2>&1",
    "cat /home/maya.chen/Documents/meeting-notes.txt 2>&1",
    "cat /home/maya.chen/logs/deploy.log 2>&1",
    "cat /home/maya.chen/.config/acme-cli/config.json 2>&1",
    "cat /home/maya.chen/scripts/rotate_logs.sh 2>&1",
    "cat /home/maya.chen/backups/2025-legacy/export.csv 2>&1",
    "ls -la /var/lib/acme/ 2>&1; ls -la /root 2>&1",
    "ls -lR /etc/sudoers.d 2>&1; cat /etc/sudoers 2>&1 | tail -30",
    "find / -iname '*flag*' -o -iname '*root.txt*' 2>/dev/null | head -40",
    "ls -la /usr/bin/ | grep -iE 'gcc|cc|clang|make|perl|python|nc|socat|tar|base64' 2>&1",
    "cat /home/maya.chen/.cache/acme-portal/session.tmp 2>&1",
]
for cmd in cmds:
    run(c, cmd)
c.close()
