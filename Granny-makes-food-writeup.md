# KPMG CTF 2026 — "Granny makes food" — Full Investigation Writeup

> **Challenge:** Granny makes food (Web)
> **Points:** 20
> **CTFd Challenge ID:** 23
> **Category:** Web
> **Type:** `application_target` (dynamic deploy via the CTFd *application_target* plugin)
> **Target:** `https://kicyber-2bccd62e5d76-granny-makes-food-0-0.chals.io`
> **Flag format:** `KPMG_CTF{...}`
> **CTF window:** ended 2026-10-11 09:59 (site now returns *"KPMG Capture the Flag (CTF) 2026 Campus Edition has ended"*)
> **Final status:** ❌ **UNSOLVED — flag not recovered.**
>
> This document is an **honest, complete evidence dump** of everything that was tried, together with raw outputs, so the work can be picked up again if the challenge is ever re-deployed.

---

## 0. TL;DR

- The instance exposed **exactly one working route: `GET /`** → a 1481-byte static HTML login portal.
- The portal's form has `action="/login"` `method="POST"` and a single `user` field, **but `/login` (GET and POST) returns a Werkzeug router-level `404`.** The route genuinely does not exist on the running deployment.
- Despite exhaustive enumeration (**full `raft-medium-words.txt` = 0 non-404 results**, ~1300 themed paths, API paths, traversal, method fuzzing, header/vhost fuzzing, path-normalisation/misrouting tricks, cookies, pickle-deserialisation probes, request-smuggling basics, port/DNS/SNI enumeration) **no additional route or behaviour was ever exposed.**
- The description *"She makes the best sour items"* is a **perfect 9-letter anagram of `misroutes`** (`s-o-u-r-i-t-e-m-s` ⇄ `m-i-s-r-o-u-t-e-s`), strongly suggesting the intended theme is **routing confusion / HTTP request smuggling**. Every misrouting/smuggling variant tested against this deployment failed.
- Conclusion: the deployment appears **broken/incomplete** (only `GET /` registered) — or the intended mechanism required a technique that this deploy did not expose. Details and reasoning in §9.

---

## 1. Challenge Metadata (CTFd)

| Field | Value |
|---|---|
| id | 23 |
| name | Granny makes food |
| value | 20 |
| category | Web |
| type | application_target |
| description | Do you want to challenge Granny to a food competition? She makes the best sour items. |
| files | *(none)* |
| hints | *(none)* |
| connection_info | `https://kicyber-2bccd62e5d76-granny-makes-food-0-0.chals.io` |

API queried (with the CTFd session cookie extracted from the local browser):

```
GET https://kicyber.ctfd.io/api/v1/challenges/23
Cookie: session=<value>
```

After the CTF closed the API returns:

```json
{"message": "KPMG Capture the Flag (CTF) 2026 Campus Edition has ended"}
```

Deploy/destroy is handled by the `application_target` CTFd plugin:

- **Destroy:** `POST /services/destroy?challenge_id=23`
- **Launch:** called from JS `window.challenge.launch()` (endpoint captured from
  `/plugins/application_target/assets/view.js`).

> Relaunching a fresh instance was considered as a last resort (to rule out a
> one-off broken container) but was **not attempted**, to avoid destroying the only
> live instance while it was still being probed.

---

## 2. Target Fingerprint

### 2.1 DNS

| Name | Result |
|---|---|
| `kicyber-2bccd62e5d76-granny-makes-food-0-0.chals.io` | `143.244.222.115` |
| `*.chals.io` | wildcard → `143.244.222.116` |
| Nameservers | `terry.ns.cloudflare.com`, `tia.ns.cloudflare.com` |
| TXT / CNAME / MX | no challenge-relevant records found |

The two IPs are DigitalOcean. The "real" host resolves to `.115`; the wildcard
falls back to `.116`.

Trying to hit the real SNI against the *other* IP, and sibling hostnames
(`...-0-1`, `...-1-0`, `kicyber-2bccd62e5d76.chals.io`, `kicyber.chals.io`) all
return TLS handshake failure (`000`) — they are **not routed**.

### 2.2 Ports

Full TCP scan of both `143.244.222.115` and `143.244.222.116`:

```
PORT     STATE SERVICE
23/tcp   open  telnet
80/tcp   open  http      (openresty/1.27.1.2 → 301 to https)
443/tcp  open  https     (Werkzeug/3.1.3 Python/3.10.18)
8443/tcp open  https-alt (accepts TLS for the real SNI, returns nothing)
```

