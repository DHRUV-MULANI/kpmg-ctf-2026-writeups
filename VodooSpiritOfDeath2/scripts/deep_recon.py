#!/usr/bin/env python3
"""Deep recon for a deterministic root vector."""
import sys
sys.path.insert(0, "/home/boss/Works/ctf/KPMG/VodooSpiritOfDeath2/artifacts")
from ssh_helper import connect, run

c = connect()
cmds = [
    "cat /etc/supervisor/supervisord.conf 2>&1",
    "ls -la /etc/supervisor/conf.d/ 2>&1",
    # find any supervisor socket / http server
    "ss -lntup 2>/dev/null || netstat -lntup 2>/dev/null || cat /proc/net/tcp",
    "ls -la /run/ /var/run/ 2>&1 | grep -iE 'sock|super|docker' ",
    "find / -xdev -type s 2>/dev/null",
    "ls -la /var/run/docker.sock /run/docker.sock 2>&1",
    # nginx
    "ls -laR /etc/nginx 2>&1 | head -60",
    "cat /etc/nginx/sites-enabled/* 2>/dev/null; cat /etc/nginx/conf.d/* 2>/dev/null; cat /etc/nginx/nginx.conf 2>/dev/null | tail -40",
    # root-executed hooks
    "ls -la /etc/profile.d/ /etc/update-motd.d/ 2>&1",
    # processes with open files we can influence
    "ls -la /proc/*/cwd 2>/dev/null | head; for p in $(pgrep -f 'app.py|backup|guard|entrypoint'); do echo PID $p: $(tr '\\0' ' ' </proc/$p/cmdline); done",
    # any writable files owned by root that get executed
    "find / -xdev -type f \\( -name '*.sh' -o -perm -4000 \\) -printf '%m %u %g %p\\n' 2>/dev/null | head -40",
    # env of root processes may leak
    "cat /proc/1/environ 2>&1 | tr '\\0' '\\n' | head -30",
    "cat /proc/1/cmdline 2>&1 | tr '\\0' ' '; echo; cat /entrypoint.sh 2>&1",
]
for cmd in cmds:
    run(c, cmd, timeout=60)
c.close()