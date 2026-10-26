#!/usr/bin/env python3
"""Robust /verify solver v7.

- Parses the dynamic target name from the page.
- Locates the 6 node circles.
- Extracts each node's label (searching above AND below the circle).
- OCRs labels; finds node closest to the target (normalized match).
- Probes plausible click zones around the matched node; fallback to a small grid.
"""
import io, json, re, ssl, subprocess, sys, tempfile, os, time, math
from collections import deque
import numpy as np
import urllib.request
from PIL import Image, ImageOps

B = "https://kicyber-deea1f3c3f67-locks-of-confusion1-0-0.chals.io"
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
WHITELIST = "-c", "tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyz0123456789-"


def get(url):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
        return r.read()


def post(x, y, nonce):
    body = json.dumps({"nonce": nonce, "x": int(x), "y": int(y)}).encode()
    req = urllib.request.Request(B + "/verify/check", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
        return r.read().decode()


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


def text_bands(img, x0, x1, ytop, ybot):
    """Return list of (by0,by1,cols_min,cols_max) text bands in the given region."""
    reg = np.array(img.crop((max(x0, 0), max(ytop, 0), min(x1, 640), min(ybot, 360))).convert("L")).astype(int)
    light = reg > 130
    rowsum = light.sum(axis=1)
    bands = []
    start = None
    for j, v in enumerate(rowsum):
        if v >= 2 and start is None:
            start = j
        elif v < 2 and start is not None:
            if j - start >= 3:
                bands.append((start, j - 1))
            start = None
    if start is not None and len(rowsum) - start >= 3:
        bands.append((start, len(rowsum) - 1))
    out = []
    for by0, by1 in bands:
        band = light[by0:by1 + 1, :]
        cols = np.where(band.any(axis=0))[0]
        if not len(cols):
            continue
        out.append((max(ytop, 0) + by0, max(ytop, 0) + by1, max(x0, 0) + cols.min(), max(x0, 0) + cols.max() + 1))
    return out


def node_label(img, cx, cy, x0, y0, x1, y1):
    """Find the label band closest to the node centre, above or below."""
    cands = text_bands(img, x0 - 95, x1 + 95, y0 - 30, y0 - 2) + text_bands(img, x0 - 95, x1 + 95, y1 + 2, y1 + 30)
    if not cands:
        return None
    def dist(b):
        return abs((b[0] + b[1]) / 2 - cy)
    return min(cands, key=dist)


def ocr_crop(img, box):
    x0, y0, x1, y1 = box
    crop = img.crop((max(x0, 0), max(y0, 0), x1, y1))
    inv = ImageOps.invert(crop.convert("L"))
    inv = inv.resize((inv.width * 20, inv.height * 20), Image.NEAREST)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        inv.save(f.name); path = f.name
    res = {}
    try:
        for psm in ("8", "7", "13"):
            out = subprocess.run(["tesseract", path, "stdout", "--psm", psm, WHITELIST[0], WHITELIST[1]],
                                 capture_output=True, text=True).stdout.strip()
            res[psm] = out
    finally:
        os.unlink(path)
    return res


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def lev(a, b):
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def probe_points(cx, cy, x0, y0, x1, y1, label):
    pts = []
    pts.append((cx, cy))                       # circle centre
    if label:
        pts.append(((label[2] + label[3]) // 2, (label[0] + label[1]) // 2))  # label centre
        for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            pts.append(((label[2] + label[3]) // 2 + dx, (label[0] + label[1]) // 2 + dy))
        # corners of label bbox
        pts.append((label[2], label[0]))
        pts.append((label[3], label[0]))
        pts.append((label[2], label[1]))
        pts.append((label[3], label[1]))
    # ring around circle centre
    for r in (14, 20, 26, 32):
        for a in range(0, 360, 45):
            pts.append((cx + int(r * math.cos(math.radians(a))), cy + int(r * math.sin(math.radians(a)))))
    # between circle bottom and label
    ly = label[0] if label else y1 + 8
    for yy in range(y1 + 1, ly, 3):
        pts.append((cx - 8, yy)); pts.append((cx, yy)); pts.append((cx + 8, yy))
    # above circle
    for yy in range(max(0, y0 - 30), y0, 4):
        pts.append((cx, yy))
    return pts


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    for attempt in range(1, limit + 1):
        html = get(B + "/verify").decode()
        m = re.search(r'click the node\s*labeled <strong>([^<]+)</strong>', html)
        if not m:
            print("parse fail")
            return 1
        target = m.group(1).strip()
        nonce = re.search(r'var nonce = "([0-9a-f]+)"', html).group(1)
        src = re.search(r'src="(/verify/image/[0-9a-f]+)"', html).group(1)
        img = Image.open(io.BytesIO(get(B + src))).convert("RGB")
        arr = np.array(img).astype(int)
        mask = (np.abs(arr - np.array([18, 18, 18])).sum(axis=2) > 100)
        comps = components(mask, minn=300)
        nodes = []
        for x0, y0, x1, y1, n in comps:
            w, h = x1 - x0 + 1, y1 - y0 + 1
            if 250 <= n <= 4000 and 0.4 <= w / h <= 2.2:
                nodes.append((x0, y0, x1, y1, (x0 + x1) // 2, (y0 + y1) // 2))
        print(f"[{attempt}] target={target!r} nonce={nonce}")

        scored = []
        for x0, y0, x1, y1, cx, cy in nodes:
            lb = node_label(img, cx, cy, x0, y0, x1, y1)
            ocr = {}
            if lb:
                ocr = ocr_crop(img, (lb[2] - 2, lb[0] - 2, lb[3] + 2, lb[1] + 2))
            vals = [norm(v) for v in ocr.values() if v]
            best = min((lev(v, norm(target)), v) for v in vals) if vals else (99, "")
            scored.append((best[0], cx, cy, lb, best[1], ocr))
            print(f"    node ({cx},{cy}) label_bbox={lb} ocr={ocr} -> dist={best[0]} {best[1]!r}")

        scored.sort(key=lambda s: s[0])
        target_guess = scored[0]
        dist, cx, cy, lb, txt, ocr = target_guess
        # try the top candidates (up to 3)
        for cand in scored[:3]:
            dist, cx, cy, lb, txt, ocr = cand
            pts = probe_points(cx, cy, *(lambda n: (n))(nodes[0])) if False else None
            # find bbox
            nbox = None
            for nx0, ny0, nx1, ny1, ncx, ncy in nodes:
                if (ncx, ncy) == (cx, cy):
                    nbox = (nx0, ny0, nx1, ny1)
                    break
            x0, y0, x1, y1 = nbox
            pts = probe_points(cx, cy, x0, y0, x1, y1, lb)
            for x, y in pts:
                x = int(x); y = int(y)
                if not (0 <= x < 640 and 0 <= y < 360):
                    continue
                res = post(x, y, nonce)
                if '"ok":true' in res:
                    print(f"SUCCESS! attempt={attempt} target={target} node=({cx},{cy}) txt={txt!r} point=({x},{y})")
                    return 0
                time.sleep(0.05)
        print(f"    [{attempt}] probe failed; will retry next nonce")
        time.sleep(0.2)
    return 1


if __name__ == "__main__":
    sys.exit(main())