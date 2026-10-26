#!/usr/bin/env python3
import json, zlib, base64, hashlib, sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
ALPHABET="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
def b58decode(s):
    n=0
    for ch in s: n=n*58+ALPHABET.index(ch)
    full=n.to_bytes((n.bit_length()+7)//8,"big")
    z=0
    for ch in s:
        if ch==ALPHABET[0]: z+=1
        else: break
    return b"\x00"*z+full
pb=json.load(open("/tmp/opencode/paste.json"))
adata=pb["adata"]; spec=adata[0]
iv=base64.b64decode(spec[0]+"="*(-len(spec[0])%4))
salt=base64.b64decode(spec[1]+"="*(-len(spec[1])%4))
iters=spec[2]; keysize=spec[3]; comp=spec[7]
ct=base64.b64decode(pb["ct"])
frag="8DPEkPZMJFcPWGWXGLbF4Nd3afesNEWs9agcT4VSsoA9"
key=b58decode(frag).rjust(32,b"\x00")
aad=json.dumps(adata,separators=(",",":"),ensure_ascii=False).encode()

def attempt(password:str):
    kb=key+(password.encode() if password else b"")
    dk=hashlib.pbkdf2_hmac("sha256",kb,salt,iters,keysize//8)
    try:
        pt=AESGCM(dk).decrypt(iv,ct,aad)
        if comp=="zlib": pt=zlib.decompress(pt)
        return pt.decode("utf-8","replace")
    except Exception:
        return None

cands=[]
phones=["6144284536","614-428-4536","(614) 428-4536","+16144284536","(614)428-4536","614 428 4536","614.428.4536"]
for p in phones:
    cands.append(p)
    cands.append(p.replace("-","").replace(" ","").replace("(","").replace(")",""))
# also raw sign plausible
for c in cands:
    r=attempt(c)
    print(repr(c), "->", "OK" if r else "no")
    if r:
        print("PASSWORD:", c)
        print(r)
        sys.exit(0)
print("no match")
