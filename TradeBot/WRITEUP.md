# TradeBot — KPMG K!Cyber CTF 2026 — API Challenge (20 pts)

## Flag

```
KPMG_CTF{O_YU0ekuwGw6DQrzqfo3wExRMZdAiU1I-OR3CAebtGbf}
```

- **Target:** `https://kicyber-ec28a209729d-tradebot-0-0.chals.io` (MCP endpoint `/mcp`)
- **Category:** Web/API — Race condition (TOCTOU) on the settlement risk engine
- **Difficulty:** the challenge’s whole point is that the engine decides "can I
  settle this order?" *before* routing and **never re-checks**.

---

## 1. Challenge text & hint

> TradeBot is your automated stock trading assistant. Look up stock prices,
> browse the market, check your portfolio, and place buy and sell orders. There
> is a special instrument that isn't sold on the public order book. **Only the
> settlement engine, the part that processes your trades, can read it.**
>
> Hint: **The engine decides whether it can settle your order before it finishes
> routing it and it never checks again.**

---

## 2. What the target is

The endpoint is a **Model Context Protocol (MCP)** server over HTTP
(Streamable-HTTP / SSE flavour), i.e. JSON-RPC 2.0. All interaction happens by
`POST /mcp` with an `initialize` handshake followed by `tools/call`, plus a
session id (`mcp-session-id` header) per connection.

Server banners are inconsistent (`/health` → `tradebot 2.0.0`, `initialize` →
`TradeBot 4.0.3`), which hints that the MCP server version was fragmented /
pulled apart – i.e. the "engine" is a separate conceptual component.

### Tools exposed (8)

| Tool | Params |
|---|---|
| `get_stock_price` | `symbol` |
| `get_stock_info` | `symbol` |
| `list_available_stocks` | – |
| `get_portfolio` | – |
| `get_risk_report` | – |
| `get_order_status` | `order_id` |
| `place_order` | `symbol, quantity, order_type` (`buy`/`sell`) |
| `health_check` | – |

### The hidden instrument

```json
get_stock_info("FLAG")
→ {"symbol":"FLAG","name":"TradeBot Reserve Note","sector":"Restricted",
   "classification":"RESTRICTED",
   "note":"Reserve vault instrument. Not tradable through the public order book;
          readable only by the settlement engine while a fill holds exclusive
          vault access."}
```

- `get_stock_price("FLAG")` → *"...RESTRICTED and has no public quote…"*
- `place_order("FLAG", buy/sell)` → *"…classified RESTRICTED… Vault access is
  granted only to the settlement engine."*

### Settlement engine shape (`get_risk_report`)

```json
{"max_concurrent_settlements":19, "settlements_inflight":0, "inflight_order_ids":[],
 "routing_latency_seconds":1.0, "fill_latency_seconds":0.8, "integrity_violations":0}
```

Normal order lifecycle:

| Phase | Duration | `settlements_inflight` |
|---|---|---|
| API admission | ~0 ms | 0 |
| Routing | 1.0 s | 0 |
| Fill (holds "exclusive vault access") | 0.8 s | **counts** |
| Response | ~2.2 s total | 0 |

---

## 3. Recon notes (what was ruled out)

- **Symbol bypass:** `.upper()` applied before checks – `flag`, `FlAg`, ligature
  `ﬂag`, fullwidth/zero-width/whitespace variants all either rejected as
  RESTRICTED or `not found`. No SSTI/SQLi/path-traversal on `symbol`/`order_id`.
- **Hidden surface:** brute of ~40 tool names, ~9 prompt names, JSON-RPC methods
  (`vault/*`, `engine/*`, `flag/*`), resource URIs (`vault://`, `file://`, …).
  Only resource is `portfolio://status`. No prompts. Batch JSON-RPC rejected.
  No hidden HTTP paths beyond `/health` + `/mcp`.
- **Headers/auth roles:** `X-Role: engine`, `X-Settlement-Engine`,
  `X-Forwarded-For`, `Authorization` → no effect.
- **Order-then-flag mixing:** racing AAPL/MSFT/GOOGL/TSLA orders produced **no**
  cross-contamination of symbol/price → not a shared "current order" global
  inside the engine.
- **In-flight order state:** `get_order_status` only knows completed orders
  (id not visible until fill completes) → no intermediate leak.
- **Server→client requests:** advertised `sampling`/`elicitation` capabilities
  and inspected raw SSE bodies – the server never sends requests to the client.

---

## 4. Vulnerability — settlement TOCTOU / oversubscription

The admission check enforces a global cap:

- **`max_concurrent_settlements = 19`** – at most 19 orders may be *settling*
  concurrently.
- The check "can this order settle?" is evaluated **once, when routing starts**
  (t≈0).
- Routing takes 1.0 s; the fill (which acquires "exclusive vault access")
  happens at t≈1.0–1.8 s. **The engine never re-checks at fill time.**

