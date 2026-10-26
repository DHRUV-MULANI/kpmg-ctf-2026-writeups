#!/bin/bash
echo "===root.txt(od)==="
od -An -c /root/root.txt
echo "===ls -la /root==="
ls -la /root
echo "===/proc/1/environ==="
tr '\0' '\n' < /proc/1/environ
echo "===all env==="
env
echo "===grep KPMG_CTF in fs==="
grep -rI "KPMG_CTF" /root /home /var/www /opt /etc /tmp 2>/dev/null | head
echo "===find root/flag files==="
find / -maxdepth 4 \( -name 'root.txt' -o -name '*flag*.txt' -o -name 'flag' \) 2>/dev/null
