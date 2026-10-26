#!/usr/bin/env python3
"""One-shot: fetch nonce+image, dump fine ASCII art of each node label,
then attempt clicks on nodes whose label looks like lb-02."""
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


def ascii_art(crop_pil, scale=3):
    arr = np.array(crop_pil.convert("L")).astype(int)
    txt = arr < 110
    out = []
    step = max(1, scale // 2)
    for j in range(0, txt.shape[0], step):
        row = []
        for i in range(0, txt.shape[1], step):
            blk = txt[j:j + step, i:i + step]
            row.append("#" if blk.mean() > 0.3 else " ")
        out.append("".join(row).rstrip())
    while out and not out[-1].strip():
        out.pop()
    while out and not out[0].strip():
        out.pop(0)
    return "\n".join(out)


def ocr_crop(img, box):
    x0, y0, x1, y1 = box
    crop = img.crop((max(x0,0), max(y0,0), x1, y1))
    inv = ImageOps.invert(crop.convert("L"))
    inv = inv.resize((inv.width * 12, inv.height * 12), Image.NEAREST)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        inv.save(f.name); path = f.name
    try:
        out = subprocess.run(["tesseract", path, "stdout", "--psm", "7",
                              "-c", "tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-"],
                             capture_output=True, text=True).stdout.strip()
    finally:
        os.unlink(path)
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
    cands = []
    for i, (x0, y0, x1, y1, cx, cy) in enumerate(sorted(nodes, key=lambda z: (z[1], z[0]))):
        strip = img.crop((max(x0 - 70, 0), y1 + 1, x1 + 70, min(y1 + 50, img.height)))
        sarr = np.array(strip.convert("L")).astype(int)
        ys, xs = np.where(sarr > 130)
        if not len(xs):
            print(f"node {i} ({cx},{cy}): NO LABEL")
            continue
        glyph_mask = sarr > 130
        gcs = components(glyph_mask, minn=2)
        gx0 = min(c[0] for c in gcs); gx1 = max(c[2] for c in gcs)
        gy0 = min(c[1] for c in gcs); gy1 = max(c[3] for c in gcs)
        ox = max(x0 - 70, 0) + gx0
        oy = y1 + 1 + gy0
        crop = img.crop((ox - 3, oy - 3, ox + gx1 - gx0 + 7, oy + gy1 - gy0 + 5))
        lab = ocr_crop(img, (ox - 3, oy - 3, ox + gx1 - gx0 + 7, oy + gy1 - gy0 + 5))
        print(f"\nnode {i} center=({cx},{cy}) OCR={lab!r}\n" + ascii_art(crop, scale=3))
        if norm(lab) in ("lb02",) or ("lb" in norm(lab)) or ("1bh02" in norm(lab)) or ("leb02" in norm(lab)):
            cands.append((cx, cy))
        # also if OCR has both an l-ish and ends 02
        nl = norm(lab)
        if nl.endswith("02") and ("lb" in nl or "1b" in nl or "1bh" in nl or "leb" in nl or "ndb" in nl or "dbl" in nl):
            cands.append((cx, cy))
    # Try candidates, plus fall back to every node
    print("\ncandidates:", cands)
    trial = list(dict.fromkeys(cands + [(c[4], c[5]) for c in nodes]))
    for x, y in trial:
        body = json.dumps({"nonce": nonce, "x": x, "y": y}).encode()
        res = http(B + "/verify/check", data=body, headers={"Content-Type": "application/json"}).decode()
        print("click", x, y, "->", res)
        if '"ok":true' in res:
            print("SUCCESS")
            return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())