#!/usr/bin/env python3
"""Click label bbox centres, circle centres, and in-between points for the
current nonce until the server accepts one."""
import io, json, re, ssl, sys, time
from collections import deque
import numpy as np
import urllib.request
from PIL import Image

B = "https://kicyber-deea1f3c3f67-locks-of-confusion1-0-0.chals.io"
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE


def http(url, data=None):
    req = urllib.request.Request(url, data=data)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
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


def main():
    html = http(B + "/verify").decode()
    nonce = re.search(r'var nonce = "([0-9a-f]+)"', html).group(1)
    src = re.search(r'src="(/verify/image/[0-9a-f]+)"', html).group(1)
    img = Image.open(io.BytesIO(http(B + src))).convert("RGB")
    arr = np.array(img).astype(int)
    mask = (np.abs(arr - np.array([18, 18, 18])).sum(axis=2) > 100)
    comps = components(mask, minn=300)
    nodes = []
    for x0, y0, x1, y1, n in comps:
        w, h = x1 - x0 + 1, y1 - y0 + 1
        if 250 <= n <= 4000 and 0.4 <= w / h <= 2.2:
            nodes.append((x0, y0, x1, y1, (x0 + x1) // 2, (y0 + y1) // 2))
    print("nonce", nonce)

    pts = []
    for x0, y0, x1, y1, cx, cy in nodes:
        lb = label_bbox(img, x0, x1, y1)
        lc = ((lb[0] + lb[2]) // 2, (lb[1] + lb[3]) // 2) if lb else (cx, y1 + 10)
        pts.append(("circle", cx, cy))
        pts.append(("label", lc[0], lc[1]))
        if lb:
            for fx, fy in ((0.25, 0.5), (0.75, 0.5), (0.5, 0.5), (0.3, 0.3), (0.7, 0.7)):
                pts.append(("labp", int(lb[0] + (lb[2] - lb[0]) * fx), int(lb[1] + (lb[3] - lb[1]) * fy)))
        pts.append(("below", cx, y1 + 12))
        pts.append(("top", cx, y0))
        print("node", (cx, cy), "label bbox", lb)

    def post(x, y):
        body = json.dumps({"nonce": nonce, "x": x, "y": y}).encode()
        try:
            return http(B + "/verify/check", body).decode()
        except Exception as e:
            return "ERR %s" % e

    seen = set()
    for kind, x, y in pts:
        x = int(x); y = int(y)
        k = (x, y)
        if k in seen:
            continue
        seen.add(k)
        res = post(x, y)
        print("click", kind, x, y, "->", res)
        time.sleep(0.05)
        if '"ok":true' in res:
            print("SUCCESS", kind, x, y)
            return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())