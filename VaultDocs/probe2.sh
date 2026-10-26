#!/bin/bash
echo "=== grep KPMG_CTF_ full fs (excluding proc/sys/dev) ==="
grep -rIl "KPMG_CTF" / --exclude-dir=proc --exclude-dir=sys --exclude-dir=dev 2>/dev/null | head -50
echo "=== grep FLAG{ patterns ==="
grep -rInI "FLAG{" /root /home /etc /opt /srv /var /run /tmp /usr/local 2>/dev/null | head -50
echo "=== files under /root recursively ==="
find /root -type f 2>/dev/null
echo "=== /var/lib/php ==="
ls -laR /var/lib/php 2>/dev/null | head -30
echo "=== docker env files ==="
cat /proc/1/environ | tr '\0' '\n'
echo "=== mounts ==="
mount | head -30
