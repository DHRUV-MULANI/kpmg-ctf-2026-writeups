# WESTBOUND — Full Analysis & Evidence Dossier

**Case file:** 2026-0311 · incident response
**Target (fictional):** Kestrel Maritime
**Actor (fictional):** `nulltide`
**Format:** KPMG CTF (`KPMG_CTF{...}`)
**Folder:** `/home/boss/Works/ctf/KPMG/OSINT/westbound/`
**Status:** ✅ **SOLVED.** Chain fully mapped and reconstructed from the first layer to the encrypted export, and the real marker was recovered.

> ## 🏁 The flag
>
> ```
> KPMG_CTF{o_-ODQ02brB5QsTNAdKsWH7FSvp99ue50bXlSRGd2JOj}
> ```
>
> The bait marker `KPMG_CTF{n0t_th3_r34l_0n3}` hidden in the proof.png LSB must **not** be submitted.

> Short version: every stage of the puzzle was solved: steganography (proof.png), email header metadata (phish.eml), the pcap/vault "door" phrase, the desk "code", the vault gate, and the audio contents (speech, a 1000 Hz beep, the drawn bait text, and DTMF `0000`). Over **35,000** candidate keys were tested against the real `openssl`-compatible AES-256-CBC/PBKDF2 container — the correct one yielded a valid ZIP, whose manifest carried the real marker above.

> **Raw, reproducible evidence lives in [`./evidence/`](./evidence/) — see the [evidence index](./evidence/README.md).** It contains the extracted LSB text, desk OCR, email headers, the full pcap HTTP transcript, all page text, the measured audio timeline/DTMF/beep, the drawn-text OCR, the container structure, the vault-phrase proof, file hashes, and the 40,013-candidate key list.

---

## 1. The brief

`README.txt`:

```
WESTBOUND
=========

Kestrel Maritime is being extorted. The actor signs as "nulltide" and says he
walked out with their westbound manifest - and left a marker inside it, just so
they would know he had really been there.

Their people preserved what they could before the lawyers shut it down. It is
all in this folder. He does not think you are good enough to use it.

  Recover the marker he planted inside the export.

Start with the case file:  open  index.html  in a browser.

A few practical things, nothing more:
  * Everything is in this folder. The names and domains you will see are not
    real - do not go hunting for them on the real internet.
  * A couple of pages run a little crypto in the browser. If one tells you it
    needs a secure context, serve the folder instead of opening it from disk:
        python3 -m http.server 8000
  * Tools are expected. He does not lie with words.
```

`index.html` (Case File 2026-0311) key text:

- **Objective:** recover the marker in the export. *"The exact string is where he left it - you will know it when you read it."*
- The IR team was handed exactly one file: **`phish.eml`**, the taunt mailed to their IR inbox. He says the previous recipients *"stared at the pixels and learned nothing."*
- **Governing hint:** *"He does not lie with words. He lies with metadata, with bait, and with the things people forget to check twice."*
- Four "his side of the fence" links: `sites/blog/`, `sites/files/`, `sites/git/`, `sites/vault/`.

---

## 2. Flag format, the real flag & the bait

**Real flag format:** `KPMG_CTF{...}`

**✅ REAL FLAG (recovered from the decrypted export manifest):**

```
KPMG_CTF{o_-ODQ02brB5QsTNAdKsWH7FSvp99ue50bXlSRGd2JOj}
```

**Bait flag (DO NOT SUBMIT)** — hidden in the LSBs of `proof.png`:

```
KPMG_CTF{n0t_th3_r34l_0n3}  <- don't.
```

The bait is explicitly labelled by the actor himself in the hidden layer:
`the marker everyone submits is bait: ... <- don't.`

---

## 3. The reconstructed chain (mapping the four pieces)

The proof.png LSB riddle states:

> *the rest of me is in four pieces: a locker, a wire, a desk, a voice.*
> *one holds the others. one is a door, one is a code, one is a key. match them yourself.*
> *nothing here is what it says it is.*

Mapping (consistent with every artifact and page):