Re-verified with a quick top-50 scan:

```
$ nmap -Pn --top-ports 50 --open -T4 143.244.222.115
PORT     STATE SERVICE
23/tcp   open  telnet
80/tcp   open  http
443/tcp  open  https
8443/tcp open  https-alt
```

- **Port 80** — `openresty/1.27.1.2`, always `301 Moved Permanently` →
  `https://<host>/<path>` (173-byte nginx 301 page). No path was served directly.
- **Port 443** — the actual app, `Server: Werkzeug/3.1.3 Python/3.10.18`,
  `Connection: close` on every response.
- **Port 8443** — TLS handshake succeeds for the real SNI but **every path returns
  an empty response** (`000`, 0 bytes).
- **Port 23** — a TCP "router" that replies literally:
  `Host: Couldn't find underlying service` for every name tried
  (`granny`, `granny-makes-food`, `admin`, `grandma`, …).

### 2.3 Edge routing

The platform edge routes by **TLS SNI**. Only the exact hostname
`kicyber-2bccd62e5d76-granny-makes-food-0-0.chals.io` is routed to the app;
all other SNI values fail the handshake. This is consistent with the platform
fronting each challenge as a raw TCP/TLS pipe to the containerised Werkzeug app.

---

## 3. Application Analysis — the only route, `GET /`

### 3.1 Response

```
$ curl -sik https://<host>/
HTTP/1.1 200 OK
Server: Werkzeug/3.1.3 Python/3.10.18
Date: Sun, 11 Oct 2026 04:39:56 GMT
Content-Type: text/html
Content-Length: 1481
Connection: close
```

Body (saved verbatim as `granny/root.html`, `md5 = aeed43fa3f6d69213d71a18cdc3a8624`):

```html
<!DOCTYPE html>
<html>
<head>
    <title>Welcome to the Portal</title>
    <style>
        body {
            background-color: #1e1e2f;
            color: #e0e0e0;
            font-family: Arial, sans-serif;
            text-align: center;
            padding-top: 100px;
        }
        h1 {
            font-size: 2.5em;
            color: #80cbc4;
        }
        .container {
            background-color: #2e2e3f;
            padding: 30px;
            margin: auto;
            width: 40%;
            border-radius: 15px;
            box-shadow: 0px 0px 15px #000;
        }
        input[type=text] {
            padding: 10px;
            width: 80%;
            margin: 10px 0;
            border-radius: 5px;
            border: 1px solid #ccc;
        }
        input[type=submit] {
            padding: 10px 20px;
            background-color: #80cbc4;
            border: none;
            color: #000;
            font-weight: bold;
            cursor: pointer;
            border-radius: 5px;
        }
        input[type=submit]:hover {
            background-color: #4db6ac;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>The Access Portal that no one can access</h1>
        <form action="/login" method="POST">
            <input type="text" name="user" placeholder="Enter username"><br>
            <input type="submit" value="Login">
        </form>
        <p>Access restricted. Admins only.</p>
    </div>
</body>
</html>
```

### 3.2 Key observations

- **Title:** `Welcome to the Portal`
- **H1:** `The Access Portal that no one can access`
- **Form:** `POST` to `/login`, single text input `name="user"`
- **Footer:** `Access restricted. Admins only.`
- **No** JavaScript, **no** linked CSS/JS assets, **no** comments, **no** hidden
  inputs, **no** cookie is ever set anywhere in the app.

### 3.3 Methods on `/`

| Method | Result |
|---|---|
| `GET /` | `200`, 1481 bytes |
| `HEAD /` | `200`, no body |
| `OPTIONS /` | `200`, `Allow: OPTIONS, GET, HEAD`, `Content-Length: 0` |
| `POST /` | `405 METHOD NOT ALLOWED`, `Allow: OPTIONS, GET, HEAD` |
| `TRACE /` | `405 METHOD NOT ALLOWED` |
| `PUT/DELETE/PATCH /` | `405` |

`/` is registered with **explicit `methods=["GET"]`** (hence POST → 405), so the
login logic cannot live on `/`.

### 3.4 The missing `/login`

```
$ curl -sik https://<host>/login
HTTP/1.1 404 NOT FOUND
Server: Werkzeug/3.1.3 Python/3.10.18
Content-Type: text/html; charset=utf-8
Content-Length: 207
Connection: close
```

