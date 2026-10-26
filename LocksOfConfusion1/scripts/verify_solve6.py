#!/usr/bin/env python3
"""Full /verify solver: parse dynamic target, OCR the 6 node labels, click the
node whose label matches the target."""
import io, json, re, ssl, subprocess, sys, tempfile, os, time
from collections import deque
import numpy as np
import urllib.request
from PIL import Image, ImageOps

B = "https://kicyber-deea1f3c3f67-locks-of-confusion1-0-0.chals.io"
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE


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


def label_bbox(img, x0, x1, y1):
    strip = np.array(img.crop((max(x0 - 120, 0), y1 + 1, min(x1 + 120, 640), min(y1 + 22, 360))).convert("L")).astype(int)
    light = strip > 130
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
    if not bands:
        return None
    by0, by1 = min(bands, key=lambda b: (b[0], -(b[1] - b[0])))
    band = light[by0:by1 + 1, :]
    cols = np.where(band.any(axis=0))[0]
    if not len(cols):
        return None
    ox = max(x0 - 120, 0)
    return (ox + cols.min(), y1 + 1 + by0, ox + cols.max() + 1, y1 + 1 + by1 + 1)


def ocr_crop(img, box):
    x0, y0, x1, y1 = box
    crop = img.crop((max(x0, 0), max(y0, 0), x1, y1))
    inv = ImageOps.invert(crop.convert("L"))
    inv = inv.resize((inv.width * 14, inv.height * 14), Image.NEAREST)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        inv.save(f.name); path = f.name
    opts = ["-c", "tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyz0123456789-"]
    res = {}
    try:
        for psm in ("7", "8", "13"):
            out = subprocess.run(["tesseract", path, "stdout", "--psm", psm] + opts,
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


def main():
    tries = 0
    while tries < 12:
        tries += 1
        html = get(B + "/verify").decode()
        m = re.search(r'click the node\s*labeled <strong>([^<]+)</strong>', html)
        if not m:
            print("could not parse target")
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
        print(f"[{tries}] target={target!r} nonce={nonce} nodes={len(nodes)}")

        scored = []
        for x0, y0, x1, y1, cx, cy in nodes:
            lb = label_bbox(img, x0, x1, y1)
            if not lb:
                scored.append((99, cx, cy, ""))
                continue
            ocr = ocr_crop(img, lb)
            ocrvals = [norm(v) for v in ocr.values() if v]
            best = min((lev(v, norm(target)), v) for v in ocrvals) if ocrvals else (99, "")
            scored.append((best[0], cx, cy, best[1], ocr))
            print(f"    node ({cx},{cy}) bbox={lb} ocr={ocr} -> dist={best[0]} text={best[1]!r}")

        scored.sort(key=lambda s: s[0])
        # try candidate nodes in ascending distance order; click multiple points
        tried = set()
        ok = False
        for dist, cx, cy, txt, ocr in scored:
            lb = label_bbox(img, *[nodes[i][2+ (0 if True else 0)] for i in range(0)])  # noop
            lbbox = None
            for nx0, ny0, nx1, ny1, ncx, ncy in nodes:
                if (ncx, ncy) == (cx, cy):
                    lbbox = label_bbox(img, nx0, nx1, ny1)
            cands = [(cx, cy)]
            if lbbox:
                cands.append(((lbbox[0] + lbbox[2]) // 2, (lbbox[1] + lbbox[3]) // 2))
                for fx, fy in ((0.5, 0.35), (0.35, 0.5), (0.65, 0.5)):
                    cands.append((int(lbbox[0] + (lbbox[2] - lbbox[0]) * fx),
                                  int(lbbox[1] + (lbbox[3] - lbbox[1]) * fy)))
            for x, y in cands:
                k = (x, y)
                if k in tried:
                    continue
                tried.add(k)
                res = post(x, y, nonce)
                print(f"    click ({x},{y}) -> {res}")
                time.sleep(0.08)
                if '"ok":true' in res:
                    print("SUCCESS node", (cx, cy), "txt", txt, "target", target)
                    return 0
        print(f"    [{tries}] failed this nonce")
        time.sleep(0.3)
    return 1


if __name__ == "__main__":
    sys.exit(main())