import json,base64,re,sys
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
D=json.load(open('vault.json'))
b=D['b1']
salt=base64.b64decode(b['s']); iv=base64.b64decode(b['iv']); ct=base64.b64decode(b['d']); it=b['it']
def norm(s): return re.sub(r'[^a-z0-9]','',s.lower())
def test(p):
    kdf=PBKDF2HMAC(algorithm=hashes.SHA256(),length=32,salt=salt,iterations=it)
    k=kdf.derive(p.encode())
    try:
        return AESGCM(k).decrypt(iv,ct,None)
    except Exception:
        return None
cands=[]
# artifact words
artifact = """Nova Keller games and golden hours indie game developer coastal photographer
Selected frames Harbour 6:04pm Last ferry Horizon line After the sun Low tide The long drive
Prints by request the rest of the keepers live in the vault
On rebranding Changed the name a while back the work's the same
Everything I build still goes up in the open warts rebases and all
On film One roll a trip and I'm ruthless about which frame survives The keepers end up in the vault not the feed
shot on film built in the open
driftlog config-archive dotfiles ld53-jam shader-doodles
old dotfiles archive shell editor config personal site build in the open ludum dare 53 prototype glsl shader experiments
Nova Keller socials draft decide which handle I am actually keeping nova drifts keller
the vault step 1 of 2 guess the place unlock the flag
nvk_dev nvk dev nvkdev""".split()
cands += artifact
links = ["https://www.linkedin.com/in/nova-drifts/","https://www.linkedin.com/in/nova-keller-/",
         "https://github.com/nova-drifts","nova-drifts","nova-keller-","nova_keller",
         "the one thing worth keeping","the one thing worth keeping I locked","i never delete i just stop pointing",
         "i never delete","i just stop pointing","everything i walked away from is still out there",
         "the key's already yours","the keys already yours","goldenhour","golden hour","golden-hour",
         "keepers","keeper","thekeeper","novakeller","novadrifts","nvk","nvkdev","nvk_dev",
         "backup-2024","backup2024","staging","app_env","debug","configarchive","config archive",
         "drift","drifts","driftwood","lowtide","harbour","ferry","horizon","longdrive","aftersun"]
cands += links
seen=set(); out=None
for c in cands:
    p=norm(c)
    if not p or p in seen: continue
    seen.add(p)
    r=test(p)
    if r:
        print("FOUND:",repr(c),"norm=",p)
        open('stage1.raw','wb').write(r); out=c; break
if not out: print("no match among",len(seen),"candidates")
