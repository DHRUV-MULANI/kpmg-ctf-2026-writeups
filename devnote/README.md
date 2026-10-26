# devnote — evidence bundle

Raw request/response evidence for the DevNote 10 SQL injection challenge.

Target: `http://kicyber-81cdac2d8817-devnote-0-0.chals.io`
Companion writeup: `../DevNote-writeup.md`

## Files

| File | What it shows |
|---|---|
| `00_http_redirect.txt` | openresty edge 301 http -> https |
| `01_login_page.txt` | login page + leaked `<!--guest:guest123 -->` |
| `02_login_guest.txt` | guest login 302 + Flask session cookie |
| `03_dashboard_guest.txt` | guest dashboard + `/dashboard?q=` dev query interface |
| `04_q_probes.txt` | SQLi confirmation probes on `q` |
| `05_schema_enumeration.txt` | `sqlite_master` dump: `users`, `secrets` |
| `06_dump_users.txt` | users table (admin/dev/guest creds) |
| `07_dump_secrets.txt` | secrets table -> FLAG |
| `08_admin_login.txt` | admin login (confirms admin is not the gate) |
| `cookies.txt` | Flask session cookie notes |

## Flag

```
KPMG_CTF{_YD6yhbWjlH1AyuIZtztcelgNRN2VA1HiVn-bZh4djGW}
```

## Note on capture timing

The live instance was up at **2026-10-10 19:25 UTC**, when all outputs above were recorded.
It was later stopped (the chals.io proxy returns `Couldn't find underlying service`), so these
files are the verbatim transcript of the successful run rather than a fresh re-capture.
