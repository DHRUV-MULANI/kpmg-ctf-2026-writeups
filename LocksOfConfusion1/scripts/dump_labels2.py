#!/usr/bin/env python3
"""Extract label glyphs only (exclude connector lines) and render ASCII art."""
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


def components(mask, minn=1):
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
        strip = img.crop((max(x0 - 90, 0), y1 + 1, x1 + 90, min(y1 + 40, img.height)))
        sarr = np.array(strip.convert("L")).astype(int)
        light = sarr > 130
        gcs = components(light, minn=2)
        # glyphs: within label-like height
        glyphs = [c for c in gcs if 4 <= (c[3] - c[1] + 1) <= 10 and 1 <= (c[2] - c[0] + 1) <= 8 and c[4] < 80]
        if not glyphs:
            print(f"\n### ({cx},{cy}): NO LABEL GLYPHS ###")
            continue
        gx0 = min(c[0] for c in glyphs); gx1 = max(c[2] for c in glyphs)
        gy0 = min(c[1] for c in glyphs); gy1 = max(c[3] for c in glyphs)
        ox = max(x0 - 90, 0); oy = y1 + 1
        crop = img.crop((ox + gx0 - 2, oy + gy0 - 2, ox + gx1 + 3, oy + gy1 + 3))
        a = np.array(ImageOps.invert(crop.convert("L")))
        txt = a > 128
        lines = ["".join("#" if txt[j, i] else " " for i in range(txt.shape[1])).rstrip()
                 for j in range(txt.shape[0])]
        while lines and not lines[-1].strip():
            lines.pop()
        print(f"\n### center=({cx},{cy}) ###")
        print("\n".join(lines))

    return nonce


if __name__ == "__main__":
    sys.exit(main())