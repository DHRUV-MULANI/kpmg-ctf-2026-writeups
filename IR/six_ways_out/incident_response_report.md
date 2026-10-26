# Incident Response Forensic Report: "Six Ways Out"

## 1. Executive Summary
During a simulated security incident on production host `prod-web-03` (`10.0.1.15`), unauthorized activity resulted in the compromise and network exfiltration of multiple sensitive files. Through correlation of endpoint audit telemetry (`audit.log`, `bash_history.txt`) with full packet capture analysis (`exfiltration.pcap`), six distinct outbound exfiltration channels were identified and analyzed.

Each exfiltrated channel contained a fragment of the final verification key. This report documents the forensic methodology, network and host artifacts, command execution traces, and reproduction commands used to recover all six fragments.

---

## 2. Evidence Overview

| Evidence Source | Location / Name | Description |
|---|---|---|
| Network Packet Capture | `network/exfiltration.pcap` | Full packet capture containing outbound network streams |
| Network Connection Log | `network/conn.log` | Zeek/Bro style connection summary of traffic flows |
| Host Audit Telemetry | `endpoint/audit.log` | Linux auditd records documenting `execve` execution calls |
| Command History | `endpoint/bash_history.txt` | Terminal history recovered from the host |
| Host Logs | `endpoint/syslog.log`, `endpoint/auth.log` | Authentication and system operational events |

---

## 3. Host Artifact Correlation

Cross-referencing `endpoint/bash_history.txt` and `endpoint/audit.log` revealed key parameters, staging commands, and cryptographic keys used prior to exfiltration:

1. **Staging Directory:** `/tmp/.s/` was created to hold intermediate artifacts.
2. **Key Material Identified:**
   - `KEY1`: Base64 `bWFuZ28tNDc=` &rarr; `mango-47`
   - `KEY4`: Base64 `cmF2ZW4tMTk=` &rarr; `raven-19`
   - `KEY6`: Base64 `U3Rvcm0tV2luZC0yMDI2` &rarr; `Storm-Wind-2026`

---

## 4. Detailed Channel Analysis & Flag Extraction

### Channel 1: HTTP POST (`production.env`)

- **Destination:** `198.244.146.163:80` (`/api/update`)
- **Transport:** HTTP POST (Frame 525, TCP Stream 26)
- **Data Encoding / Transformation:** Base32 + XOR with key `mango-47`
- **Source Artifact:** `/opt/app/config/production.env`

#### Extraction Method
The HTTP POST body from frame 525 contained the raw string:
```text
FQYT4OBBNR4XEUAIAAJQUX22KYAUYHQGCZAFCWIZJQHROBRAHZZS6PRGFA6HSCKTB5GB4FIAJENF4AYVBMKQCTCYHJTSKLBYHJ7HCZKQAAPBOMC6KFCRWCANAJRCO4DVGIYS6NB4PJ5WKKK4E4VQAW2RPQ6SYKJYDJNECFTANMVSSOLEMZ4CGLBLFE5RARCFAICRWBA3IRNVSYDLMNWWEJ3EOY7TKMKWKJ6AGXC7BQRBO
```

Decoding with Base32, followed by XOR using key `mango-47`:
```python
import base64

raw_b32 = "FQYT4OBBNR4XEUAIAAJQUX22KYAUYHQGCZAFCWIZJQHROBRAHZZS6PRGFA6HSCKTB5GB4FIAJENF4AYVBMKQCTCYHJTSKLBYHJ7HCZKQAAPBOMC6KFCRWCANAJRCO4DVGIYS6NB4PJ5WKKK4E4VQAW2RPQ6SYKJYDJNECFTANMVSSOLEMZ4CGLBLFE5RARCFAICRWBA3IRNVSYDLMNWWEJ3EOY7TKMKWKJ6AGXC7BQRBO"
rem = len(raw_b32) % 8
if rem:
    raw_b32 += "=" * (8 - rem)
dec = base64.b32decode(raw_b32)
key = b"mango-47"
plaintext = bytes(b ^ key[i % len(key)] for i, b in enumerate(dec)).decode()
print(plaintext)
```

#### Recovered Content
```text
APP_NAME=internal-payment-api
DB_HOST=db-prod.internal
DB_USER=app_service
DB_PASSWORD=ILoveKPMG_uwu!
ENVIRONMENT=production

PART_1=Q7k2mLp
```

**Recovered Fragment 1:** `Q7k2mLp`

---

### Channel 2: DNS Tunneling (`employee_records.csv`)

