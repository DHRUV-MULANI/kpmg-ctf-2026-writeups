#!/usr/bin/env python3
"""Try full-image OCR to find the lb-02 label, then click that node."""
import io, json, re, ssl, subprocess, sys, tempfile, os
from collections import deque
import numpy as np
import urllib.request
from PIL import Image, ImageOps

B = "https://kicyber-deea1f3c3f67-locks-of-confusion1-0-0.chals.io"
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE


def http(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, context=ctx, timeout=25) as r:
        return r.read()


def components(mask, minn=10):
    H, W = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    out = []
    for y in range(H):
        for x in range(W):
            if not mask[y, x] or seen[y, x]:
                continue
            q = deque([(y, x)]); seen[y, x] = True
            xs, ys = [], []
            while q:
                cy, cx = q.popleft(); xs.append(cx); ys.append(cy)
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True; q.append((ny, nx))
            if len(xs) >= minn:
                out.append((min(xs), min(ys), max(xs), max(ys), len(xs)))
    return out


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def main():
    html = http(B + "/verify").decode()
    nonce = re.search(r'var nonce = "([0-9a-f]+)"', html).group(1)
    src = re.search(r'src="(/verify/image/[0-9a-f]+)"', html).group(1)
    img = Image.open(io.BytesIO(http(B + src))).convert("RGB")
    arr = np.array(img).astype(int)
    bg = np.array([18, 18, 18])
    mask = (np.abs(arr - bg).sum(axis=2) > 100)
    comps = components(mask, minn=300)
    nodes = []
    for x0, y0, x1, y1, n in comps:
        w, h = x1 - x0 + 1, y1 - y0 + 1
        if 250 <= n <= 4000 and 0.4 <= w / h <= 2.2:
            nodes.append((x0, y0, x1, y1, (x0 + x1) // 2, (y0 + y1) // 2))
    print("nonce", nonce, "nodes:", [(cx, cy) for _, _, _, _, cx, cy in nodes])

    # Full-image OCR word boxes
    inv = ImageOps.invert(img.convert("L"))
    big = inv.resize((inv.width * 6, inv.height * 6), Image.NEAREST)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        big.save(f.name); path = f.name
    try:
        tsv = subprocess.run(["tesseract", path, "stdout", "--psm", "11", "tsv"],
                             capture_output=True, text=True).stdout
    finally:
        os.unlink(path)
    words = []
    for line in tsv.splitlines()[1:]:
        p = line.split("\t")
        if len(p) >= 12 and p[11].strip():
            words.append((int(p[6]) / 6, int(p[7]) / 6, int(p[8]) / 6, int(p[9]) / 6, p[11].strip()))
    print("words:")
    for w in sorted(words, key=lambda v: (v[1], v[0])):
        print("   %-12s x=%.0f y=%.0f  (center %.0f,%.0f)" % (w[4], w[0], w[1], w[0] + w[2] / 2, w[1] + w[3] / 2))

    # find lb-02
    tgt = None
    for wx, wy, ww, wh, wt in words:
        if norm(wt) == "lb02" or norm(wt) in ("1b02",):
            tgt = (wx + ww / 2, wy + wh / 2, wt)
            break
    print("target:", tgt)
    if tgt is None:
        print("lb-02 not found via OCR")
        return 1
    tx, ty, wt = tgt
    # click the node whose center is nearest the label
    near = min(nodes, key=lambda z: (z[4] - tx) ** 2 + (z[5] - ty) ** 2) if nodes else None
    cands = []
    if near:
        cands.append((near[4], near[5]))
    cands.append((int(tx), int(ty)))
    for x, y in cands:
        body = json.dumps({"nonce": nonce, "x": x, "y": y}).encode()
        res = http(B + "/verify/check", data=body, headers={"Content-Type": "application/json"}).decode()
        print("click", x, y, "->", res)
        if '"ok":true' in res:
            print("SUCCESS")
            return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())