The Werkzeug **default 404 page is exactly 207 bytes**:

- Every unknown path returns this identical 207-byte body.
- Every known-but-wrong-method situation returns a 405 with the specific
  `Allow` header (verified on `/`).
- Since `POST /login` returns **404 (not 405)**, the `/login` route is **not
  registered at all** on this deployment — it is not a method mismatch.

This mismatch — *the only page the user can see points at `/login`, yet
`/login` does not exist* — is the central anomaly of this deployment.

---

## 4. Enumeration — complete matrix of what was tested

### 4.1 Directory / route fuzzing (ffuf)

| Wordlist | Command | Results |
|---|---|---|
| `common.txt` | `ffuf … -mc all -fc 404` | **0** (`granny/ffuf_common.json`) |
| `raft-medium-directories.txt` | `ffuf … -mc all -fc 404` | **0** (`granny/ffuf_raft.json`) |
| `raft-medium-words.txt` | `ffuf … -mc all -fc 404` | **0** (`granny/ffuf_words_full.json`) |

A full `raft-medium-words.txt` scan (`ffuf_words_full.json`) returned **zero
non-404 responses** — i.e. *nothing but `GET /` exists*.

Additionally ~1300 hand-crafted/themed paths were probed
(API-style `/api/login`, `/api/user`, DB/deserialize names, food/kitchen words,
`/admin`, `/flag`, `/grandma`, `/secret`, `/recipe`, `/menu`, `/portal`, …) plus
trailing-slash and case variants — all **404/207**.

> Because the ancestor challenge's denial page returns HTTP 200 (not 404), a
> wordlist scan *would* have surfaced any such guarded route. It found none.

Artifacts: `granny/ffuf_common.json`, `granny/ffuf_raft.json`,
`granny/ffuf_words.json`, `granny/ffuf_words_full.json`.

### 4.2 Path-normalisation / "misroute" tricks (`granny/misroute.py`)

Probed `/login/`, `/login;/`, `/login;x`, `/login%2f`, `/login%00`, `/login%0a`,
`/login./`, `/./login`, `/login/.`, `/login/..`, `/login/../`, `/login/..;/`,
`/log%69n`, `/%6cogin`, `/LOGIN`, `/Login`, `//login`, `///login`, `/;/login`,
`/%2flogin`, `/%2e%2e/login`, `/..%2flogin`, `/login%2e`, `/login%20`,
`/login/;`, `/login\\`, `/.//login`, `/%252flogin`, plus themed routes with a
trailing slash. **Result: no route was ever reached.** The only non-404s were
`//`, `/%2e%2e/`, `/login/..` — all of which simply **normalise to `/`** and
return the 1481-byte portal.

### 4.3 Header-based routing / override (`granny/misroute.py`, `vhost*.sh`)

| Header (on `GET /`) | Result |
|---|---|
| `X-Original-URL: /login` | `200 / 1481` (portal, no effect) |
| `X-Rewrite-URL: /login` | `200 / 1481` |
| `X-Forwarded-Prefix: /login` | `200 / 1481` |
| `X-Original-URI: /login` | `200 / 1481` |
| `X-Forwarded-Uri: /login` | `200 / 1481` |
| `X-Override-URL: /login` | `200 / 1481` |
| `X-HTTP-Method-Override: POST` | `200 / 1481` |
| `X-Method-Override: POST` | `200 / 1481` |
| `X-Forwarded-Host: localhost` / `127.0.0.1` | `200 / 1481` |

A `Host:` header vhost fuzz (with correct SNI) across ~100 candidate virtual
hosts also produced **no difference** (`granny/vhost.py`, `granny/vhost2.sh`).

### 4.4 Parameters (`granny/refl.py`, `granny/hdrreflect.py`, `granny/boolq.py`)

- 60+ query parameters on `/` tested for reflection and logic changes.
- ~30 custom request headers tested for reflection.
- Boolean/logic probes (e.g. `?admin=true`, `?debug=1`) — no effect.

**No parameter or header ever changed the response** or set a cookie.

### 4.5 Cookies (`granny/cookietest.py`, `granny/cookiefuzz.py`, `granny/ckbrute.py`)

- Many cookie names (`session`, `user`, `admin`, `role`, `auth`, `token`,
  `logged_in`, `pickle`, `flag`, `sour`, …) and values.
- **Forged role/checksum cookies** (see §6) for `grandma`, `granny`, `admin`,
  `chef`, `kitchen helper`, `root`, … with and without
  `checksum = md5(role)` — **no effect**.
