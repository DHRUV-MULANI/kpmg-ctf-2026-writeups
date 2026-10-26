#!/usr/bin/env python3
"""Template-match the lb-02 label in the diagram for the current nonce, then click."""
import io, json, re, ssl, sys
from collections import deque
import numpy as np
import urllib.request
from PIL import Image, ImageDraw, ImageFont

B = "https://kicyber-deea1f3c3f67-locks-of-confusion1-0-0.chals.io"
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE


def http(url, data=None):
    req = urllib.request.Request(url, data=data)
    if data is not None:
        req.add_header("Content-Type", "application/json")
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


def extract_label_bitmap(img, x0, x1, y1):
    """Return binarized bitmap (True=text light pixels) of the label below node,
    found via row-band analysis."""
    strip = img.crop((max(x0 - 100, 0), y1 + 1, min(x1 + 100, 640), min(y1 + 40, 360)))
    sarr = np.array(strip.convert("L")).astype(int)
    light = sarr > 130
    # row profile
    rowsum = light.sum(axis=1)
    # find contiguous bands with >=2 light px
    bands = []
    start = None
    for j, v in enumerate(rowsum):
        if v >= 2 and start is None:
            start = j
        elif v < 2 and start is not None:
            if j - start >= 4:
                bands.append((start, j - 1))
            start = None
    if start is not None and len(rowsum) - start >= 4:
        bands.append((start, len(rowsum) - 1))
    if not bands:
        return None, None
    # label is the band closest to top of strip (just below the node)
    by0, by1 = min(bands, key=lambda b: (b[0], -(b[1] - b[0])))
    band = light[by0:by1 + 1, :]
    cols = np.where(band.any(axis=0))[0]
    if not len(cols):
        return None, None
    cols = np.arange(cols.min(), cols.max() + 1)
    return band[:, cols], (max(x0 - 100, 0) + cols.min(), y1 + 1 + by0)


def render_templates():
    """Render 'lb-02' with several plausible fonts/sizes -> list of bool bitmaps."""
    outs = []
    # PIL default font (TrueType DejaVu in modern Pillow), various sizes
    for size in (9, 10, 11, 12, 14):
        try:
            f = ImageFont.load_default(size)
        except TypeError:
            f = ImageFont.load_default()
        im = Image.new("L", (120, 60), 0)
        d = ImageDraw.Draw(im)
        d.text((2, 2), "lb-02", font=f, fill=255)
        a = np.array(im)
        a = a[a.sum(axis=1) > 0, :]
        a = a[:, a.sum(axis=0) > 0]
        outs.append((f"default{size}", a > 128))
    # try load default TrueType name
    for cand in ("DejaVuSans.ttf", "DejaVuSansMono.ttf", "LiberationSans-Regular.ttf",
                 "FreeSans.ttf", "Arial.ttf"):
        try:
            f = ImageFont.truetype(cand, 11 if "Mono" not in cand else 10)
            im = Image.new("L", (120, 60), 0)
            d = ImageDraw.Draw(im)
            d.text((2, 2), "lb-02", font=f, fill=255)
            a = np.array(im)
            a = a[a.sum(axis=1) > 0, :]
            a = a[:, a.sum(axis=0) > 0]
            outs.append((cand, a > 128))
        except OSError:
            pass
    return outs


def score(template, label):
    """Scale template to label height (or near), align on center, IoU + mdiff penalty."""
    t = template
    l = label
    best = -1
    th = t.shape[0]
    for target_h in range(int(th * 0.85), int(th * 1.2) + 1):
        if target_h <= 0:
            continue
        scaled = np.array(Image.fromarray((t * 255).astype(np.uint8)).resize(
            (max(1, int(t.shape[1] * target_h / th)), target_h), Image.LANCZOS)) > 128
        # try horizontal offsets
        for dx in range(-6, 7):
            # matched area = intersection of widths
            w = min(scaled.shape[1], l.shape[1] - dx if dx >= 0 else l.shape[1])
            # simpler: pad label or template to same width
            W = max(scaled.shape[1], l.shape[1]) + 4
            H = max(scaled.shape[0], l.shape[0])
            tb = np.zeros((H, W), bool)
            lb = np.zeros((H, W), bool)
            sx = max(0, -dx); lx = max(0, dx)
            tb[0:scaled.shape[0], sx:sx + min(scaled.shape[1], W - sx)] = scaled[:, :min(scaled.shape[1], W - sx)]
            lb[0:l.shape[0], lx:lx + min(l.shape[1], W - lx)] = l[:, :min(l.shape[1], W - lx)]
            inter = (tb & lb).sum()
            union = (tb | lb).sum() + 1e-6
            best = max(best, inter / union)
    return best


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

    tmpls = render_templates()
    print("templates:", [name for name, _ in tmpls])

    best_node_list = []
    for x0, y0, x1, y1, cx, cy in nodes:
        label, _ = extract_label_bitmap(img, x0, x1, y1)
        if label is None:
            print(f"node ({cx},{cy}): no label")
            continue
        sc = max(score(t, label) for _, t in tmpls)
        best_node_list.append((sc, cx, cy))
        print(f"node ({cx},{cy}): lb-02 template best IoU={sc:.3f}")

    best_node_list.sort(reverse=True)
    score0 = best_node_list[0][0] if best_node_list else 0
    # candidates: top scorer and any within 0.05
    cands = [(cx, cy) for s, cx, cy in best_node_list if s >= max(score0 - 0.05, 0.25)]
    print("candidates:", cands)
    for cx, cy in cands:
        body = json.dumps({"nonce": nonce, "x": cx, "y": cy}).encode()
        res = http(B + "/verify/check", body).decode()
        print("click", cx, cy, "->", res)
        if '"ok":true' in res:
            print("SUCCESS")
            return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())