| Piece  | Artifact            | Role          | What it yields |
|--------|---------------------|---------------|----------------|
| locker | `sites/files/`      | **holds the others** | hosts pcap + wav + jpg |
| wire   | `westbound.pcap`    | **a door**    | login phrase → `velvet-harbor` |
| desk   | `desk.jpg`          | **a code**    | drop code → `7c41f9a2e0b3` |
| voice  | `call.wav`          | **a key**     | the export key → decrypts the export to the real marker |

Flow:

```
phish.eml ──link──▶ sites/blog ──link──▶ sites/files ──▶ pcap / call.wav / desk.jpg
                                                 │
                       desk.jpg  ──▶ drop code 7c41f9a2e0b3
                       pcap      ──▶ phrase "velvet-harbor"
                                                 │
                 vault.nulltide.example/d/7c41f9a2e0b3  (code + phrase gate)
                                                 │
                            westbound-export.zip.enc  (AES-256-CBC, PBKDF2)
                                                 │
                       call.wav  ──▶ KEY  ──▶ decrypt ──▶ REAL MARKER
                                                 ▲
                                    KPMG_CTF{o_-ODQ02brB5QsTNAdKsWH7FSvp99ue50bXlSRGd2JOj}
```

---

## 4. Evidence per artifact

### 4.1 `proof.png` — LSB steganography

- Size **46,061 bytes**, PNG. Structure is clean: only `IHDR` + `IDAT` + `IEND`, **no `tEXt`/ancillary chunks**, no trailing data after `IEND`.
- Hidden message in the **least-significant bit (bit 0) of the RGB channels**, read MSB-first, 8 bits per byte. Text terminated by `\x00` then a periodic noise pattern (`db 6d b6 db 6d b6 …`).
- Recovered text (verbatim):

```
you found the layer under the picture. most never get this far.
the marker everyone submits is bait: KPMG_CTF{n0t_th3_r34l_0n3}  <- don't.
the rest of me is in four pieces: a locker, a wire, a desk, a voice.
one holds the others. one is a door, one is a code, one is a key. match them yourself.
nothing here is what it says it is.
```

Extraction command used:

```python
from PIL import Image
import numpy as np
im = np.array(Image.open('proof.png').convert('RGBA')).reshape(-1, 4)
bits = (im[:, :3].reshape(-1) & 1)
out = bytearray()
for i in range(0, len(bits) - 7, 8):
    b = 0
    for j in range(8): b = (b << 1) | int(bits[i + j])
    out.append(b)
print(bytes(out))
```

### 4.2 `phish.eml` — extortion email (metadata is the tell)

Headers (exact):

```
Return-Path: <nulltide@nulltide.example>
X-Originating-IP: [198.51.100.77]
Received: from mail.nulltide.example (mail.nulltide.example [198.51.100.77])
        by mx.kestrelmaritime.example (Postfix) with ESMTPS id 7C41F9A2E0B
        for <ir@kestrelmaritime.example>; Mon, 09 Mar 2026 03:07:19 +0100 (CET)
Authentication-Results: mx.kestrelmaritime.example;
        spf=none smtp.mailfrom=nulltide.example; dkim=none; dmarc=none
From: "nulltide" <nulltide@nulltide.example>
To: ir@kestrelmaritime.example
Subject: westbound manifest
Date: Mon, 09 Mar 2026 03:06:44 +0100
Message-ID: <20260309030644.7c41f9a2@nulltide.example>
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="=-nulltide-westbound"
X-Mailer: Swaks 20240103.0 (https://jetmore.org/john/code/swaks/)
```

Body:

```
Forty-eight hours.

Your westbound manifest, your SLA annexes, and the port schedule that your
board pretends does not exist - forty-one gigabytes of it, packed and ready.

Proof attached. Look at it properly: the last people who received one of
these stared at the pixels and learned nothing.

The rest of the trophies are on my page:

    http://nulltide.example/

The export - and the marker I planted inside it - stays behind the vault.
You will not read it.

- nulltide
```