- ~1,100 cookie combinations brute-forced (`ckbrute.py`) → **0 hits**.

### 4.6 Pickle / deserialisation probes

Because *"sour items"* could point at **pickles**, extensive pickle-injection
was attempted (`granny/pickleprobe.py`, `granny/pickletime.py`,
`granny/bodypickle.py`, `granny/bigsleep.py`):

- Base64 + raw + urlsafe-base64 pickle payloads whose `__reduce__` calls
  `time.sleep(8/15)` — injected via **cookies, query params, and POST bodies**
  to `/` and `/login`.
- Payload classes: `pickle.loads`, `eval`, `os.system`, reverse-shell shells.

**Result:** no deserialisation occurred (timings were pure network jitter;
no response-size or status change anywhere). The `user` field never reaches a
handler, because `/login` does not exist.

### 4.7 Werkzeug debugger / source disclosure

| Attempt | Result |
|---|---|
| `/console` | `404` |
| `/__debugger__` | `404` |
| `/?__debugger__=yes&cmd=resource&f=debugger.js` | `200` but returns the portal (debugger not enabled) |
| `/static/app.py`, `/app.py`, `.env`, `../`, source files | `404` |

Source-disclosure fuzzing (`granny/srcfuzz.py`, `granny/staticfuzz.py`) found
nothing.

### 4.8 HTTP request smuggling (basic)

CL.TE / TE.CL / TE.TE and dual-`Content-Length` / obfuscated
`Transfer-Encoding` variants were attempted against 443 (raw sockets) in an
effort to reach a backend route that the front could not — **no smuggled
response, no differential timing, no backend route reached.**

### 4.9 Other techniques

- **WebSocket upgrade / `CONNECT`** — no effect.
- **HTTP Basic auth** — no effect.
- **Absolute-URI request targets** (proxy-style `GET http://host/login HTTP/1.1`)
  — no effect.
- **`//`, dot-segment, `%2e` normalisation** — collapse to `/` (portal).
- **Sibling services** — `…-0-1`, `…-1-0`, `kicyber-2bccd62e5d76.chals.io`,
  `kicyber.chals.io` → not routed (TLS `000`).
- **Port 8443** — empty responses for `/`, `/login`, `/flag`.
- **Port 23 router** — `Host: Couldn't find underlying service` for all names.

---

## 5. Primary Hypothesis — "sour items" = "misroutes"

```
sour items  →  s o u r i t e m s
misroutes   →  m i s r o u t e s
```

Two natural readings of the description:

1. **"sour items" = "pickles"** → Python pickle deserialisation on the `user`
   field posted to `/login`. (Tested; endpoint absent.)
2. **"sour items" = anagram of `misroutes`** → the challenge theme is
   **routing confusion / HTTP request smuggling** — which fits the tagline
   *"The Access Portal that no one can access"* (i.e. you must *misroute* a
   request to reach the inaccessible portal/admin).

The exact 9-letter anagram is almost certainly deliberate, so the intended bug
was almost certainly a **misrouting class bug** (path confusion, proxy
normalisation mismatch, or request smuggling). Against *this* deployment every
variant of that class failed because there was no second route/backend to reach.

---

## 6. Secondary Hypothesis — the BroncoCTF ancestor ("Grandma's Secret Recipe")

A very similar challenge exists in the public **BroncoCTF 2025** set:
*"Grandma's Secret Recipe"*. Its mechanic:

- `GET /login` sets cookies `role="kitchen helper"` and
  `checksum = md5(role)`.
- `GET /grandma` with `role=grandma; checksum=md5("grandma")` returns the flag.
- The denial page is HTTP **200**, so a wordlist scan would find the route.

The instance's own HTML is even themed as a "Grandma/Granny" portal, so this
lineage was worth testing. Verified hashes:

| value | md5 |
|---|---|
| `kitchen helper` | `a223befb6660a23f9c3491f74ef84e43` |
| `grandma` | `a5d19cdd5fd1a8f664c0ee2b5e293167` |
| `granny` | `dc5a4e9caf9a70b6fe736090eb2016d8` |
| `admin` | `21232f297a57a5a743894a0e4a801fc3` |
| `chef` | `cbb4581ba3ada1ddef9b431eef2660ce` |

Tests performed:

