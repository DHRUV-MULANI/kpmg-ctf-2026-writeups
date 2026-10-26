#!/usr/bin/env python3
import sys
sys.path.insert(0, "/home/boss/Works/ctf/KPMG/VodooSpiritOfDeath2/artifacts")
from ssh_helper import connect, run

c = connect()
cmds = [
    "/lib/x86_64-linux-gnu/libc.so.6 2>/dev/null | head -1; ldd --version | head -1",
    "dpkg -l | grep -E 'libc6 ' ",
    "strings -a /lib/x86_64-linux-gnu/libc.so.6 | grep -i 'libnss_' | head",
    "strings -a /lib/x86_64-linux-gnu/libc.so.6 | grep -iE '^libnss|%s\\.so' | head",
    # does sudo strip env? check version/build flags
    "sudo -V 2>&1 | grep -iE 'root-mailer|ldap|selinux|apparmor|noexec' ; echo '---'; sudo --version",
    # check whether secure paths / secure_path in sudoers (can't read, but try sudo -S -l shown before)
    "ldd --version 2>&1 | head -2",
    "dpkg -l | grep -E 'libc6 ' 2>/dev/null",
]
for cmd in cmds:
    run(c, cmd, timeout=40)
c.close()