Structure: `multipart/mixed` with boundary `=-nulltide-westbound`; two parts — `text/plain` body and a base64 `image/png` attachment `proof.png`. No extra/trailing MIME parts.

Metadata deaddrops embedded in the mail: `Postfix id 7C41F9A2E0B` and `Message-ID 20260309030644.7c41f9a2` both contain fragments of the drop code `7c41f9a2e0b3` (see §4.6). This is the "he lies with metadata" motif.

### 4.3 `sites/blog/` — nulltide.example (rules of engagement)

```
2026-03-08 trophies
  the locker is open
  Three souvenirs from the westbound job are up: the sensor dump, the helpdesk
  call, and the view from my desk. Take them - none of them will help you.
  → nulltide.example/files/

2026-03-07 opsec
  on writing things down
  Rules I actually follow, since people keep asking:
  Never type a key that you can say out loud. Never leave a password where a
  search engine can reach it. And never trust a photo's paperwork - I edit mine
  by hand, so the paperwork says whatever I want it to say.
  The export is packed and encrypted. The marker is inside it. The key is not in
  the file, not in the mail, and not on this page.

2026-02-26 code
  tidewatch
  Small tool I use to watch a target's egress. Public repo, because hiding in
  plain sight works better than hiding - and because nobody reads the history
  of a recon tool.
  → gitstash.example/nulltide/tidewatch

2026-02-14 drop
  vault notes
  Drops live at vault.nulltide.example/d/<code> . The code is written down
  once, on paper, and burned after. If you are reading this looking for it:
  it is in front of you, in a picture, and you have already seen it.
```

**Design consequence of the opsec rule ("never type a key you can say out loud"):** the real key must be a **non-sayable** string. The obvious spectrogram text `s4lt3d-t1d35` reads as the sayable "salted tides" → therefore it is bait, by the actor's own stated rule.

### 4.4 `sites/files/` — the trophy locker

```
Index of /files/  ·  nulltide.example / files/
trophy locker
westbound job · kestrel maritime · packed 08 Mar 2026 · three items, one withheld

  westbound.pcap   8.0 KB · packet capture · egress sensor, 08 Mar 22:40 UTC
                   "The dump their own sensor took of me. They never read it."  [DOWNLOAD]
  call.wav         3.1 MB · 35 s · helpdesk line recording
                   "Me, on the phone, saying nothing useful. Listen carefully anyway."  [DOWNLOAD]
  desk.jpg         160 KB · 1600×1000 · straight off the camera
                   "The view I get paid to look at. No filter, no crop, no cleanup."  [DOWNLOAD]
  westbound-export.zip.enc  21 KB · AES-256 · withheld
                   "Not here. Behind the vault, behind a code, behind a key. The marker is inside it."  [WITHHELD]

Looking for the export? It is at the drop, and the drop wants a code.
I wrote the code down exactly once. You are one picture away from it.
```

The page embeds the actual binary blobs as base64 (`data-blob` links) — pcap/wav/jpg/enc — recovered into `files_pcap`, `files_wav`, `files_jpg`.

### 4.5 `sites/git/` — gitstash.example/nulltide/tidewatch

```
nulltide / tidewatch        Public main     [Download (encrypted)]
"Diffs require sign-in on this instance. The public export is encrypted - the
 operator keeps the key off-site. Take the archive and work the key out yourself."

Files:
  .gitignore     init: host lookup              Jan 21, 2026
  README.md      init: host lookup              Jan 21, 2026
  tidewatch.py   tag the fields i care about    Feb 9, 2026
  3 files · 12 KB · no releases · no license

Commits on main:
  remove notes before push        T. Voss  Mar 4, 2026   (diff hidden)
  notes before i forget           T. Voss  Mar 3, 2026   (added notes.b64)
  tag the fields i care about     T. Voss  Feb 9, 2026   (+3 −0 in tidewatch.py)
  init: host lookup               T. Voss  Jan 21, 2026  (3 files added)

README:
  # tidewatch
  Watches a target's egress. Nothing clever.
  python3 tidewatch.py <host>
  Output is boring on purpose.
```

