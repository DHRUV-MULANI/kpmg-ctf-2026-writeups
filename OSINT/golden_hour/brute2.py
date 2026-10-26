import json,base64,re,sys
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

D=json.load(open('vault.json'))
b=D['b2']
salt=base64.b64decode(b['s']); iv=base64.b64decode(b['iv']); ct=base64.b64decode(b['d']); it=b['it']
def norm(s): return re.sub(r'[^a-z0-9]','',s.lower())
def test(key):
    kdf=PBKDF2HMAC(algorithm=hashes.SHA256(),length=32,salt=salt,iterations=it)
    k=kdf.derive(key.encode())
    try:
        return AESGCM(k).decrypt(iv,ct,None)
    except Exception:
        return None

cands = sys.argv[1:]
if not cands:
    cands = open('places.txt').read().split('\n') if __import__('os').path.exists('places.txt') else []
base = "driftwood"
seen=set(); found=None
for c in cands:
    c=c.strip()
    if not c: continue
    key = norm(base)+"|"+norm(c)
    if key in seen: continue
    seen.add(key)
    r=test(key)
    if r:
        print("FOUND key=%r input=%r" % (key,c))
        print(r.decode('utf-8','replace'))
        found=c; break
if not found: print("no match among",len(seen),"candidates")
