#!/bin/bash
echo "=== ls /var/lib/docker ==="
ls -la /var/lib/docker 2>&1 | head
echo "=== find container configs ==="
find /var/lib/docker/containers -maxdepth 2 -name 'config.v2.json' 2>/dev/null | head
echo "=== grep ROOT_FLAG in docker metadata ==="
grep -rIl "ROOT_FLAG" /var/lib/docker 2>/dev/null | head
echo "=== grep KPMG_CTF in docker ==="
grep -rIl "KPMG_CTF" /var/lib/docker 2>/dev/null | head
echo "=== hostname config ==="
cat /etc/hostname
