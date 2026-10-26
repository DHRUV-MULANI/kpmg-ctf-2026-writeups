#!/usr/bin/env python3
"""Deep inspect one random diagram image: colors, all components, labels."""
import io, json, re, ssl, subprocess, sys, tempfile, os
from collections import Counter, deque
import numpy as np
import urllib.request
from PIL import Image, ImageOps

B = "https://kicyber-deea1f3c3f67-locks-of-confusion1-0-0.chals.io"
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE


def http(url):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, context=ctx, timeout=25) as r:
        return r.read()


def components(mask, minn=3):
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


def main():
    html = http(B + "/verify").decode()
    nonce = re.search(r'var nonce = "([0-9a-f]+)"', html).group(1)
    src = re.search(r'src="(/verify/image/[0-9a-f]+)"', html).group(1)
    im = Image.open(io.BytesIO(http(B + src))).convert("RGB")
    arr = np.array(im).astype(int)
    print("nonce", nonce)
    print("colors:")
    for col, n in Counter(map(tuple, arr.reshape(-1, 3))).most_common(20):
        print("  ", col, n)

    # non-background
    bg = np.array([18, 18, 18])
    mask = (np.abs(arr - bg).sum(axis=2) > 60)
    comps = sorted(components(mask, minn=4), key=lambda c: -c[4])
    print("\ncomponents (x0,y0,x1,y1,area):")
    for x0, y0, x1, y1, n in comps[:40]:
        col = arr[y0 + (y1 - y0) // 2, x0 + (x1 - x0) // 2]
        print("  ", (x0, y0, x1, y1, n), "center color", tuple(col))


if __name__ == "__main__":
    sys.exit(main())