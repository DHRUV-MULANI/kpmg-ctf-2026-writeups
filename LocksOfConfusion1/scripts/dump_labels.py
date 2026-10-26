#!/usr/bin/env python3
"""Dump inverted, high-fidelity ASCII art of each node label for the CURRENT nonce.
Prints nonce so labels can be read, then click target manually."""
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


def render_labels(nonce):
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
    for i, (x0, y0, x1, y1, cx, cy) in enumerate(sorted(nodes, key=lambda z: (z[1], z[0]))):
        strip = img.crop((max(x0 - 90, 0), y1 + 1, x1 + 90, min(y1 + 60, img.height)))
        sarr = np.array(strip.convert("L")).astype(int)
        ys, xs = np.where(sarr > 130)
        if not len(xs):
            print(f"\n### node {i} ({cx},{cy}): NO LABEL ###")
            continue
        gcs = components(sarr > 130, minn=2)
        gx0 = min(c[0] for c in gcs); gx1 = max(c[2] for c in gcs)
        gy0 = min(c[1] for c in gcs); gy1 = max(c[3] for c in gcs)
        ox = max(x0 - 90, 0); oy = y1 + 1
        crop = img.crop((ox + gx0 - 4, oy + gy0 - 4, ox + gx1 + 4, oy + gy1 + 4))
        inv = ImageOps.invert(crop.convert("L"))
        a = np.array(inv)
        txt = a > 128
        # upscale 2x by repeating to make art larger
        step = 1
        out = []
        for j in range(0, txt.shape[0], step):
            row = "".join("#" if txt[j, i] else " " for i in range(0, txt.shape[1], step)).rstrip()
            out.append(row)
        while out and not out[-1].strip():
            out.pop()
        print(f"\n### node {i}: center=({cx},{cy}) ###")
        print("\n".join(out))
    return nonce


if __name__ == "__main__":
    render_labels(sys.argv[1] if len(sys.argv) > 1 else None)