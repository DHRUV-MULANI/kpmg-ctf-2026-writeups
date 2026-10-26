#!/usr/bin/env python3
"""Full inventory of one diagram: all text OCR + all small shapes, to find lb-02."""
import io, re, ssl, subprocess, sys, tempfile, os
from collections import deque, Counter
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
    img = Image.open(io.BytesIO(http(B + src))).convert("RGB")
    arr = np.array(img).astype(int)
    print("nonce", nonce)

    inv = ImageOps.invert(img.convert("L"))
    big = inv.resize((inv.width * 8, inv.height * 8), Image.NEAREST)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        big.save(f.name); path = f.name
    try:
        tsv = subprocess.run(["tesseract", path, "stdout", "--psm", "11", "tsv"],
                             capture_output=True, text=True).stdout
    finally:
        os.unlink(path)
    print("--- OCR words (orig coords) ---")
    for line in tsv.splitlines()[1:]:
        p = line.split("\t")
        if len(p) >= 12 and p[11].strip():
            x, y, w, h = int(p[6]) / 8, int(p[7]) / 8, int(p[8]) / 8, int(p[9]) / 8
            if 0 <= x <= 640:
                print(f"  {p[11].strip():14s} x={x:6.1f} y={y:6.1f} w={w:4.1f} h={h:4.1f} conf={p[10]}")

    print("--- shapes (non-bg components area>=6) ---")
    mask = (np.abs(arr - np.array([18, 18, 18])).sum(axis=2) > 60)
    comps = sorted(components(mask, minn=6), key=lambda c: c[4])
    small = []
    for x0, y0, x1, y1, n in comps:
        if n >= 2000:
            print(f"  BIG shape area={n} x=[{x0},{x1}] y=[{y0},{y1}]")
        elif n >= 50:
            print(f"  med shape area={n} x=[{x0},{x1}] y=[{y0},{y1}] w={x1-x0+1} h={y1-y0+1}")
        else:
            small.append((x0, y0, x1, y1, n))
    print(f"  small shapes ({len(small)}): ", small[:40])


if __name__ == "__main__":
    sys.exit(main())