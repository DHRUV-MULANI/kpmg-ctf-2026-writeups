#!/usr/bin/env python3
import sys
sys.path.insert(0, "/home/boss/Works/ctf/KPMG/VodooSpiritOfDeath2/artifacts")
from ssh_helper import connect, run

c = connect()
cmds = [
    "id; hostname; cat /etc/os-release | head -4",
    "sudo --version 2>&1 | head -4; dpkg -l | grep -i sudo",
    "ls -la /home/; ls -la /home/maya.chen/",
    "find /home/maya.chen -type f 2>/dev/null | head -60",
    "uname -a; ls -l /usr/bin/sudo; ls -l /usr/bin/sudoedit",
    "ls -la /tmp /var/tmp /dev/shm /run/lock 2>&1",
    "sudo -l 2>&1 | head -20",
    "find / -perm -4000 -type f 2>/dev/null",
    "getcap -r / 2>/dev/null",
    "cat /etc/crontab 2>/dev/null; ls -la /etc/cron.d 2>/dev/null; crontab -l 2>&1",
    "cat /etc/passwd",
    "env",
    "ps auxww",
]
for cmd in cmds:
    run(c, cmd)
c.close()
