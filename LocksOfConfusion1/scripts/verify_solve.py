#!/usr/bin/env python3
"""Solver for the /verify access-check gate.

The page serves a randomly regenerated network diagram per request. The image
src and the JSON nonce share the same hex id. We must click the node labeled
"lb-02" and POST its natural-image coordinates.
"""
import io, json, re, ssl, subprocess, sys, tempfile
from collections import deque

import numpy as np
import urllib.request
from PIL import Image

B = "https://kicyber-deea1f3c3f67-locks-of-confusion1-0-0.chals.io"
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def http(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, context=ctx, timeout=25) as r:
        return r.read()


def components(mask):
    H, W = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    out = []
    for y in range(H):
        for x in range(W):
            if not mask[y, x] or seen[y, x]:
                continue
            q = deque([(y, x)])
            seen[y, x] = True
            xs, ys = [], []
            while q:
                cy, cx = q.popleft()
                xs.append(cx); ys.append(cy)
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
            out.append((min(xs), min(ys), max(xs), max(ys), len(xs)))
    return out


def find_nodes(im):
    """Blue filled circles = nodes."""
    arr = np.array(im.convert("RGB")).astype(int)
    blue = (np.abs(arr - np.array([60, 110, 180])).sum(axis=2) <= 60)
    nodes = []
    for x0, y0, x1, y1, n in components(blue):
        w, h = x1 - x0 + 1, y1 - y0 + 1
        if n < 400 or not (0.6 < w / h < 1.7):
            continue
        nodes.append(((x0 + x1) // 2, (y0 + y1) // 2, w, h))
    return nodes


def ocr_words(im):
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        big = im.resize((im.width * 5, im.height * 5), Image.LANCZOS)
        big.save(f.name)
        path = f.name
    out = subprocess.run(["tesseract", path, "stdout", "--psm", "11", "tsv"],
                         capture_output=True, text=True).stdout
    words = []
    for line in out.splitlines()[1:]:
        p = line.split("\t")
        if len(p) >= 12 and p[11].strip():
            x, y, w, h = int(p[6]), int(p[7]), int(p[8]), int(p[9])
            words.append((x / 5, y / 5, w / 5, h / 5, p[11].strip()))
    return words


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def main():
    html = http(B + "/verify").decode()
    nonce = re.search(r'var nonce = "([0-9a-f]+)"', html).group(1)
    src = re.search(r'src="(/verify/image/[0-9a-f]+)"', html).group(1)
    img = Image.open(io.BytesIO(http(B + src)))
    im = img.convert("RGB")
    nodes = find_nodes(im)
    words = ocr_words(im)
    print("nonce", nonce)
    print("nodes", nodes)
    print("words", [(round(w[0]), round(w[1]), w[4]) for w in words])

    target = None
    for wx, wy, ww, wh, wt in words:
        if norm(wt) in ("lb02", "1b02", "lb0z", "lb02."):
            target = (wx + ww / 2, wy + wh / 2)
    print("target label center", target)

    # candidate clicks: node nearest to the label, plus the label itself
    cands = []
    if target:
        best = min(nodes, key=lambda n: (n[0] - target[0]) ** 2 + (n[1] - target[1]) ** 2)
        cands.append((best[0], best[1]))
        cands.append((int(target[0]), int(target[1])))
        for n in nodes:
            cands.append((n[0], n[1]))
    cands = list(dict.fromkeys(cands))

    for x, y in cands:
        body = json.dumps({"nonce": nonce, "x": x, "y": y}).encode()
        try:
            res = http(B + "/verify/check", data=body,
                       headers={"Content-Type": "application/json"}).decode()
        except Exception as e:
            res = "ERR %s" % e
        print("click", x, y, "->", res)
        if '"ok":true' in res or '"ok": true' in res:
            print("SUCCESS")
            return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
