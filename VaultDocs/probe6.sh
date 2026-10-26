#!/bin/bash
echo "=== grep KPMG (whole fs) ==="
grep -rIa "KPMG" / --exclude-dir=proc --exclude-dir=sys --exclude-dir=dev --exclude-dir=tmp 2>/dev/null | grep -v '^Binary' | head -20
echo "=== motd.dynamic ==="
cat /run/motd.dynamic
echo "=== runit ==="
find /run/runit -maxdepth 3 2>/dev/null | head
echo "=== any file containing 'FLAG' under /etc /var /root /home ==="
grep -rIna "FLAG" /etc /var /root /home --exclude-dir=lib 2>/dev/null | head -20
echo "=== env vars (full) ==="
cat /proc/1/environ | tr '\0' '\n' | sort
echo "=== docker labels / image env hints ==="
cat /.dockerenv 2>/dev/null; strings /entrypoint.sh | head
