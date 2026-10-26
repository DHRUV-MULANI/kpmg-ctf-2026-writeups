# Last Will — CTF Writeup

**Category:** IoT / ICS / MQTT
**Points:** 20
**Event:** KPMG Cyber 2026 (kicyber)

## Challenge Description

> GreenLeaf migrated its plant telemetry to an old protocol based IIoT gateway last
> quarter. The contractor who set it up left the engagement early, ops has been finding
> undocumented pieces of the deployment ever since, and nobody's fully sure what's still
> running out there. You've been given network access to the plant's environment. Find the flag!

**Targets:**
- Web Portal: `https://kicyber-e7d544a91579-lastwill-0-0.chals.io`
- Plant Gateway: `0.cloud.chals.io:16792`

## TL;DR

1. `0.cloud.chals.io:16792` is an **MQTT broker** (pre-3.1.1 CONNECT/CONNACK handshake succeeds). The web "login" portal is a decoy, but a hidden `/pub/` archive on it leaks the whole story.
2. A `/pub/backups/notes.txt` explainer says MQTT wildcard `#` **skips `$`-prefixed topics**, and that a **duplicate client ID bumps the existing client** and fires an "unexpected disconnect". A startup log shows the gateway **set its Last Will on `plant/gateway/heartbeat_lost`**.
3. Subscribing to the exact `$internal/...` branch reveals `$internal/gateway/registry → {"primary_device": "gateway01"}` — the gateway's client ID.
4. Connecting a second MQTT client with `client_id="gateway01"` kicks the real gateway; the broker publishes its **Last Will** to `plant/gateway/heartbeat_lost`, which is a base64 blob that decodes to the flag.

**Flag:** `KPMG_CTF{iB-dprsBT6ScaXHwOjWkkNWBr4VXpCe0u9HOn-rPLxN2}`

---

## Step 1 — Reconnaissance & port discovery

* `nmap -sV -Pn -p 16792 0.cloud.chals.io` → port open, service unknown.
* A raw MQTT 3.1.1 CONNECT on the port returns a valid CONNACK:

```
sent   : 101000044d51545404020000000474657374
recv   : 20020000            (ACK, return code 0x00 = Connection Accepted)
```

So the Plant Gateway is an **MQTT broker**. The web portal is a "Gateway Access Portal"
login page whose submit handler simply shows "Invalid username or password" (pure
client-side decoy — there is no real auth backend).

## Step 2 — MQTT wildcard enumeration

Subscribing to `#` (all topics) yields only live sensor telemetry — a constant stream:

```
plant/sensors/tank1/level          80.6
plant/sensors/tank2/level          84.9
plant/sensors/pump2/rpm            2713.3
plant/sensors/pump4/rpm            2710.9
plant/sensors/compressor1/pressure 103.1
plant/sensors/valve3/state         open
```

No retained messages, no `$SYS/#` output. Nothing interesting — the flag is hidden elsewhere.

## Step 3 — Web portal `robots.txt` and the `/pub/` archive

`GET /robots.txt`:

```
User-agent: *
Disallow: /pub/
```

Following the disallowed path reveals a **SimpleHTTP directory listing** with a
"Plant Historian Archive":

```
/pub/
  backups/
    config_backup_2024.txt
    notes.txt
  docs/
    network_diagram_old.txt
  logs/
    gateway_startup.log
  README.txt
```

Two files are the *real* intel:

**`/pub/backups/notes.txt`** (contractor notes):

> Reminder to self: the internal diagnostics branch doesn't show up on a normal full
> subscribe. Smthn about how MQTT treats topics starting with a certain character as
> broker reserved and skips them on wildcard matches. Have to ask for the "internal"
> branch by its exact name if I want to see it.
>
> Also, ops flagged this again: whenever a second device boots up using the same client
> ID as one that's already connected, the broker kicks the original off without warning,
> and it fires an "unexpected disconnect" alert downstream. Annoying race condition,
> haven't had time to fix it. Don't spin up a duplicate client ID unless you mean to
> bump whatever's already using it.

Two MQTT facts to exploit:
1. **`$`-prefixed topics are not matched by wildcards** — the internal diagnostics branch lives under a `$` namespace and must be subscribed to by its exact name.
2. **Duplicate client ID → the old client is kicked** → its **Last Will and Testament** (MQTT LWT) fires.

**`/pub/logs/gateway_startup.log`** confirms the LWT topic:

