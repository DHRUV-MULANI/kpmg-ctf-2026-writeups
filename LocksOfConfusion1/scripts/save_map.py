#!/usr/bin/env python3
"""Render coarse ASCII map of one diagram; save image+nonce to evidence dir."""
import io, re, ssl, sys, os
import numpy as np
import urllib.request
from PIL import Image

B = "https://kicyber-deea1f3c3f67-locks-of-confusion1-0-0.chals.io"
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
OUT = os.path.join(os.path.dirname(__file__), "..", "raw")
OUT = os.path.abspath(OUT)

with urllib.request.urlopen(B + "/verify", context=ctx, timeout=25) as r:
    h = r.read().decode()
nonce = re.search(r'var nonce = "([0-9a-f]+)"', h).group(1)
src = re.search(r'src="(/verify/image/[0-9a-f]+)"', h).group(1)
with urllib.request.urlopen(B + src, context=ctx, timeout=25) as r:
    data = r.read()
img = Image.open(io.BytesIO(data)).convert("RGB")
arr = np.array(img).astype(int)

with open(os.path.join(OUT, "verify_current.png"), "wb") as f:
    f.write(data)
with open(os.path.join(OUT, "verify_nonce.txt"), "w") as f:
    f.write(nonce + "\n" + src + "\n")
print("nonce", nonce, "saved", OUT)

# coarse map: downsample 4x
H, W = arr.shape[0], arr.shape[1]
sy, sx = 4, 4
mapfile = os.path.join(OUT, "verify_map.txt")
rows = []
for j in range(0, H, sy):
    row = []
    for i in range(0, W, sx):
        blk = arr[j:j + sy, i:i + sx].reshape(-1, 3)
        blue = (np.abs(blk - np.array([60, 110, 180])).sum(axis=1) <= 60).sum()
        light = ((blk > 150).all(axis=1)).sum()
        if blue > sy * sx * 0.5:
            row.append("#")
        elif light > 2:
            row.append("T")
        else:
            row.append(".")
    rows.append("".join(row))
with open(mapfile, "w") as f:
    f.write("\n".join(rows))
print("map written", mapfile)
for line in rows[:90]:
    print(line)