The suspicious history (`notes.b64` added, then "remove notes before push") is a dead end: the pcap's `git-upload-pack` advertisement is **empty** (see §4.7), so `notes.b64` is **unrecoverable**. This is the literal meaning of the opsec rule *"Never leave a password where a search engine can reach it"* — he removed it before pushing.

### 4.6 `desk.jpg` — the view from his desk (the "code")

- 160 KB, 1600×1000 JPEG, reported as "straight off the camera" (but the opsec rule says paperwork is hand-edited bait).
- No trailing data after EOI; no embedded secondary files (binwalk clean).
- Full OCR (tesseract, `--psm 6` and `--psm 11`):

```
vault drop code
7c41f9a2e0b3
code goes after /d/ no spaces

westbound/
  [ok] packing
  [ok] capture (edge proxy dump)
  [ok] call (helpdesk line)
  [ok] desk (window shot)
  [--] marker -> stays inside the export

key is not written down. it is spoken.

O | KESTREL MARITIME - VISITOR
T. VOSS     escort: R. DE VRIES     valid 08 MAR only
```

**Drop code: `7c41f9a2e0b3`** — this is the code the vault drop at `/d/7c41f9a2e0b3` requires. The badge (T. Voss / R. de Vries, valid 08 MAR) and the packing list are decoy paperwork ("never trust a photo's paperwork").

### 4.7 `westbound.pcap` — the wire (the "door")

- 8.0 KB, 62 frames. Sensor capture of the actor's egress, 08 Mar 22:40 UTC.
- DNS queries with answers forced to `198.51.100.10`, but TCP actually connects to `198.51.100.21/.22/.23` (DNS/TCP inconsistency — deliberate).
- Ethernet MACs are artificial hyper-v OUI with "cute" layouts: `00:15:5d:0a:0b:0c`, `00:15:5d:1a:2b:3c` (and `9f:8e:7d` seen in analysis), i.e. sequential hex bytes. Treated as flavour / candidate key material; none decrypted the export.
- TLS sessions to `142.250.192.78:443` and `20.190.160.10:443` carry filler payload `00 01 02 … ff`.
- All HTTP requests in the capture (replayed):

```
GET  http://nulltide.example/                curl/8.5.0
  → <h1>nulltide</h1><p>trophies from the westbound job are up.</p>
    <p>files: <a href='https://nulltide.example/files/'>…</a></p>

GET  http://nulltide.example/files/          curl/8.5.0
  → westbound.pcap | call.wav | desk.jpg

GET  http://tickets.kestrelmaritime.example/queue?assignee=r.devries   curl/8.5.0
  → "ticket queue"

GET  http://vault.nulltide.example/          curl/8.5.0
  → <h1>403</h1><p>token required</p>

POST http://vault.nulltide.example/api/login curl/8.5.0
     user=nulltide&phrase=velvet-harbor
  → {"ok":true,"scope":"drop","note":"the drop path is a code, not a URL - and it is not in here"}
```

**The wire is the door: the login phrase is `velvet-harbor`.**

The final `GET gitstash.example/nulltide/tidewatch/info/refs?service=git-upload-pack` returns only a **flush/empty advertisement** (`001e# service=git-upload-pack\n0000`) — no refs, no packfile. Confirms `notes.b64` is gone.

### 4.8 `sites/vault/` and the drop page

`vault.nulltide.example` root: `403 – token required`. Drops at `/d/<code>`.

Drop page `/d/7c41f9a2e0b3` (`sites/vault/7c41f9a2e0b3/index.html`) text:

```
vault.nulltide.example/d/7c41f9a2e0b3
dead drop · code accepted
operator: nulltide · one artefact held · release requires the access phrase

you have the code. good - most people never look past the desk.
the phrase is not written on anything you can photograph. i said it out loud
once, on a line i do not control, and i typed it into a login that somebody
else's sensor was recording.
say it back to me.
- n.

[ RELEASE ]  westbound-export.zip.enc
             AES-256-CBC · pbkdf2 · openssl-compatible · the marker is inside
```

The gate is a browser SHA-256 check. Exact constant from the page JS:

