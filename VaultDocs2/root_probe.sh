#!/bin/sh
echo "===ID==="
id
echo "===HOSTNAME==="
hostname
echo "===ROOTFLAG==="
cat /root/root.txt
echo "===USERFLAG==="
cat /home/vboxuser/user.txt
echo "===ENV_PID1==="
tr '\0' '\n' < /proc/1/environ
echo "===ENTRYPOINT==="
cat /entrypoint.sh 2>/dev/null
echo "===ROOTLS==="
ls -la /root/
echo "===SEARCH_FLAGS==="
grep -rIl "KPMG_CTF{" /root /home /opt /srv /var/backups /tmp 2>/dev/null
echo "===DONE==="