```
2024-03-15 06:00:12 [INFO] Last Will set on plant/gateway/heartbeat_lost
```

## Step 4 — Discovering the `$internal` branch and device client ID

Because `#` skips reserved `$` topics, we subscribe to the likely internal branch names
explicitly (`$internal/#`, `$diag/#`, `$diagnostics/#`, `$sys/#`, ...). One retained
message appears:

```
$internal/gateway/registry  (retain) → {"primary_device": "gateway01"}
```

So the gateway's MQTT **client ID is `gateway01`**.

## Step 5 — Bumping the gateway and forcing its Last Will

Attack: connect a second MQTT client using `client_id = "gateway01"` while a watcher
subscribes to `plant/gateway/heartbeat_lost`. The broker instantly disconnects the real
gateway and fires its Last Will:

```
[watcher] connected Success
[*] connected as gateway01 (bumped real gateway)
[watcher MSG] plant/gateway/heartbeat_lost retain=False:
    S1BNR19DVEZ7aUItZHByc0JUNlNjYVhId09qV2trTldCcjRWWHBDZTB1OUhPbi1yUEx4TjJ9
```

The payload is base64:

```
$ echo S1BNR19DVEZ7aUItZHByc0JUNlNjYVhId09qV2trTldCcjRWWHBDZTB1OUhPbi1yUEx4TjJ9 | base64 -d
KPMG_CTF{iB-dprsBT6ScaXHwOjWkkNWBr4VXpCe0u9HOn-rPLxN2}
```

## Flag

```
KPMG_CTF{iB-dprsBT6ScaXHwOjWkkNWBr4VXpCe0u9HOn-rPLxN2}
```

---

## Root Cause / Real-World Lesson

This challenge models a classic **insecure IIoT/OT deployment**:

- **Undocumented / public-accessible artifacts** — a contractor archive (`/pub/`) left
  on a web server containing notes, logs and config that reveal fleet internals
  (an OSINT-style information-disclosure foothold).
- **Hiding data with MQTT's `$` reserved-topic rule** instead of proper ACLs — the
  internal diagnostics branch was "hidden" only because `$` topics are skipped by
  wildcard subscriptions; anyone who knows (or leaks) the exact topic name can read it.
- **No client-ID authentication / broker default behavior** — MQTT brokers treat
  client IDs as session identity. Any remote client can **impersonate a device ID** and
  force the legitimate device offline (session hijack / device spoofing), which triggers
  the device's **Last Will and Testament** — publishing whatever the (misconfigured)
  device configured, here the flag.
- MQTT **Last Will and Testament (LWT)** is a genuinely useful liveness mechanism, but
  when a gateway is unauthenticated on the broker, another actor can weaponise the
  duplicate-client-ID race to read telemetry, cause disconnects (DoS), and exfiltrate
  will data.

### Defensive takeaways

- Authenticate every MQTT client (`username/password`, X.509 certificates) and enforce
  per-tenant ACLs — never rely on topic-obscurity.
- Use unique, unpredictable client IDs and broker-side duplicate-ID rejection, or
  `keepalive`/session policy that prevents silent session takeover.
- Treat `/pub/`-style directories as sensitive; remove contractor archives when an
  engagement ends.
- Monitor duplicate-client-ID and abrupt-disconnect events as OT security signals.

---

## Artifacts (this folder)

```
lastwill/
├── evidence/
│   └── flag_and_proof.txt          # CONNACK, key messages, base64 blob, decoded flag
├── pub/                            # downloaded /pub archive (recursive)
│   ├── pub_README.txt
│   ├── pub_backups_config_backup_2024.txt
│   ├── pub_backups_notes.txt
│   ├── pub_docs_network_diagram_old.txt
│   ├── pub_logs_gateway_startup.log
│   ├── pub.pub_..._listings         # raw directory listings
│   └── portal_index.html           # decoy login page
├── scripts/
│   ├── mqtt_enum.py                # subscribe '#' -> telemetry discovery
│   ├── mqtt_enum2.py               # subscribe '#', '$SYS/#', will topics
│   ├── mqtt_diag.py                # subscribe '$internal/...' -> registry
│   ├── mqtt_bump.py                # LWT trigger: impersonate gateway01
│   ├── probe_broker.py             # raw MQTT CONNECT version probes
│   └── pub_dl.py                   # resilient /pub/ recursive downloader
└── Last-Will-writeup.md            # this file
```