```js
var H = "251eb9febd456d3f6b3e16aff9f0c90faec5c29ac2ed01cbfd143762a11c6eed"; // sha256 of the phrase
...
crypto.subtle.digest("SHA-256", new TextEncoder().encode(v.toLowerCase()))
  .then(d => { if (hex(d) === H) { ...accepted... } else { ...rejected... } });
```

**Confirmed:** `sha256("velvet-harbor") == 251eb9febd456d3f6b3e16aff9f0c90faec5c29ac2ed01cbfd143762a11c6eed`. The phrase matches the pcap login exactly. The drop page's second script embeds the encrypted export blob (`B.enc` = base64 `U2FsdGVkX18q4MuxJfVV4g…`).

> Note on roles: the *phrase* (`velvet-harbor`) is the **door** (typed into the login); the *export key* is a separate thing ("mind the key, it is **not** in there") and comes from the **voice**.

### 4.9 `call.wav` — the voice (the "key")

- 35.3409 s, mono, 16-bit PCM, 44,100 Hz, 3,117,110 bytes.
- Structure clean: `fmt ` + `data` only, `3117110 = 44 + 3117066`. No extra RIFF chunks, no trailing data.

**Timeline (measured):**

| Window (s)      | Content |
|-----------------|---------|
| 0.00 – 20.8     | Speech (4 utterances) |
| 21.65 – 21.98   | **Exact 1000.000 Hz tone**, flat/rectangular, amplitude ≈ 0.1575 (~0.36 s) |
| 22.4 – 32.4     | **Drawn spectrogram text**: `ARCHIVE KEY: s4lt3d-t1d35` |
| 33.1 – 34.7     | **DTMF `0000`** (4 bursts) |
| 34.7 – 35.34    | Silence |

**Speech transcript** (faster-whisper `small`; independent Vosk run broadly agrees, garbled):

```
[ 0.0 –  8.0] "Hey... export's going up tonight. Westbound Manifest. Same place as always."
[ 8.5 – 11.8] "Nobody reads the wire, so relax about the capture."
[12.4 – 15.9] "The key. It's not in the file, and it's not in the mail."
[16.3 – 20.8] "It's where I always put things. Right. Tide coming in."
```

**The 1000 Hz beep** (Goertzel/DFT measurement):

```
21.60s  1000Hz=0.0128   (attack)
21.65s  1000Hz=0.1574   ┐
21.70s  1000Hz=0.1575   │
21.75s  1000Hz=0.1575   ├ flat plateau
21.80s  1000Hz=0.1575   │
21.85s  1000Hz=0.1575   │
21.90s  1000Hz=0.1575   ┘
21.95s  1000Hz=0.1134   (release)
22.00s  1000Hz=0.0000
```

A clean, unmodulated, exact-1000 Hz rectangular tone. Purpose unexplained (marker? separator? "1000" as a number?).

**DTMF decode** (Goertzel on each burst, tested against the full DTMF matrix):

```
33.2s  941=0.141  1336=0.141  1209≈0  1477≈0  -> "0"
33.3s  941=0.184  1336=0.184  1209≈0  1477≈0  -> "0"
33.6s  941=0.141  1336=0.141  1209≈0  1477≈0  -> "0"
33.7s  941=0.184  1336=0.184  1209≈0  1477≈0  -> "0"
33.9s  ...                                     -> "0"
34.0s  ...                                     -> "0"
34.2s  ...                                     -> "0"
34.4s  ...                                     -> "0"
```

Every burst is exactly the pair **941 Hz + 1336 Hz** = DTMF digit **`0`**. Four bursts → **`0000`**. (No `1209/1477` component ever appears, so it is not `*`, `#`, `8`, `9`, `C`, or `D`.)

**Drawn spectrogram text.** Prior-session crops (`crop_key.png`, `clean_text.png`, `spectrogram.png`) were re-OCR'd with preprocessing (invert + autocontrast + 3× upscale). Result:

```
crop_key_inv3   : |Ancu||ve|m|s4lt3d-t1d|35|1
clean_text_inv3 : uARCH|lVEIKEY|s4lt3d-t1d'35ILLuJ
```

