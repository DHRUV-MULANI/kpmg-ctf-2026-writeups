# TradeBot CTF Challenge - Technical Analysis & Investigation Summary

## 1. Challenge Overview

- **Challenge Name:** TradeBot
- **Category:** API / Web Security / Race Conditions / TOCTOU
- **Target URL:** `http://kicyber-ec28a209729d-tradebot-0-0.chals.io`
- **Challenge Description:**
  > *TradeBot is your automated stock trading assistant. Look up stock prices, browse the market, check your portfolio, and place buy and sell orders. There is a special instrument that isn't sold on the public order book. Only the settlement engine, the part that processes your trades, can read it.*
- **Given Hint:**
  > *"The engine decides whether it can settle your order before it finishes routing it and it never checks again."*

---

## 2. Reconnaissance & Architecture

### 2.1 Web Server & Protocol
- **Server:** FastAPI / Uvicorn (Python backend, using Pydantic v2.13 and FastMCP).
- **Interface:** Model Context Protocol (MCP) JSON-RPC 2.0 over HTTP Server-Sent Events (SSE).
- **Session Handshake:**
  - `POST /mcp` with `{"jsonrpc":"2.0","id":1,"method":"initialize",...}` returns an SSE stream with an assigned `mcp-session-id` header.
  - Subsequent tool calls send `mcp-session-id: <session_id>` header.

### 2.2 Available MCP Tools
Upon issuing `tools/list`, eight MCP tools were discovered:

| Tool Name | Parameters | Description |
|---|---|---|
| `get_stock_price` | `symbol: str` | Retrieves current price of a stock. |
| `get_stock_info` | `symbol: str` | Fetches stock profile and classification metadata. |
| `list_available_stocks` | *none* | Lists publicly traded assets (`AAPL`, `GOOGL`, `MSFT`, `AMZN`, `TSLA`). |
| `get_portfolio` | *none* | Returns available cash balance and current holdings. |
| `get_risk_report` | *none* | Exposes real-time settlement risk engine state. |
| `get_order_status` | `order_id: str` | Returns order details (`ORD-XXXXXX`). |
| `place_order` | `symbol: str`, `quantity: int`, `order_type: "buy"\|"sell"` | Submits order to settlement risk engine and exchange. |
| `health_check` | *none* | Service health probe. |

---

## 3. Key Findings

### 3.1 The Hidden Instrument (`FLAG`)
Probing `get_stock_info(symbol="FLAG")` revealed the restricted target:

```json
{
  "symbol": "FLAG",
  "name": "TradeBot Reserve Note",
  "sector": "Restricted",
  "classification": "RESTRICTED",
  "note": "Reserve vault instrument. Not tradable through the public order book; readable only by the settlement engine while a fill holds exclusive vault access."
}
```

When attempting public price lookup via `get_stock_price(symbol="FLAG")`:
> *"Symbol 'FLAG' is classified RESTRICTED and has no public quote. Reserve vault instruments are priced by the settlement engine only."*

When attempting `place_order(symbol="FLAG", quantity=1)`:
> Blocked at the API layer with a restriction notice.

### 3.2 Settlement Risk Engine Architecture (`get_risk_report`)
The risk engine exposes its internal operational constraints:
```json
{
  "max_concurrent_settlements": 19,
  "settlements_inflight": 0,
  "inflight_order_ids": [],
  "routing_latency_seconds": 1.0,
  "fill_latency_seconds": 0.8,
  "integrity_violations": 0
}
```

**Order Lifecycle:**
1. **Admission Check:** Engine verifies if `settlements_inflight < max_concurrent_settlements` (19 max).
2. **Routing Phase:** Takes `1.0s`. *(According to the hint: "The engine decides whether it can settle your order before it finishes routing it and it never checks again.")*
3. **Fill Phase:** Takes `0.8s`. Holds **exclusive vault access** during order execution.
4. **Completion:** Order transitions to `filled` or `rejected`.

---

## 4. Exploitation Vectors Explored

### 4.1 TOCTOU & Concurrency Testing
- **Double-Spending Proof of Concept:**
  - Sent concurrent sell orders for held positions (`AAPL`).
  - Successfully exploited the delay window, resulting in balance inflation (from ~$1,200 to >$25,000) and registering `integrity_violations: 2` on the settlement engine report.
  - Confirmed state race conditions are active on the backend.

### 4.2 Engine Saturation Testing
- Flooded the engine with 19 concurrent legitimate trades to max out capacity (`settlements_inflight == 19`).
- Submitted `FLAG` orders simultaneously to test if capacity pressure bypassed the symbol validation gate.
- Result: Symbol filter operates strictly before admission to the routing queue.

### 4.3 In-Flight Vault Inspection
- Evaluated the condition: *"readable only by the settlement engine while a fill holds exclusive vault access"*.
- While an active legitimate order is in the `0.8s` fill phase, the vault locks exclusively for the engine.
- Tested reading `get_stock_price("FLAG")` and `get_stock_info("FLAG")` precisely during the fill window of an active order.
- Tested edge case parameter types (negative quantities, floating points, batch JSON-RPC, SSE listener streams).

---

## 5. Next Steps & Recommended Path

1. **Vault Access Race Alignment:**
   - Launch an order with a known latency pattern (`AAPL` buy/sell).
   - Time parallel requests to `get_stock_price` or `get_order_status` during the exact `[1.0s, 1.8s]` window (during the 0.8s fill window where exclusive vault access is claimed).
2. **Order Modification / Parameter Pollution:**
   - Test if `place_order` accepts alternative parameters or undocumented routing directives.
3. **SSE Notification Stream Capture:**
   - Monitor the raw SSE event stream during multi-stage fills to capture broadcasted internal engine state or log emissions.
