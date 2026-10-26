import subprocess, re
from PIL import Image
P="/home/boss/Works/ctf/KPMG/OSINT/a_clean_tail/Challenge.png"
img=Image.open(P).convert("L")
W,H=img.size
cols,rows=5,4
ow,oh=W//cols,H//rows
allwords=[]
for r in range(rows):
    for c in range(cols):
        x0=max(0,c*ow-20); y0=max(0,r*oh-20)
        x1=min(W,(c+1)*ow+20); y1=min(H,(r+1)*oh+20)
        t=img.crop((x0,y0,x1,y1)).resize(((x1-x0)*4,(y1-y0)*4))
        p=f"/tmp/opencode/tt_{r}_{c}.png"; t.save(p)
        out=subprocess.run(["tesseract",p,"stdout","--psm","11"],capture_output=True,text=True).stdout
        for w in out.split():
            if len(w)>=3 and re.search(r"[A-Za-z]{3,}", w):
                allwords.append((r,c,w))
seen=set()
for r,c,w in allwords:
    k=w.lower()
    if k in seen: continue
    seen.add(k)
    print(f"r{r}c{c}: {w}")
