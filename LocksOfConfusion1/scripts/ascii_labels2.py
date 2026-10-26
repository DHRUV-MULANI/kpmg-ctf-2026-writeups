#!/usr/bin/env python3
"""Improved label reader: tight crop, invert, thicken, upscale, OCR + ASCII."""
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


def ocr_file(path):
    res = {}
    for psm in ("7", "13", "6"):
        r = subprocess.run(["tesseract", path, "stdout", "--psm", psm],
                           capture_output=True, text=True).stdout.strip()
        res[psm] = r
    return res


def ascii_art(crop_pil, scale=4):
    arr = np.array(crop_pil.convert("L")).astype(int)
    txt = arr < 110  # white text on black after invert
    out = []
    H, W = txt.shape
    step = max(1, scale // 2)
    for j in range(0, H, step):
        row = []
        for i in range(0, W, step):
            blk = txt[j:j + step, i:i + step]
            row.append("#" if blk.mean() > 0.3 else " ")
        out.append("".join(row).rstrip())
    while out and not out[-1].strip():
        out.pop()
    while out and not out[0].strip():
        out.pop(0)
    return "\n".join(out)


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
        # scan down from below node for light pixels
        strip = img.crop((max(x0 - 70, 0), y1 + 1, x1 + 70, min(y1 + 50, img.height)))
        sarr = np.array(strip.convert("L")).astype(int)
        ys, xs = np.where(sarr > 130)
        if not len(xs):
            print(f"\n===== node {i} ({cx},{cy}): NO LABEL =====")
            continue
        # gather glyph components in strip and take their bbox
        glyph_mask = sarr > 130
        gcs = components(glyph_mask, minn=2)
        gx0 = min(c[0] for c in gcs); gx1 = max(c[2] for c in gcs)
        gy0 = min(c[1] for c in gcs); gy1 = max(c[3] for c in gcs)
        crop = img.crop((max(x0 - 70 + gx0 - 3, 0), y1 + 1 + gy0 - 3, max(x0 - 70 + gx0, 0) + gx1 - gx0 + 7, y1 + 1 + gy1 + 4))
        inverted = ImageOps.invert(crop.convert("L"))
        inverted = inverted.resize((inverted.width * 12, inverted.height * 12), Image.NEAREST)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            inverted.save(f.name); path = f.name
        try:
            o = ocr_file(path)
        finally:
            os.unlink(path)
        print(f"\n===== node {i}: center=({cx},{cy}) ASCII =====")
        print(ascii_art(crop, scale=4))
        print("OCR:", o)


if __name__ == "__main__":
    sys.exit(main())