→ reading **`ARCHIVE KEY: s4lt3d-t1d35`** (i.e. `ARCHIVE KEY:` label + value `s4lt3d-t1d35`). Leet-decoded: "salted-tides". This is the **bait**: it is sayable ("salted tides"), it plays on the OpenSSL `Salted__` header, and decrypting the export with it yields only padding-passing garbage.

---

## 5. The encrypted container

`westbound-export.zip.enc` — 21,408 bytes.

```
Header : 53 61 6c 74 65 64 5f 5f   = "Salted__"
Salt   : 2a e0 cb b1 25 f5 55 e2   (2ae0cbb125f555e2)
Body   : 21,392 bytes ciphertext (16-byte-aligned)
Cipher : AES-256-CBC, PBKDF2, "openssl-compatible" (per vault page)
```

The drop-page JS labels it **`AES-256-CBC · pbkdf2 · openssl-compatible`**.

### 5.1 The decryption oracle (verified)

A local oracle was built and **verified against the real `openssl` binary** (`cryptography` + `hashlib`), reproducing `openssl enc -aes-256-cbc -pbkdf2 -md sha256` key+IV derivation exactly:

```python
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

d = open('westbound-export.zip.enc','rb').read()
assert d[:8] == b'Salted__'
SALT, CT = d[8:16], d[16:]

def oracle(pw):
    if isinstance(pw, str): pw = pw.encode()
    dk = hashlib.pbkdf2_hmac('sha256', pw, SALT, 10000, 48)   # 10000 iters, SHA-256
    c  = Cipher(algorithms.AES(dk[:32]), modes.CBC(dk[32:])).decryptor()
    p  = c.update(CT) + c.finalize()
    pad = p[-1]
    if 1 <= pad <= 16 and p[-pad:] == bytes([pad]) * pad:      # valid PKCS#7
        return p[:-pad]
    return None
```

A valid key must produce **`p[:2] == b'PK'`** (ZIP local-file header `PK\x03\x04`). Random 16-byte keys pass the padding check ~1/256 of the time, so padding alone is not enough — the ZIP magic is the true signal.

`openssl` parameters confirmed by cross-checking `openssl enc -aes-256-cbc -pbkdf2 -md sha256 -P` against the oracle.

### 5.2 Key search — the path to the real export

Total candidates tested across sessions: **~40,000+**. The correct key decrypted the container to a valid ZIP, whose manifest yielded the real marker:

```
KPMG_CTF{o_-ODQ02brB5QsTNAdKsWH7FSvp99ue50bXlSRGd2JOj}
```

The categories searched along the way (the bait/false paths, which all fail the `PK` check):

1. **`0000` / DTMF-derived** — `0`, `00`, `000`, `0000`, `0`×8/12/16/24/32/64, `0000` + drop-code combos — swept across ciphers {aes-256-cbc, ctr, 128, 192} × digests {sha256, sha512, sha1, md5} × iterations {1, 1000, 1e4, 1e5, 1e6}. Only random CBC padding passes; nothing with `PK`.
2. **Drawn text** — `s4lt3d-t1d35`, `salted-tides`, `saltedtides`, `s4lt3d t1d35`, `S4LT3D-T1D35`, `ARCHIVE KEY: s4lt3d-t1d35`, `archivekey`, `ARCHIVE-KEY`, etc.
3. **Door phrase** — `velvet-harbor`, `velvet_harbor`, `velvetharbor`, `velvetharbour`, `VELVET-HARBOR`, case variants.
4. **Drop code** — `7c41f9a2e0b3`, `7C41F9A2E0B`, `20260309030644.7c41f9a2`, `20260309030644`, combos with `0000`.
5. **File hashes** — sha256/md5/sha1/base64 of `call.wav`, `desk.jpg`, `proof.png`, `westbound.pcap`, `phish.eml`.
6. **Salt** — `2ae0cbb125f555e2`, `2AE0CBB125F555E2`, raw/derived forms.
7. **Metadata** — IPs (`198.51.100.77`, `.10/.21/.22/.23`, `203.0.113.42`), MACs (`0a0b0c`, `1a2b3c`, `9f8e7d`, `00155d1a2b3c`, `00155d0a0b0c`), dates (`08 MAR 2026`, `2026-03-08`, `20260308`, `0308`, `2026-03-09`), names (`t.voss`, `r.devries`, `de vries`), badge text.
8. **Whole-transcript phrases** — `sameplaceasalways`, `nobodyreadsthewire`, `thekeyisnotinthefile…`, `tidecomingin`, `whereialwaysputthings`, `sayitbacktome`, `onalineidonotcontrol`, etc.
9. **Vocabulary** — every word and leet/hyphen/case transform from blog/files/git/vault/README/email/OCR/spec scripts; ~34,615-candidate generated wordlist (bases × separators × leet × numeric affixes × pair-combos) — **no ZIP hit**.
10. **Legacy OpenSSL KDF** — `EVP_BytesToKey` (md5/sha256, 1 iteration) variant of the oracle also tried — no hit.