- **Destination Resolver / Nameserver:** `66.132.172.130:53`
- **Domain:** `npmjs-registry.net`
- **Transport:** DNS Queries (Frames 554 through 588)
- **Data Encoding / Transformation:** Base32 subdomain labels
- **Source Artifact:** `/opt/hr/employee_records.csv`

#### Extraction Method
Filtering for non-standard DNS query names directed at `npmjs-registry.net` yielded 14 consecutive subdomain labels:
```text
MVWXA3DPPFSWKX3JMQEW4YLNMUEWIZ
LQMFZHI3LFNZ2AS4TFNVQXE23TBUFE
KTKQGAYDCCKENF3GC4YJIRSXMT3QOM
EU4ZLFMRZSA5DPEBRGKIDQOJXW233U
MVSA2CSFJVIDAMBSBFHGC3TEMEEUG6
LCMVZFGZLDOVZGS5DZBFHGKZLEOMQH
I3ZAMJSSA4DSN5WW65DFMQGQURKNKA
YDAMYJKZUXG2DBNQEUQ5LNMFXCAUTF
ONXXK4TDMUEU4ZLFMRZSA5DPEBRGKI
DEMVWW65DFMQGQURKNKAYDANAJKNUG
S5TBBFDGS3TBNZRWKCKPNYQE433UNF
RWKICQMVZGS33EBUFEKTKQGAYDKCKW
MFZHK3QJKNHUGCKQIFJFIXZSHIQGWO
JRLB3DEULBBUFA
```

Concatenating these labels and decoding from Base32:
```python
import base64

labels = [
    "MVWXA3DPPFSWKX3JMQEW4YLNMUEWIZ",
    "LQMFZHI3LFNZ2AS4TFNVQXE23TBUFE",
    "KTKQGAYDCCKENF3GC4YJIRSXMT3QOM",
    "EU4ZLFMRZSA5DPEBRGKIDQOJXW233U",
    "MVSA2CSFJVIDAMBSBFHGC3TEMEEUG6",
    "LCMVZFGZLDOVZGS5DZBFHGKZLEOMQH",
    "I3ZAMJSSA4DSN5WW65DFMQGQURKNKA",
    "YDAMYJKZUXG2DBNQEUQ5LNMFXCAUTF",
    "ONXXK4TDMUEU4ZLFMRZSA5DPEBRGKI",
    "DEMVWW65DFMQGQURKNKAYDANAJKNUG",
    "S5TBBFDGS3TBNZRWKCKPNYQE433UNF",
    "RWKICQMVZGS33EBUFEKTKQGAYDKCKW",
    "MFZHK3QJKNHUGCKQIFJFIXZSHIQGWO",
    "JRLB3DEULBBUFA"
]
b32 = "".join(labels)
if len(b32) % 8:
    b32 += "=" * (8 - len(b32) % 8)
print(base64.b32decode(b32).decode())
```

#### Recovered Content
```text
employee_id	name	department	remarks
EMP001	Divas	DevOps	Needs to be promoted
EMP002	Nanda	CyberSecurity	Needs to be promoted
EMP003	Vishal	Human Resource	Needs to be demoted
EMP004	Shiva	Finance	On Notice Period
EMP005	Varun	SOC	PART_2: k91Xv2Qa
```

**Recovered Fragment 2:** `k91Xv2Qa`

---

### Channel 3: SMTP Email Attachments (`p3_src.dat`)

- **Destination:** `20.122.142.214:25`
- **Recipient:** `finance.archive@external.example`
- **Transport:** SMTP (TCP Stream 28)
- **Data Encoding / Transformation:** Multipart MIME with Base64-encoded PNG QR codes
- **Source Artifact:** `/tmp/.s/p3_src.dat` (rendered via `gen_qr.py`)

#### Extraction Method
Inspecting TCP stream 28 revealed an SMTP session delivering three PNG attachments: `q3_recon_0001.png`, `q3_recon_0002.png`, and `q3_recon_0003.png`.

Extracting the image bytes from the MIME stream and processing via `zbarimg`:
```bash
zbarimg qr_1.png qr_2.png qr_3.png
```

#### Recovered Content
```text
QR-Code:PART_3A: Hnc
QR-Code:PART_3B: fuEY
QR-Code:PART_3C: 92kL
```

Concatenating parts 3A, 3B, and 3C:
`Hnc` + `fuEY` + `92kL` = `HncfuEY92kL`

**Recovered Fragment 3:** `HncfuEY92kL`

---

### Channel 4: ICMP Echo Request (`data.dump`)

- **Destination:** `221.162.63.50`
- **Transport:** ICMP Echo Requests (Type 8, Sequence numbers 1–20)
- **Data Encoding / Transformation:** Hex encoding + XOR with key `raven-19`
- **Source Artifact:** `/var/backups/data.dump`

