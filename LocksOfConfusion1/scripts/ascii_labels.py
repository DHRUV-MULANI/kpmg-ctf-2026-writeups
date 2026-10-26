#!/usr/bin/env python3
"""Debug: print each node's label as ASCII art to read lb-02 by eye."""
import io, json, re, ssl, sys
from collections import deque
import numpy as np
import urllib.request
from PIL import Image

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


def ascii_art(im, box, scale=8):
    x0, y0, x1, y1 = box
    crop = im.crop((max(x0, 0), max(y0, 0), x1, y1))
    arr = np.array(crop.convert("L")).astype(int)
    # text is light on dark -> threshold
    txt = arr > 140
    H, W = txt.shape
    lines = []
    for j in range(0, H, max(1, scale // 2)):
        row = []
        for i in range(0, W, scale // 2):
            block = txt[j:j + max(1, scale // 2), i:i + max(1, scale // 2)]
            row.append("#" if block.mean() > 0.25 else " ")
        lines.append("".join(row).rstrip())
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines) if lines else "(empty)"


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
        if 400 <= n <= 3600 and 0.55 <= w / h <= 1.8:
            nodes.append((x0, y0, x1, y1, (x0 + x1) // 2, (y0 + y1) // 2))
    print("nonce", nonce)
    for i, (x0, y0, x1, y1, cx, cy) in enumerate(sorted(nodes, key=lambda z: (z[1], z[0]))):
        print(f"\n===== node {i}: center=({cx},{cy}) x=[{x0},{x1}] y=[{y0},{y1}] =====")
        # find label below the node: light pixels in y range [y1, y1+45], x range [x0-60, x1+60]
        strip = img.crop((max(x0 - 60, 0), y1 + 1, x1 + 60, min(y1 + 45, img.height)))
        sarr = np.array(strip.convert("L")).astype(int)
        ys, xs = np.where(sarr > 140)
        if len(xs):
            bx0, bx1 = xs.min(), xs.max()
            by0, by1 = ys.min(), ys.max()
            print(ascii_art(img, (max(x0 - 60, 0) + bx0, y1 + 1 + by0, max(x0 - 60, 0) + bx0 + bx1 - bx0 + 1, y1 + 1 + by1), scale=6))
        else:
            print("(no label found below)")


if __name__ == "__main__":
    sys.exit(main())