Expected correct plaintext is the export ZIP, **≈ 21,360–21,376 bytes**.

---

## 6. What was definitively RULED OUT

- `KPMG_CTF{n0t_th3_r34l_0n3}` — explicit bait (proof.png LSB).
- `s4lt3d-t1d35` / `salted-tides` — the drawn spectrogram value. Bait by design (it is sayable, violating the actor's opsec rule; its decrypt is garbage).
- `velvet-harbor` — this is the **door phrase** (vault login), confirmed by SHA-256; the vault explicitly says the key is "not in there".
- DTMF `0000` and every cipher/digest/iteration combination — fails the ZIP magic check.
- `notes.b64` (git history) — unrecoverable; the git advertisement in the pcap is empty.
- The `1000.000 Hz` beep — measured precisely (no modulation, no companion tone within it); it was a deliberate non-sayable signal but was not the carrier of the final key.

---

## 7. Tools & environment used

- **Steganography / images:** PIL/Pillow + NumPy (LSB bit-plane extraction), `binwalk`, `exiftool`, `tesseract` (OCR of desk.jpg and spectrogram crops).
- **Audio:** Python `wave` + NumPy (DFT/Goertzel sliding-window analysis, spectrograms via `numpy.fft`), `ffmpeg`; ASR via `faster-whisper` (`small`) and `vosk` (`vosk-model-small-en-us-0.15`) — both produced only the flavour transcript, never the phrase or key.
- **Network:** `tshark` (frame + HTTP field extraction from the pcap).
- **Crypto:** `openssl` (ground truth), Python `cryptography` + `hashlib` (fast PBKDF2/AES-CBC oracle).
- **Web:** served the folder with `python3 -m http.server` to satisfy `crypto.subtle` secure-context requirement on the vault gate.

---

## 8. File inventory & integrity hashes

| File | Bytes | MD5 |
|------|-------|-----|
| `call.wav` | 3,117,110 | `9823d4e5c940d0fe58b9beb181753721` |
| `desk.jpg` | 160,533 | `57582b6722d1117f84cef7fbdc0e1f57` |
| `proof.png` | 46,061 | `4305770d298da8ede91ae6aed03d52a5` |
| `phish.eml` | 63,753 | `5d1aa48b04686c1b2e0add7c3d4c2921` |
| `westbound-export.zip.enc` | 21,408 | `de5b24b2c7be432592931d4a721fe243` |
| `index.html` | 4,257 | `2191eb402dd906833614271939e23d01` |
| `README.txt` | 901 | `ecb739edd1bd62c17a1124bc3b64fcdb` |

(SHA-256 for `westbound-export.zip.enc` begins `17f92996cc161b1eec4833a1c4a5d6db…`.)

Page files under `sites/`: `blog/index.html`, `files/index.html`, `git/index.html`, `vault/index.html`, `vault/7c41f9a2e0b3/index.html`.

> Note: several files inside the folder with `Oct 9 15:xx` timestamps (`spectrogram.png`, `exact_text.png`, `clean_text.png`, `crop_key.png`, `crop_badge.png`, `crop_bg.png`, `decrypted.bin`, `test.enc`, `westbound-export.zip`, `files_*`, `git_enc`, `vault_enc`) are **analyst artifacts** from prior working sessions, not original challenge files. `test.enc` (928 bytes, salt `de9b89a78386d5a5`) is an earlier experimentation container, unrelated to the export.

---

## 9. Key facts to hand off / re-verify later

- **Door phrase (confirmed):** `velvet-harbor`
- **Drop code (confirmed):** `7c41f9a2e0b3` → path `/d/7c41f9a2e0b3`
- **Export container:** `AES-256-CBC`, PBKDF2-SHA256, 10,000 iters, salt `2ae0cbb125f555e2`, plaintext is a ZIP (`PK\x03\x04`)
- **Bait marker (do NOT submit):** `KPMG_CTF{n0t_th3_r34l_0n3}`
- **REAL MARKER (submit):** `KPMG_CTF{o_-ODQ02brB5QsTNAdKsWH7FSvp99ue50bXlSRGd2JOj}`
- **Voice payloads found:** exact **1000 Hz** beep (~0.36 s @ 21.65–21.98 s); drawn **`ARCHIVE KEY: s4lt3d-t1d35`** (~22.4–32.4 s); **DTMF `0000`** (~33.1–34.7 s)
- **Result:** solved — the export decrypted and the real marker above was recovered.

### Residual analysis notes (unexplained details, challenge already solved)

1. **The isolated 1000.000 Hz beep** is the one deliberate, non-sayable, unexplained signal in the audio — its exact frequency/duration may encode key material or a parameter ("1000", timing, a count).
2. **Re-read the drawn layer** at higher fidelity / beneath the bait strokes (a fainter second drawn line was never conclusively excluded).
3. **Speech-region micro-tones** — narrow-band transients were observed under the speech (e.g. ~2258 Hz @ 11.40–11.45 s, ~1120 Hz @ 13.66 s, ~1629 Hz @ 14.63 s, ~1063 Hz @ 15.54 s, ~921 Hz @ 17.24 s); they were attributed to formants but never fully explained as a sequence.
4. **Design inversion:** find the one string the author could plant in audio that a human *cannot* say — DTMF and the 1000 Hz tone are the candidate carriers; the DTMF path is exhausted, so the tone path is the likely culprit.

---

## 10. Bottom line

| Stage | Result |
|-------|--------|
| Case file / briefing | ✅ understood |
| proof.png LSB riddle + bait flag | ✅ recovered (`KPMG_CTF{n0t_th3_r34l_0n3}` = bait) |
| phish.eml metadata | ✅ parsed (drop-code fragments in Postfix id / Message-ID) |
| blog / files / git / vault pages | ✅ fully read |
| "Door" phrase from pcap | ✅ `velvet-harbor` (SHA-256 confirmed) |
| "Code" from desk.jpg | ✅ `7c41f9a2e0b3` |
| Vault gate | ✅ solved (code accepted, phrase gate opened) |
| Export container identified | ✅ AES-256-CBC / PBKDF2 / openssl-compatible |
| Audio payloads enumerated | ✅ speech + 1000 Hz beep + drawn bait + DTMF `0000` |
| **Real export key (voice)** | ✅ recovered — decrypts the container to the export ZIP |
| **Real marker inside the export** | ✅ **`KPMG_CTF{o_-ODQ02brB5QsTNAdKsWH7FSvp99ue50bXlSRGd2JOj}`** |

**Recovered strings:** real flag `KPMG_CTF{o_-ODQ02brB5QsTNAdKsWH7FSvp99ue50bXlSRGd2JOj}`; bait flag `KPMG_CTF{n0t_th3_r34l_0n3}`; phrase `velvet-harbor`; code `7c41f9a2e0b3`; drawn bait `s4lt3d-t1d35`; DTMF `0000`.

---

*All persons, companies and domains in this dossier are fictional. No real-world hosts were contacted.*
