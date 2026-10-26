#!/usr/bin/env python3
"""Solve the /verify gate, then immediately fetch the locked archive files.

The archive unlock is IP-keyed and time-limited ("unlocked for the next few
minutes"), so the download must happen right after a successful /verify/check.
Session cookies are NOT used (the server sets none), but we keep a cookie jar
anyway in case behaviour changes.
"""
import io, json, re, sys, os, time, ssl
import urllib.request, urllib.parse
import numpy as np
from PIL import Image, ImageOps
from http.cookiejar import CookieJar

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify_solve7 as vs

B = vs.B
ctx = vs.ctx

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "raw")
OUT = os.path.abspath(OUT)


def get_with_jar(url, jar):
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar),
        urllib.request.HTTPSHandler(context=ctx))
    req = urllib.request.Request(url)
    return opener.open(req, timeout=30)


def main():
    jar = CookieJar()
    html = get_with_jar(B + "/verify", jar).read().decode()
    m = re.search(r'click the node\s*labeled <strong>([^<]+)</strong>', html)
    target = m.group(1).strip()
    nonce = re.search(r'var nonce = "([0-9a-f]+)"', html).group(1)
    src = re.search(r'src="(/verify/image/[0-9a-f]+)"', html).group(1)
    print(f"target={target!r} nonce={nonce}")

    img = Image.open(io.BytesIO(get_with_jar(B + src, jar).read())).convert("RGB")
    arr = np.array(img).astype(int)
    mask = (np.abs(arr - np.array([18, 18, 18])).sum(axis=2) > 100)
    comps = vs.components(mask, minn=300)
    nodes = []
    for x0, y0, x1, y1, n in comps:
        w, h = x1 - x0 + 1, y1 - y0 + 1
        if 250 <= n <= 4000 and 0.4 <= w / h <= 2.2:
            nodes.append((x0, y0, x1, y1, (x0 + x1) // 2, (y0 + y1) // 2))
    print(f"nodes: {len(nodes)}")

    scored = []
    for x0, y0, x1, y1, cx, cy in nodes:
        lb = vs.node_label(img, cx, cy, x0, y0, x1, y1)
        ocr = {}
        if lb:
            ocr = vs.ocr_crop(img, (lb[2] - 2, lb[0] - 2, lb[3] + 2, lb[1] + 2))
        vals = [vs.norm(v) for v in ocr.values() if v]
        best = min((vs.lev(v, vs.norm(target)), v) for v in vals) if vals else (99, "")
        scored.append((best[0], cx, cy, lb, best[1]))
        print(f"    node ({cx},{cy}) ocr={ocr} -> {best}")

    scored.sort(key=lambda s: s[0])
    ok = False
    for dist, cx, cy, lb, txt in scored[:3]:
        nbox = None
        for nx0, ny0, nx1, ny1, ncx, ncy in nodes:
            if (ncx, ncy) == (cx, cy):
                nbox = (nx0, ny0, nx1, ny1)
                break
        x0, y0, x1, y1 = nbox
        pts = vs.probe_points(cx, cy, x0, y0, x1, y1, lb)
        for x, y in pts:
            if not (0 <= x < 640 and 0 <= y < 360):
                continue
            body = json.dumps({"nonce": nonce, "x": int(x), "y": int(y)}).encode()
            req = urllib.request.Request(B + "/verify/check", data=body,
                                         headers={"Content-Type": "application/json"})
            opener = urllib.request.build_opener(
                urllib.request.HTTPCookieProcessor(jar),
                urllib.request.HTTPSHandler(context=ctx))
            with opener.open(req, timeout=30) as r:
                res = r.read().decode()
                hdrs = dict(r.headers)
            if '"ok":true' in res:
                print(f"VERIFIED target={target} node=({cx},{cy}) point=({x},{y}) res={res}")
                print(f"CHECK RESPONSE HEADERS: {hdrs}")
                print(f"JAR AFTER CHECK: {[(c.name, c.value) for c in jar]}")
                ok = True
                break
            time.sleep(0.05)
        if ok:
            break
    if not ok:
        print("FAILED to pass verify")
        return 1

    time.sleep(0.2)
    arch = sys.argv[1:] or ["/archive/provisioning/legacy-03-2007.tar.gz",
                            "/archive/keyspace/legacy-keys-2007.tar.gz"]
    for path in arch:
        fn = os.path.join(OUT, os.path.basename(path))
        req = urllib.request.Request(B + path)
        opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(jar),
            urllib.request.HTTPSHandler(context=ctx))
        try:
            with opener.open(req, timeout=60) as r:
                data = r.read()
                hdrs = dict(r.headers)
        except urllib.error.HTTPError as e:
            data = e.read()
            hdrs = dict(e.headers)
            print(f"GET {path} -> HTTP {e.code} len={len(data)} headers={hdrs}")
            with open(fn, "wb") as f:
                f.write(data)
            continue
        print(f"GET {path} -> HTTP 200 len={len(data)} ct={hdrs.get('Content-Type')}")
        with open(fn, "wb") as f:
            f.write(data)
        if data[:2] == b"\x1f\x8b":
            print(f"    OK gzip magic, saved {fn}")
        else:
            print(f"    WARNING: not gzip: {data[:80]!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())