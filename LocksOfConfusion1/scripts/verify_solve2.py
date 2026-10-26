#!/usr/bin/env python3
"""Solver for /verify gate v2.

Handles randomized diagram: download the image tied to the nonce, locate the
node *directly above* the OCR label "lb-02", click its center.
"""
import io, json, re, ssl, subprocess, sys, tempfile, os
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


def components(mask, minn=10):
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
            if len(xs) >= minn:
                out.append((min(xs), min(ys), max(xs), max(ys), len(xs)))
    return out


def ocr_crop(im, box):
    x0, y0, x1, y1 = box
    crop = im.crop((max(x0,0), max(y0,0), x1, y1))
    crop = crop.resize((crop.width * 8, crop.height * 8), Image.LANCZOS)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        crop.save(f.name)
        path = f.name
    try:
        out = subprocess.run(["tesseract", path, "stdout", "--psm", "7",
                              "digits_and_letters" if False else ""],
                             capture_output=True, text=True).stdout
        # plain psm7
        out = subprocess.run(["tesseract", path, "stdout", "--psm", "7"],
                             capture_output=True, text=True).stdout
    finally:
        os.unlink(path)
    return out.strip()


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def main():
    html = http(B + "/verify").decode()
    nonce = re.search(r'var nonce = "([0-9a-f]+)"', html).group(1)
    src = re.search(r'src="(/verify/image/[0-9a-f]+)"', html).group(1)
    img = Image.open(io.BytesIO(http(B + src))).convert("RGB")
    arr = np.array(img).astype(int)

    # non-background mask
    bg = np.array([18, 18, 18])
    mask = (np.abs(arr - bg).sum(axis=2) > 100)
    comps = components(mask, minn=300)
    # keep shapes that look like node circles (fill ~2000px, roughly square)
    nodes = []
    for x0, y0, x1, y1, n in comps:
        w, h = x1 - x0 + 1, y1 - y0 + 1
        if 400 <= n <= 3600 and 0.55 <= w / h <= 1.8:
            nodes.append((x0, y0, x1, y1, (x0 + x1) // 2, (y0 + y1) // 2, n))
    print("nonce", nonce, "src", src.split('/')[-1])
    print("nodes (x0,y0,x1,y1,cx,cy,n):")
    for n_ in nodes:
        print("  ", n_)

    # For each node, OCR the strip just below it (and centered) to label it
    for x0, y0, x1, y1, cx, cy, n in nodes:
        strip = (cx - 60, y1, cx + 60, y1 + 40)
        lab = ocr_crop(img, strip)
        print("node at", (cx, cy), "label strip OCR ->", repr(lab))

    # Find whichever strip OCRs as lb-02 (tolerant)
    for x0, y0, x1, y1, cx, cy, n in nodes:
        strip = (cx - 60, y1, cx + 60, y1 + 40)
        lab = ocr_crop(img, strip)
        if norm(lab) in ("lb02", "1b02") or "lb" in norm(lab):
            print("MATCHED lb-02 -> node center", (cx, cy))
            body = json.dumps({"nonce": nonce, "x": cx, "y": cy}).encode()
            res = http(B + "/verify/check", data=body,
                       headers={"Content-Type": "application/json"}).decode()
            print("click", cx, cy, "->", res)
            return 0
    print("no match")
    return 1


if __name__ == "__main__":
    sys.exit(main())