Consequence: if N > 19 orders are all submitted fast enough to pass admission
before any fill starts, **all** of them will fill concurrently. `settlements_inflight`
grows past 19, `integrity_violations` climbs, and the "exclusive vault access"
invariant is broken.

### The leak

When ≥ 20 settlements hold a slot at the same time, the engine notices the
violation, marks the risk engine **COMPROMISED / SETTLEMENT_OVERSUBSCRIPTION**
and "reconciles by returning the sealed vault record" — **attached to the order
response**:

```json
{
  "order":       {"order_id":"ORD-000174","symbol":"AAPL","type":"sell","quantity":1,
                  "price":178.15,"total":178.15,"status":"filled","timestamp":...},
  "status":      "success",
  "risk_engine": {"integrity":"COMPROMISED","incident":"SETTLEMENT_OVERSUBSCRIPTION"},
  "vault_reconciliation": {
    "vault":     "TRADEBOT-RESERVE",
    "instrument":"TRADEBOT-RESERVE-NOTE",
    "integrity": "COMPROMISED",
    "reason":    "Settlement exclusivity violated: the reserve vault was read while
                  more than one settlement held a slot. Reconciling by returning
                  the sealed vault record.",
    "vault_seal":"KPMG_CTF{O_YU0ekuwGw6DQrzqfo3wExRMZdAiU1I-OR3CAebtGbf}"
  }
}
```

The **`vault_seal`** is the flag.

Bonus: the same TOCTOU also allows double-spending — the position/balance check
is also admission-time only, so the same held shares can be sold over and over
concurrently (observed balance inflation while `integrity_violations` climbed).

---

## 5. Exploit (`solve.py`, `flag_leak.py`)

Prerequisites per run:

1. Hold enough AAPL so the (admission-time) SELL position check passes:
   `place_order(AAPL, qty, buy)` until position ≥ #concurrent sells.
2. Open one MCP session per concurrent order (the server tolerates ~24; >~30
   starts dropping connections).
3. Fire `place_order(AAPL, 1, sell)` from **all** sessions through a threading
   barrier so all requests arrive at the same instant (all pass admission, all
   fill at t≈1.0s → inflight ≥ 20).
4. Read the leaked `vault_reconciliation.vault_seal` from any response.

```bash
python3 solve.py 22        # 22 concurrent sells  → flag leaked
python3 flag_leak.py 22    # minimal version
```

Verified stable across runs (same `KPMG_CTF{…}` on each leak).

---

## 6. Reproduction (minimal, step by step)

```
1. POST /mcp  initialize            → get mcp-session-id
2. tools/call place_order AAPL 22 buy   → position 22 AAPL
3. open 22 MCP sessions
4. thread barrier → 22 × tools/call place_order AAPL 1 sell
5. at least one response contains:
     "integrity":"COMPROMISED", "incident":"SETTLEMENT_OVERSUBSCRIPTION"
     "vault_reconciliation": { ..., "vault_seal":"KPMG_CTF{...}" }
```

---

## 7. Files in `TradeBot/`

| File | Purpose |
|---|---|
| `solve.py` | **Final exploit** – buys inventory, fires 22 concurrent sells, prints the flag |
| `flag_leak.py` | Saturation run that captures the full vault reconciliation |
| `mcpclient.py` | Minimal MCP-over-HTTP client (handshake + `tools/call`) |
| `burst_inspect.py` | Concurrent burst; inspected every response for contamination |
| `sat2.py`, `sat3.py` | Saturation harnesses (capacity bypass, integrity_violations) |
| `race1.py`, `race_double.py`, `race_mix.py`, `race_saturate.py`, `cross_test.py` | Race / double-spend / contamination tests |
| `test_precise.py`, `focus1.py`, `poll_order.py` | Fill-window probes (in-flight order state) |
| `recon2.py`, `recon3.py`, `recon4.py`, `recon5.py` | Hidden tools/methods/prompts/headers/paths brute |
| `probe1.py`, `probe2.py`, `probe_symbols.py`, `inj.py`, `iso.py` | Input validation / injection / case-folding probes |
| `explore.py`, `explore2.py`, `sessions.py`, `sse.py`, `timing.py` | Surface enumeration, session sharing, phase timing |
| `capture_raw.py`, `enum_orders.py` | Raw SSE capture, order-id enumeration |

---

## 8. Remediation (for the challenge author / product side)

- Re-validate admission guarantees **atomically at fill time** (instrument
  tradability, capacity, position/balance), not at routing start.
- Use a real mutex/semaphore for vault ("reserve") access; the count must hold
  for the whole settlement window, and violations must not dump otherwise-sealed
  vault records into client-visible responses.
- Never attach `vault_reconciliation` / sealed instrumentation data to ordinary
  order responses.