#### Extraction Method
Extracting data fields across the 20 ICMP echo requests sent to `221.162.63.50`:
```python
import subprocess

cmd = [
    "tshark", "-r", "network/exfiltration.pcap",
    "-Y", "icmp.type == 8 && ip.dst == 221.162.63.50",
    "-T", "fields", "-e", "data.data"
]
hex_chunks = subprocess.check_output(cmd, text=True).split()
raw = bytes.fromhex("".join(hex_chunks))
key = b"raven-19"
dec = bytes(b ^ key[i % len(key)] for i, b in enumerate(raw))
print(dec.decode(errors="replace"))
```

#### Recovered Content
```text
-- PostgreSQL database dump
-- Database: customer_portal

CREATE TABLE settings (
id integer,
name varchar(64),
value text
);

INSERT INTO settings VALUES
(1, 'timezone', 'UTC'),
(2, 'maintenance_mode', 'false'),
(3, 'backup_status', 'enabled');

-- Internal challenge metadata
INSERT INTO settings VALUES
(4, 'PART_4', 'xP83LmQa');

-- PostgreSQL database dump complete
```

**Recovered Fragment 4:** `xP83LmQa`

---

### Channel 5: FTP Transfer (`q3_forecast.xlsx`)

- **Destination:** `198.244.146.163:21`
- **Filename:** `daily_metrics.dat`
- **Transport:** FTP-DATA (TCP Stream 31)
- **Data Encoding / Transformation:** 7-Zip Gzip archive (`.gz`) + Base64
- **Source Artifact:** `/opt/finance/q3_forecast.xlsx`

#### Extraction Method
Stream 31 contains the Base64 representation of a gzip archive. Following TCP Stream 31, base64-decoding the stream content, and decompressing with gzip reconstructed `recovered_q3.xlsx`:
```python
import base64, gzip, zipfile

with open("recovered_q3.xlsx", "wb") as f:
    f.write(gzip.decompress(base64.b64decode(b64_stream_data)))

z = zipfile.ZipFile("recovered_q3.xlsx")
print(z.read("xl/worksheets/sheet2.xml").decode())
```

Inspection of `xl/worksheets/sheet2.xml` and `xl/sharedStrings.xml` showed row 8:
- Cell `B8`: Shared string index 41 (`PART_5`)
- Cell `C8`: Shared string index 21 (`7vQm91Xe`)

**Recovered Fragment 5:** `7vQm91Xe`

---

### Channel 6: WebSocket Channel (`release-notes.txt`)

- **Destination:** `66.132.172.130:8080` (`/ws/metrics`)
- **Transport:** WebSocket Binary Frames (Frame 766, TCP Stream 33)
- **Data Encoding / Transformation:** OpenSSL AES-256-CBC (`pass:Storm-Wind-2026`, `-md sha256`, salted) + Base64
- **Source Artifact:** `/srv/app/releases/release-notes.txt`

#### Extraction Method
Frame 766 carries the WebSocket payload starting with ASCII `U2FsdGVk...` (Base64 for OpenSSL magic `Salted__`).

Base64-decoding and decrypting:
```bash
echo -n "U2FsdGVkX198CEy3QJsm2MTDJ9b4TvznV90hHbhevd3UTqOxp3SzA...=" | base64 -d > r.enc
openssl enc -d -aes-256-cbc -salt -md sha256 -pass "pass:Storm-Wind-2026" -in r.enc
```

#### Recovered Content
```text
Release Notes
=============

Version 4.7.2

- Improved database connection handling
- Updated authentication middleware
- Fixed logging issue
- Updated deployment documentation

Internal release reference:
PART_6: Lm92Qx7P
```

**Recovered Fragment 6:** `Lm92Qx7P`

---

## 5. Reconstruction of the Complete Flag

All fragments extracted in sequential order:

| Fragment Index | Extraction Source | Value |
|:---:|:---|:---|
| Part 1 | HTTP POST | `Q7k2mLp` |
| Part 2 | DNS Tunneling | `k91Xv2Qa` |
| Part 3 | SMTP QR Codes | `HncfuEY92kL` |
| Part 4 | ICMP Echo Data | `xP83LmQa` |
| Part 5 | FTP Spreadsheet | `7vQm91Xe` |
| Part 6 | WebSocket Encrypted Frame | `Lm92Qx7P` |

### Final Flag:
```text
KPMG_CTF{Q7k2mLpk91Xv2QaHncfuEY92kLxP83LmQa7vQm91XeLm92Qx7P}
```