- `GET /login` → **404** (in the ancestor this sets the cookies).
- `GET /grandma` → **404** (in the ancestor this returns the flag).
- Forged `role=grandma; checksum=md5("grandma")` and ~1,100 other
  role/checksum combinations against `/` — **no response change, no cookie set**.

So **this deployment does not implement the ancestor's routes at all.**

---

## 7. Full Timeline of Attempts

| Time (IST) | Action | Outcome |
|---|---|---|
| 01:31–01:36 | Initial recon, captured `root.html` | 1 route, portal |
| 01:32 | `ffuf common.txt` | 0 results |
| 01:39 | Saved `root.html` (1481 B) | baseline |
| 01:46–01:59 | `ffuf raft-medium-directories.txt` | 0 results |
| 01:49–01:56 | Cookie fuzz, header reflection, `ffuf words` | nothing |
| 08:38–08:45 | Reflection, static/src fuzz, SNI/vhost scripts | nothing |
| 08:51–09:18 | **Pickle deserialisation probes** (cookies/params/body) | no execution |
| 08:55–09:13 | Cookie role/checksum brute force (~1,100 combos) | no hits |
| 09:01 | `ffuf raft-medium-words.txt` (full) | **0 results** |
| 09:04–09:09 | Boolean probes, `homeprobe`, ancestor route tests | `/login`,`/grandma` → 404 |
| 09:25 | Re-ran full words scan to confirm | 0 results |
| 10:02+ | **Misroute** battery (paths, headers, overrides, trailing slash) | nothing |
| 10:09 | Sibling hostnames, 8443, port-23 router | not routed / empty |
| 10:10 | Port/DNS re-verification | 23/80/443/8443 only |

---

## 8. Environment / Tooling

- **OS:** local Kali Linux, Python 3 venv (`~/venv`).
- **Tools used:** `ffuf`, `curl`, `nmap`, `nc`, `python3` (`requests`,
  `urllib3`, `concurrent.futures`), browser dev-tools / Caido for traffic.
- **CTFd session** extracted from the Zen browser cookie DB
  (`…/zen/*/cookies.sqlite` → copied to `/tmp/ctfd_cookies.sqlite`) to query
  the CTFd API for challenge 23.

---

## 9. Conclusion & Analysis

**The flag was not recovered.** Assessment:

1. **The deployment exposes only `GET /`.** Three independent wordlist scans
   (`common.txt`, `raft-medium-directories.txt`, the entire
   `raft-medium-words.txt`) returned **zero** non-404 results, and ~1300
   hand-picked paths plus all method/header/cookie/normalisation tricks found
   nothing else. The `/` route is bound to `GET` only (POST → 405), so the
   visible login logic cannot live on `/`.

2. **The page advertises `/login`, but `/login` is not registered.**
   `POST /login` returns a router-level `404` (not `405`), which is only
   possible when the route does not exist. This is almost certainly the crux:
   the intended solution needs the `/login` handler (and probably a guarded
   admin/flag route) that this container failed to serve.

3. **The description screams "misroutes".** `sour items` ⇄ `misroutes` is an
   exact anagram; together with *"The Access Portal that no one can access"*
   this points at a routing-confusion / request-smuggling class bug. Every
   variant of that class was tested and none applied to this deployment.

4. **Most likely explanation:** a **broken/incomplete deploy** (the app's
   route table only contained `/`), or the challenge expected a platform
   mechanic (e.g. destroying + relaunching the instance) that was not exercised
   before the CTF closed. A fresh redeploy is the recommended next step if the
   challenge is ever re-run — it would immediately show whether `/login` is
   supposed to exist.

### Recommended next steps (if revisited)

1. **Destroy + relaunch** the instance via CTFd
   (`POST /services/destroy?challenge_id=23`, then `challenge.launch()`) and
   immediately re-check `GET /login` / `GET /grandma`.
2. With a healthy deploy, re-run the **misroute** battery against the route
   that actually appears, focusing on *cluster* techniques:
   `X-Original-URL`/`X-Rewrite-URL`, absolute-URI targets, and **HTTP/1.1
   request smuggling** between openresty (80/443) and Werkzeug.
3. If `/login` appears: test the `user` field for **pickle** (`pickles` /
   "sour items") and for role/checksum cookie logic (ancestor mechanic).

---

## Appendix A — Raw Evidence Snippets

### A.1 `GET /` (headers)

```
HTTP/1.1 200 OK
Server: Werkzeug/3.1.3 Python/3.10.18
Date: Sun, 11 Oct 2026 04:39:56 GMT
Content-Type: text/html
Content-Length: 1481
Connection: close
```

