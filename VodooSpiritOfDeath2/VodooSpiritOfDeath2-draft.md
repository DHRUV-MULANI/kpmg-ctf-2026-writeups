# Vodoo Spirit of Death — 2 — Writeup (draft)

> **Superseded** — see the full writeup in [`VodooSpiritOfDeath2-writeup.md`](./VodooSpiritOfDeath2-writeup.md).

**"Get to root"** — ✅ SOLVED

| | |
|---|---|
| **Challenge** | Vodoo Spirit of Death - 2 (KPMG CTF) |
| **Points** | 10 |
| **Service** | `nc 0.cloud.chals.io 32779` → SSH |
| **Root path** | CVE‑2021‑3156 (Baron Samedit) via CptGibbon's deterministic PoC |
| **Root flag** | `KPMG_CTF{70uFWYXOQHHQyPDE-U8hnnosfwrCFhkFuANAqdZWo_9-}` |

## Status

* [x] Foothold: `maya.chen : Onboard-Maya25!` (leaked via exposed Redis in Part 1)
* [x] User flag: `KPMG_CTF{6cf60da16034c94ec03370ce6f90308c}`
* [x] Root: CVE‑2021‑3156 → `uid=0(root)` in one shot via `/run/lock/cpt/exploit`
