#!/bin/bash
echo "=== all process envs containing FLAG ==="
for f in /proc/[0-9]*/environ; do
  if tr '\0' '\n' < "$f" 2>/dev/null | grep -q "FLAG"; then
    echo "--- $f ---"
    tr '\0' '\n' < "$f" 2>/dev/null | grep -i flag
  fi
done
echo "=== /run/secrets ==="
ls -la /run/secrets /var/run/secrets 2>&1 | head
echo "=== /etc/environment ==="
cat /etc/environment 2>/dev/null
echo "=== search whole fs for flag-like KPMG or FLAG{ (bytes) ==="
grep -rInIa "KPMG_CTF{" / --exclude-dir=proc --exclude-dir=sys --exclude-dir=dev --exclude-dir=usr --exclude-dir=lib 2>/dev/null | head
echo "=== /dev/shm /run contents ==="
ls -la /dev/shm /run 2>/dev/null | head -40
echo "=== bash history root ==="
cat /root/.bash_history 2>/dev/null