### A.2 `GET /login`

```
$ curl -sik https://<host>/login
HTTP/1.1 404 NOT FOUND
Server: Werkzeug/3.1.3 Python/3.10.18
Content-Type: text/html; charset=utf-8
Content-Length: 207
Connection: close

<!doctype html>
<html lang=en>
<title>404 Not Found</title>
<h1>Not Found</h1>
<p>The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.</p>
```

### A.3 `OPTIONS /`

```
HTTP/1.1 200 OK
Server: Werkzeug/3.1.3 Python/3.10.18
Allow: OPTIONS, GET, HEAD
Content-Length: 0
Connection: close
```

### A.4 Port 80 (openresty) redirect

```
$ curl -sik http://<host>/login
HTTP/1.1 301 Moved Permanently
Server: openresty/1.27.1.2
Location: https://kicyber-2bccd62e5d76-granny-makes-food-0-0.chals.io/login
Content-Length: 175
```

### A.5 ns / ports

```
PORT     STATE SERVICE
23/tcp   open  telnet
80/tcp   open  http
443/tcp  open  https
8443/tcp open  https-alt
```

### A.6 Sibling hostname routing test

```
kicyber-2bccd62e5d76-granny-makes-food-0-1.chals.io  ip=143.244.222.116  https/443=000
kicyber-2bccd62e5d76-granny-makes-food-1-0.chals.io  ip=143.244.222.116  https/443=000
kicyber-2bccd62e5d76-granny-makes-food-0-0.chals.io  ip=143.244.222.115  https/443=200
kicyber-2bccd62e5d76.chals.io                       ip=143.244.222.116  https/443=000
kicyber.chals.io                                    ip=143.244.222.116  https/443=000
```

### A.7 Port 23 router

```
granny             -> Host: Couldn't find underlying service
granny-makes-food  -> Host: Couldn't find underlying service
admin              -> Host: Couldn't find underlying service
grandma            -> Host: Couldn't find underlying service
```

---

## Appendix B — Evidence Files in `granny/`

| File | Purpose |
|---|---|
| `root.html` | Verbatim portal body (1481 B, md5 `aeed43fa…`) |
| `ffuf_common.json` | `common.txt` scan — 0 results |
| `ffuf_raft.json` | `raft-medium-directories.txt` scan — 0 results |
| `ffuf_words.json` | Partial words scan — 0 results |
| `ffuf_words_full.json` | Full `raft-medium-words.txt` scan — **0 results** |
| `misroute.py` | Path/header/trailing-slash "misroute" battery |
| `pickleprobe.py` | Pickle-via-cookie/param timing probes |
| `pickletime.py`, `bodypickle.py`, `bigsleep.py` | Pickle POST-body / sleep payloads |
| `cookietest.py`, `cookiefuzz.py`, `ckbrute.py` | Cookie / role-checksum forgery (~1100 combos) |
| `refl.py`, `hdrreflect.py`, `boolq.py` | Parameter/header reflection & logic probes |
| `grandma.py`, `grandma2.py` | Ancestor (BroncoCTF) route/hash tests |
| `homeprobe.py`, `srcfuzz.py`, `staticfuzz.py` | Source-disclosure fuzzing |
| `themed.py`, `themed2.py`, `matrix.py` | Themed route enumeration |
| `vhost.py`, `vhost2.sh`, `snifuzz.sh` | Host/SNI vhost fuzzing |
| `bench.py` | Baseline timing/behaviour benchmark |
| `granny/ctfd_challenge23.json` | CTFd API response (post-CTF "has ended") |

---

## Appendix C — Key Facts at a Glance

- Flag format: **`KPMG_CTF{...}`**
- Route table of the deployment: **`GET /` only.**
- `/` POST → **405**; `/login` any method → **404** (route absent).
- Server: **Werkzeug/3.1.3 Python/3.10.18**; edge on 80 is **openresty/1.27.1.2**.
- Anomaly: portal advertises `/login`, but `/login` does not exist → **root cause of the failed solve** (broken/incomplete deploy).
- Strong hint: **`sour items` ⇄ `misroutes`** (routing confusion / request smuggling theme).
- Ports: **23, 80, 443, 8443**. Edge routes by **TLS SNI**.

---

*End of writeup. Compiled 2026-10-11 after the KPMG CTF 2026 campus edition closed.*
