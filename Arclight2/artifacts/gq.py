#!/usr/bin/env python3
import json, sys, urllib.request

BASE = "https://kicyber-c3b255e0db87-arclight2-0-0.chals.io"
COOKIE = "session=eyJyb2xlIjoic3RhbmRhcmQiLCJ1c2VybmFtZSI6ImhheDIifQ.asr6LA.qIqZB6sE6vJut1itU-LLJgLFzzg"

def gql(query, cookie=COOKIE):
    data = json.dumps({"query": query}).encode()
    h = {"Content-Type": "application/json"}
    if cookie:
        h["Cookie"] = cookie
    req = urllib.request.Request(BASE + "/graphql", data=data, headers=h)
    try:
        r = urllib.request.urlopen(req, timeout=20)
        return r.read().decode()
    except Exception as e:
        return "ERR: " + str(e)

if __name__ == "__main__":
    for q in sys.argv[1:]:
        print("--- " + q)
        print(gql(q))
        print()
