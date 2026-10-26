#!/usr/bin/env python3
"""Resilient recursive downloader for the flaky /pub/ SimpleHTTP server."""
import re, time, os, sys, urllib.request, ssl

BASE = "https://kicyber-e7d544a91579-lastwill-0-0.chals.io"
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0", "Accept": "*/*"}

def fetch(path, tries=6):
    url = BASE + path
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
                data = r.read()
            return r.status, data
        except Exception as e:
            time.sleep(3 + i * 2)
    return None, None

seen = set()
queue = ["/pub/"]

def walk(path):
    st, data = fetch(path)
    if data is None:
        print("FAIL", path)
        return
    print(f"{st} {len(data)} {path}")
    out = path.lstrip("/").replace("/", "_")
    with open(out, "wb") as f:
        f.write(data)
    if data[:5] == b"<!DOC" and b'<li><a href=' in data:
        for m in re.finditer(rb'href="([^"]+)"', data):
            href = m.group(1).decode()
            if href in ("../",):
                continue
            child = path.rstrip("/") + "/" + href
            if child not in seen:
                seen.add(child)
                queue.append(child)

while queue:
    p = queue.pop(0)
    walk(p)
print("done")