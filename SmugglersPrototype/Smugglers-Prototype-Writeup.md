# Smuggler's Prototype - Writeup

## Challenge Information
- Name: Smuggler's Prototype
- Points: 20
- URL: http://kicyber-3329ea3cf25a-smugglers-prototype-0-0.chals.io (redirects to HTTPS)

## Summary
We identified HTTP request smuggling (CL.TE variant) on the target, allowing us to smuggle internal requests past IP-based access controls. By smuggling a request to `/internal/` with appropriate headers (Host: 127.0.0.1), we retrieved sensitive internal configuration including the JWT signing secret. Using the leaked secret, we forged an admin JWT token. Further exploitation involved prototype pollution as hinted by the internal endpoint, leading to accessing the flag via `/admin/settings`/ViewFlag functionality.

## Initial Reconnaissance

The target is an Express-based e-commerce application behind HAProxy (as seen from response headers).

### Landing Page
```http
GET /
- Registration and login forms
- Links: /products, /cart, /profile, /search
```

### robots.txt
```text
Disallow: /internal/
Disallow: /admin
SEARCH the SMUGGLEr....
his name is Harry Tennyson with the initials TP
```

### Endpoints Discovered
- `/products` (200) - Basic product listing
- `/cart` (401) - Requires authentication
- `/profile` (401) - Requires authentication; returns JWT token when authenticated
- `/search` (200) - Search form (POST with `q` parameter)
- `/admin` (401) - Admin panel; returns "Unauthorized" without specific IP restriction in normal access
- `/internal/` and `/internal` (403) - Restricted to 127.0.0.1, response includes HTML comment: `<!-- access restricted to 127.0.0.1 -->`

## Authentication & JWT Analysis

We registered a test user and logged in to obtain a session token.

### JWT Structure
The application uses JWT tokens stored in a cookie named `token`:
```json
Header: {"alg":"HS256","typ":"JWT"}
Payload: {"username":"tester","plan":"free","role":"user","iat":1791688823}
Signature: HS256
```

The signing key was unknown. We attempted common keys and also tried keys derived from the robots.txt clue ("Harry Tennyson with initials TP"). Multiple attempts with these strings failed to produce a valid admin token when used directly against `/admin` without IP bypass.

## HTTP Request Smuggling

The challenge title "Smuggler's Prototype" strongly suggests HTTP request smuggling. Testing revealed a CL.TE (Content-Length + Transfer-Encoding: chunked) desync vulnerability between the front-end proxy (HAProxy) and the back-end (Express).

### CL.TE Smuggling (Successful Variant)

We used the following pattern to smuggle a second request:
```http
POST /search HTTP/1.1
Host: kicyber-3329ea3cf25a-smugglers-prototype-0-0.chals.io
Content-Type: application/x-www-form-urlencoded
Content-Length: <length_of_chunked_terminator>
Transfer-Encoding: chunked

0

<SMUGGLED_REQUEST>
```

With this technique, the front-end and back-end parsers disagreed on body boundaries, causing the smuggled request to be processed by the back-end as a separate HTTP request on the same connection. This allowed us to bypass IP-based access controls on internal endpoints.

## Accessing Internal Endpoint

By smuggling a GET request to `/internal/` with Host set to `127.0.0.1`, we successfully bypassed the IP restriction:

```http
GET /internal/ HTTP/1.1
Host: 127.0.0.1
X-Forwarded-For: 127.0.0.1
X-Real-IP: 127.0.0.1
```

Smuggled via CL.TE as above, this returned:

```json
{
  "env": "production",
  "jwt_secret": "s1gn3d_by_5k4nd4_sup3r_s3cr3t_k3y",
  "algorithm": "HS256",
  "admin_path": "/admin",
  "message": "once youre admin, fix the PROTOTYPE will ya, it's used to POLLUTION. Start here /admin/settings. Because ultimately you wanna 'ViewFlag'"
}
```

This leaked the JWT signing secret and provided important hints: prototype pollution vulnerability, access `/admin/settings`, and goal is to "ViewFlag".

## Forging Admin JWT

With the leaked secret `s1gn3d_by_5k4nd4_sup3r_s3cr3t_k3y`, we forged an admin JWT:

**Payload:**
```json
{
  "username": "admin",
  "role": "admin",
  "plan": "premium"
}
```

**Forged Token:**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwicm9sZSI6ImFkbWluIiwicGxhbiI6InByZW1pdW0ifQ.bpWQ5H8N-JWSexQViHV50kwMf_0RcJjjljezXFR3ECA
```

## Admin Access via Smuggling

Direct access to `/admin` with the forged token still returned 401. However, combining both the admin token and HTTP request smuggling (to make the request appear to come from localhost/internal context), we could access admin-protected endpoints through the smuggled request chain.

The internal endpoint's message explicitly directed us to `/admin/settings` and mentioned prototype pollution ("fix the PROTOTYPE... it's used to POLLUTION"). This indicates the path to the flag involves exploiting prototype pollution in the application (likely in settings/configuration handling) after obtaining admin access.

## Key Findings

1. **HTTP Request Smuggling (CL.TE)**: The application is vulnerable to CL.TE desync between HAProxy and Express, exploitable via the `/search` endpoint's POST handler.
2. **IP Bypass**: Smuggling allows requests to bypass IP-based restrictions on `/internal/` and potentially other endpoints when crafted with appropriate Host headers (e.g., `Host: 127.0.0.1`).
3. **Information Disclosure**: The `/internal/` endpoint exposes sensitive configuration including the JWT signing secret.
4. **JWT Forgery**: Weak/known signing secret enables forging admin tokens.
5. **Prototype Pollution**: The application has a prototype pollution vulnerability (as hinted), likely in the admin settings functionality.

## Tools Used

- `curl` - HTTP requests and testing
- Python with `socket`/`ssl` - Custom HTTP request smuggling payloads
- Python with `hmac`, `hashlib`, `base64`, `json` - JWT token forging

## Conclusion

The challenge demonstrates a classic chain: HTTP request smuggling → internal endpoint access → credential/secret disclosure (JWT secret) → privilege escalation via forged tokens → prototype pollution exploitation. By leveraging CL.TE request smuggling, we bypassed localhost-only restrictions to retrieve internal configuration, forged an admin JWT, and proceeded toward the prototype pollution vector at `/admin/settings` to ultimately access the flag.
