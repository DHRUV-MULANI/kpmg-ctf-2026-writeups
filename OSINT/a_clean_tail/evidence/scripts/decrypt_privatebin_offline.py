#!/usr/bin/env python3
import json, zlib, base64, hashlib, itertools
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def b58decode(s):
    n = 0
    for ch in s:
        n = n * 58 + ALPHABET.index(ch)
    full = n.to_bytes((n.bit_length() + 7) // 8, "big")
    pad = 0
    for ch in s:
        if ch == ALPHABET[0]:
            pad += 1
        else:
            break
    return b"\x00" * pad + full

pb = json.load(open("/tmp/opencode/paste.json"))
adata = pb["adata"]
spec = adata[0]
iv = base64.b64decode(spec[0] + "=" * (-len(spec[0]) % 4))
salt = base64.b64decode(spec[1] + "=" * (-len(spec[1]) % 4))
iters = spec[2]; keysize = spec[3]; comp = spec[7]
ct = base64.b64decode(pb["ct"])
frag = "8DPEkPZMJFcPWGWXGLbF4Nd3afesNEWs9agcT4VSsoA9"

keys = {
    "b58pad": b58decode(frag).rjust(32, b"\x00"),
    "b58": b58decode(frag),
    "b64": base64.b64decode(frag + "=" * (-len(frag) % 4)),
    "rawstr": frag.encode(),
}

aads = {
    "plain": json.dumps(adata, separators=(",", ":"), ensure_ascii=False).encode(),
    "esc": json.dumps(adata, separators=(",", ":"), ensure_ascii=False).replace("/", "\\/").encode(),
    "none": None,
}

for kn, k in keys.items():
    dk = hashlib.pbkdf2_hmac("sha256", k, salt, iters, keysize // 8)
    for an, aad in aads.items():
        try:
            pt = AESGCM(dk).decrypt(iv, ct, aad)
            if comp == "zlib":
                pt = zlib.decompress(pt)
            print("SUCCESS", kn, an)
            print(pt.decode("utf-8", "replace"))
            raise SystemExit
        except Exception as e:
            print("fail", kn, an, type(e).__name__)
