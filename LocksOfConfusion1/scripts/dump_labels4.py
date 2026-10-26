#!/usr/bin/env python3
"""Row-band label extraction + ASCII render (clean, full labels)."""
import io, re, ssl, sys, subprocess, tempfile, os
from collections import deque
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


def label_band(strip):
    sarr = np.array(strip.convert("L")).astype(int)
    light = sarr > 130
    rowsum = light.sum(axis=1)
    bands = []
    start = None
    for j, v in enumerate(rowsum):
        if v >= 2 and start is None:
            start = j
        elif v < 2 and start is not None:
            if j - start >= 4:
                bands.append((start, j - 1))
            start = None
    if start is not None and len(rowsum) - start >= 4:
        bands.append((start, len(rowsum) - 1))
    if not bands:
        return None
    by0, by1 = min(bands, key=lambda b: (b[0], -(b[1] - b[0])))
    return light[by0:by1 + 1, :]


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
    print("nonce", nonce)
    for x0, y0, x1, y1, cx, cy in sorted(nodes, key=lambda z: (z[1], z[0])):
        strip = img.crop((max(x0 - 120, 0), y1 + 1, min(x1 + 120, 640), min(y1 + 22, 360)))
        lb = label_band(strip)
        if lb is None:
            print(f"\n### ({cx},{cy}): NO LABEL ###")
            continue
        cols = np.where(lb.any(axis=0))[0]
        cols = np.arange(cols.min(), cols.max() + 1)
        lb = lb[:, cols]
        show = ["".join("#" if lb[j, i] else " " for i in range(lb.shape[1])).rstrip()
                for j in range(lb.shape[0])]
        while show and not show[-1].strip():
            show.pop()
        print(f"\n### center=({cx},{cy}) ###")
        for line in show:
            print("  " + "".join(c * 2 for c in line))


if __name__ == "__main__":
    sys.exit(main())