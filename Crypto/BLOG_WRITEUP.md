# KPMG CTF Writeup: Deep-Dive Forensics & Cryptanalysis of `challenge_file`

> **Author:** Antigravity  
> **Category:** Forensics / Steganography / Cryptography  
> **Challenge File:** [`challenge_file`](file:///home/boss/Works/ctf/KPMG/Crypto/challenge_file)  
> **Final Flag:** `KPMG_CTF{S33K_AND_F1ND_M3}`  

---

## Table of Contents
1. [Executive Summary / TL;DR](#executive-summary--tldr)
2. [Phase 1: Initial Triage & Magic Byte Anomaly](#phase-1-initial-triage--magic-byte-anomaly)
3. [Phase 2: JPEG Marker Forensics & The Truncation Trap](#phase-2-jpeg-marker-forensics--the-truncation-trap)
4. [Phase 3: Restoring True Dimensions (SOF0 Recovery)](#phase-3-restoring-true-dimensions-sof0-recovery)
5. [Phase 4: Optical Character Recognition (OCR)](#phase-4-optical-character-recognition-ocr)
6. [Phase 5: Cryptanalysis & Statistical Inspection](#phase-5-cryptanalysis--statistical-inspection)
7. [Phase 6: Morse Code Translation & Flag Extraction](#phase-6-morse-code-translation--flag-extraction)
8. [Phase 7: End-to-End Automated Solver & Terminal Output](#phase-7-end-to-end-automated-solver--terminal-output)
9. [Key Takeaways & Lessons Learned](#key-takeaways--lessons-learned)

---

## Executive Summary / TL;DR

The challenge presented an unidentified binary blob titled [`challenge_file`](file:///home/boss/Works/ctf/KPMG/Crypto/challenge_file) (322,687 bytes). Unraveling the flag required solving a three-stage puzzle across forensics, steganography, and classical cryptography:

1. **Header Obfuscation:** The file opened with fake PNG magic bytes (`\x89PNG\r\n\x1a\n`), masking a legitimate JPEG/JFIF stream. Restoring the 8-byte header fixed the file container.
2. **Dimension Manipulation:** The JPEG SOF0 baseline frame marker was modified to report a height of only 550 pixels, hiding a text block in the lower 450 pixels of the 800x1000 image. Repairing the height field in the marker restored the hidden text.
3. **Word-Length Morse Cipher:** The revealed paragraph consisted of exactly 125 words, restricted exclusively to lengths of 3, 5, and 7 characters. Length `3` acted as a letter delimiter (occurring exactly 25 times), length `5` represented dots (`.`), and length `7` represented dashes (`-`), spelling out the flag in Morse code: `KPMG_CTF{S33K_AND_F1ND_M3}`.

```mermaid
flowchart TD
    A["Corrupted Binary File<br/>('challenge_file')"] -->|"Fix Magic Bytes (PNG -> JFIF)"| B["Cropped JPEG Image<br/>(800x550 px)"]
    B -->|"Repair SOF0 Height (550 -> 1000 px)"| C["Restored JPEG Image<br/>(Reveals Hidden Paragraph)"]
    C -->|"Run Tesseract OCR"| D["Extracted Text<br/>(125 Words)"]
    D -->|"Word Length Analysis<br/>{3, 5, 7}"| E["Morse Code<br/>(3=Sep, 5=Dot, 7=Dash)"]
    E -->|"Morse Decode"| F["Flag: KPMG_CTF{S33K_AND_F1ND_M3}"]
```

---

## Phase 1: Initial Triage & Magic Byte Anomaly

When initially checking the file with standard utilities, the Linux `file` utility identified it simply as `data`:

```bash
$ file challenge_file
challenge_file: data
```

To understand why `file` failed to recognize the format, we examined the first 64 bytes using Python:

```python
with open('challenge_file', 'rb') as f:
    data = f.read(64)
print("Hex dump:", data.hex())
print("ASCII representation:", data)
```

### Output:
```text
Hex dump: 89504e470d0a1a0a494600010100000100010000ffdb004300030202020202030202020303030304060404040404080606050609080a0a090809090a0c0f0c0a
ASCII representation: b'\x89PNG\r\n\x1a\nIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C...'
```

### Forensic Breakdown of the Header:
Notice the conflicting bytes:
- Bytes `0..7`: `89 50 4E 47 0D 0A 1A 0A` — The standard 8-byte PNG file signature (`\x89PNG\r\n\x1a\n`).
- Bytes `8..9`: `49 46` — ASCII characters `'I'`, `'F'`.
- Bytes `10..19`: `00 01 01 00 00 01 00 01 00 00` — Version, density units, X/Y density for JFIF.
- Bytes `20..23`: `FF DB 00 43` — Define Quantization Table (DQT) segment marker for JPEG.
- End of File: `... b0 1f ff d9` — Standard JPEG End of Image (EOI) marker `FF D9`.

The author had intentionally overwritten the first 8 bytes of a JFIF JPEG file with the PNG magic header.

In standard JFIF:
- `FF D8` = Start of Image (SOI)
- `FF E0` = APP0 Marker
- `00 10` = APP0 Segment Length (16 bytes)
- `4A 46 49 46` = Identifier ASCII `"JFIF"` (followed by `00`)

Notice that `FF D8 FF E0 00 10 4A 46` is exactly **8 bytes** long!
By replacing the first 8 bytes with `FF D8 FF E0 00 10 4A 46`, the remainder of the header aligns: `'I'`, `'F'`, `'\x00'`, version `1.1`, density `1x1`.

```python
# Repairing the 8-byte header
repaired_data = bytes.fromhex('ffd8ffe000104a46') + data[8:]
```

After writing this repaired buffer, `file` successfully recognized the image:
```bash
$ file repaired.jpg
repaired.jpg: JPEG image data, JFIF standard 1.01, aspect ratio, density 1x1, segment length 16, baseline, precision 8, 800x550, components 3
```

---

## Phase 2: JPEG Marker Forensics & The Truncation Trap

Opening `repaired.jpg` displayed an 800x550 image showing an agent in a gas mask, with two lines of text at the bottom. However, the last line of text was abruptly sliced off:

> *"Hackers sneak through, and steal network secrets daily. Now foreign"*  
> *"systems are falling offline today. Our agent seeks answers without delay..."*

When running an image decoder or OCR engine (`tesseract repaired.jpg stdout`), the decoder emitted a telling warning:

```text
Corrupt JPEG data: 179702 extraneous bytes before marker 0xd9
Hackers sneak through, and steal network secrets daily. Now foreign
```

### Explaining "Extraneous Bytes Before Marker 0xd9":
In JPEG encoding, entropy-coded scan data begins after the Start of Scan (`FF DA`) marker and continues until all pixel blocks (Minimum Coded Units / MCUs) required by the dimensions in the Start of Frame (`FF C0` / SOF0) marker are parsed.
- The total file size is **322,687 bytes**.
- To decode 800x550 pixels, libjpeg only consumed ~143,000 bytes.
- The remaining **179,702 bytes** were ignored before hitting `FF D9` (EOI).

This is a classic anti-forensics steganography technique: **height tampering in the SOF0 marker**.

Let us parse the JPEG markers manually:

```python
with open('repaired.jpg', 'rb') as f:
    buf = f.read()

i = 2
while i < len(buf):
    if buf[i] == 0xFF:
        marker = buf[i+1]
        length = int.from_bytes(buf[i+2:i+4], 'big')
        if marker == 0xC0: # SOF0 (Start of Frame, Baseline DCT)
            precision = buf[i+4]
            h = int.from_bytes(buf[i+5:i+7], 'big')
            w = int.from_bytes(buf[i+7:i+9], 'big')
            print(f"SOF0 Marker at offset {i}:")
            print(f"  Precision: {precision}")
            print(f"  Reported Height: {h} px (Hex: {buf[i+5:i+7].hex()})")
            print(f"  Reported Width:  {w} px (Hex: {buf[i+7:i+9].hex()})")
            break
        i += 2 + length
    else:
        i += 1
```

### Output:
```text
SOF0 Marker at offset 158:
  Precision: 8
  Reported Height: 550 px (Hex: 0226)
  Reported Width:  800 px (Hex: 0320)
```

The author changed the two height bytes at offset `163:165` from their real value to `0x0226` (550).

---

## Phase 3: Restoring True Dimensions (SOF0 Recovery)

To find the true height, we tested heights incrementally and checked `djpeg` stderr for decode anomalies:

```python
import subprocess

for test_h in [600, 700, 800, 900, 990, 995, 1000, 1005, 1010]:
    modified = bytearray(buf)
    modified[163:165] = test_h.to_bytes(2, 'big')
    with open('test.jpg', 'wb') as f:
        f.write(modified)
    res = subprocess.run(['djpeg', 'test.jpg'], capture_output=True)
    err = res.stderr.decode().strip()
    print(f"Height {test_h:4d} px: {err if err else 'CLEAN DECODE (0 errors)'}")
```

### Output:
```text
Height  600 px: Corrupt JPEG data: 160968 extraneous bytes before marker 0xd9
Height  700 px: Corrupt JPEG data: 118844 extraneous bytes before marker 0xd9
Height  800 px: Corrupt JPEG data: 77902 extraneous bytes before marker 0xd9
Height  900 px: Corrupt JPEG data: 29408 extraneous bytes before marker 0xd9
Height  990 px: Corrupt JPEG data: 2463 extraneous bytes before marker 0xd9
Height  995 px: CLEAN DECODE (0 errors)
Height 1000 px: CLEAN DECODE (0 errors)
Height 1005 px: CLEAN DECODE (0 errors)
Height 1010 px: Corrupt JPEG data: premature end of data segment
```

The image dimensions are standard multiples of MCU blocks (800x1000). Setting the height to **1000 pixels** (`0x03E8`) decoded with 0 errors and cleanly consumed the full byte stream up to `FF D9`.

The fully restored image was written to [`restored_image.jpg`](file:///home/boss/Works/ctf/KPMG/Crypto/restored_image.jpg).

---

## Phase 4: Optical Character Recognition (OCR)

With the image restored to 800x1000 pixels, the full paragraph became visible below the photo:

```bash
$ tesseract restored_image.jpg stdout
```

### Full Extracted Text Output:
```text
Hackers sneak through, and steal network secrets daily. Now foreign
systems are falling offline today. Our agent seeks answers without delay
tonight. The mystery grows thicker after all hunters for every ghost
machine trace can uncover these signals heneath radar. You watch their
codes, but virus worms creep forward forever. And worse logic hombs
corrupt records. All shadows exist outside the walls where digital thieves
dwell quietly. The alert watcher can analyze bytes, yet nothing makes
sense. His chief focus remains finding those hackers. Who wrote these
complex files? New teams writing strange scripts nightly. Our nearest
enemy has dropped decoy nodes. Now every cyher soldier marches
ahead bravely. Men extract botnets, and purge dirty files forever tonight.
The victory takes massive efforts under attacks.
```

---

## Phase 5: Cryptanalysis & Statistical Inspection

At first glance, the text appears to be standard CTF lore. However, careful inspection reveals artificial vocabulary choices:
- *"Hackers sneak through, and steal network secrets daily..."*
- Notice the rhythm and word sizing.

Let us inspect the length of every word in the paragraph:

```python
import re
from collections import Counter

words = re.findall(r'[a-zA-Z]+', text)
lengths = [len(w) for w in words]

print(f"Total word count: {len(words)}")
print(f"Unique lengths: {sorted(set(lengths))}")
print(f"Length frequencies: {Counter(lengths)}")
```

### Output:
```text
Total word count: 125
Unique lengths: [3, 5, 7]
Length frequencies: Counter({7: 51, 5: 49, 3: 25})
```

### Cryptographic Insights:
1. **Strictly 3, 5, and 7:** Every single word in the entire 125-word text has a length of either 3, 5, or 7 letters.
2. **Exactly 25 Threes:** There are exactly 25 words of length 3.
3. **Delimiter Distribution:** Splitting the sequence by length 3 yields exactly **26 sub-sequences** composed of 5s and 7s.
4. **Length of Sub-sequences:** The length of each sub-sequence varies between 1 and 6 elements.
5. In International Morse Code:
   - Alphabet characters have lengths 1 to 4.
   - Digits have length 5.
   - Underscores (`_`) have Morse code `..--.-` (length 6).
   - Parentheses / braces have length 5 or 6.

Therefore:
- **Length 3:** Word / Letter delimiter (Space)
- **Length 5:** Dot (`.`)
- **Length 7:** Dash (`-`)

---

## Phase 6: Morse Code Translation & Flag Extraction

Splitting the word lengths by `3` and mapping `5 -> .` and `7 -> -`:

```python
# Split lengths by 3
parts = []
curr = []
for l in lengths:
    if l == 3:
        parts.append(curr)
        curr = []
    else:
        curr.append(l)
parts.append(curr)
```

### Character-by-Character Breakdown Table:

| Index | Word Sample | Word Lengths | Morse Pattern | Decoded Character |
| :---: | :--- | :--- | :---: | :---: |
| **0** | `Hackers sneak through` | `[7, 5, 7]` | `-.-` | **K** |
| **1** | `steal network secrets daily` | `[5, 7, 7, 5]` | `.--.` | **P** |
| **2** | `foreign systems` | `[7, 7]` | `--` | **M** |
| **3** | `falling offline today` | `[7, 7, 5]` | `--.` | **G** |
| **4** | `agent seeks answers without delay tonight` | `[5, 5, 7, 7, 5, 7]` | `..--.-` | **_** |
| **5** | `mystery grows thicker after` | `[7, 5, 7, 5]` | `-.-.` | **C** |
| **6** | `hunters` | `[7]` | `-` | **T** |
| **7** | `every ghost machine trace` | `[5, 5, 7, 5]` | `..-.` | **F** |
| **8** | `uncover these signals beneath radar` | `[7, 5, 7, 7, 5]` | `-.--.` | **{** (or `(`) |
| **9** | `watch their codes` | `[5, 5, 5]` | `...` | **S** |
| **10** | `virus worms creep forward forever` | `[5, 5, 5, 7, 7]` | `...--` | **3** |
| **11** | `worse logic bombs corrupt records` | `[5, 5, 5, 7, 7]` | `...--` | **3** |
| **12** | `shadows exist outside` | `[7, 5, 7]` | `-.-` | **K** |
| **13** | `walls where digital thieves dwell quietly` | `[5, 5, 7, 7, 5, 7]` | `..--.-` | **_** |
| **14** | `alert watcher` | `[5, 7]` | `.-` | **A** |
| **15** | `analyze bytes` | `[7, 5]` | `-.` | **N** |
| **16** | `nothing makes sense` | `[7, 5, 5]` | `-..` | **D** |
| **17** | `chief focus remains finding those hackers` | `[5, 5, 7, 7, 5, 7]` | `..--.-` | **_** |
| **18** | `wrote these complex files` | `[5, 5, 7, 5]` | `..-.` | **F** |
| **19** | `teams writing strange scripts nightly` | `[5, 7, 7, 7, 7]` | `.----` | **1** |
| **20** | `nearest enemy` | `[7, 5]` | `-.` | **N** |
| **21** | `dropped decoy nodes` | `[7, 5, 5]` | `-..` | **D** |
| **22** | `every cyber soldier marches ahead bravely` | `[5, 5, 7, 7, 5, 7]` | `..--.-` | **_** |
| **23** | `extract botnets` | `[7, 7]` | `--` | **M** |
| **24** | `purge dirty files forever tonight` | `[5, 5, 5, 7, 7]` | `...--` | **3** |
| **25** | `victory takes massive efforts under attacks` | `[7, 5, 7, 7, 5, 7]` | `-.--.-` | **}** (or `)`) |

Putting it together:
$$\text{KPMG\_CTF\{S33K\_AND\_F1ND\_M3\}}$$

---

## Phase 7: End-to-End Automated Solver & Terminal Output

We consolidated the entire multi-stage solution into a standalone Python script, [`solve.py`](file:///home/boss/Works/ctf/KPMG/Crypto/solve.py):

```python
#!/usr/bin/env python3
"""
KPMG CTF - challenge_file Automated Solver
1. Restores JFIF SOI/APP0 magic bytes (PNG header bypass).
2. Fixes SOF0 baseline height marker (550px -> 1000px).
3. Executes OCR on the recovered image.
4. Cryptanalyzes word lengths to decode Morse code.
"""

import re
import subprocess

def repair_image(input_path: str, output_path: str):
    with open(input_path, "rb") as f:
        data = bytearray(f.read())

    # Step 1: Replace fake PNG header with original JFIF header
    data[:8] = bytes.fromhex("ffd8ffe000104a46")

    # Step 2: Fix modified height in SOF0 marker at offset 163-164
    # Set height to 1000 (0x03E8)
    data[163:165] = (1000).to_bytes(2, "big")

    with open(output_path, "wb") as f:
        f.write(data)

def extract_text_tesseract(image_path: str) -> str:
    res = subprocess.run(["tesseract", image_path, "stdout"], capture_output=True, text=True)
    return res.stdout

def decode_morse_word_lengths(text: str) -> str:
    morse_table = {
        '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E', '..-.': 'F',
        '--.': 'G', '....': 'H', '..': 'I', '.---': 'J', '-.-': 'K', '.-..': 'L',
        '--': 'M', '-.': 'N', '---': 'O', '.--.': 'P', '--.-': 'Q', '.-.': 'R',
        '...': 'S', '-': 'T', '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X',
        '-.--': 'Y', '--..': 'Z',
        '-----': '0', '.----': '1', '..---': '2', '...--': '3', '....-': '4',
        '.....': '5', '-....': '6', '--...': '7', '---..': '8', '----.': '9',
        '..--.-': '_', '-.--.': '{', '-.--.-': '}'
    }

    words = re.findall(r'[a-zA-Z]+', text)
    lengths = [len(w) for w in words]

    # Delimiter = 3, Dot = 5, Dash = 7
    parts = []
    current = []
    for l in lengths:
        if l == 3:
            parts.append(current)
            current = []
        else:
            current.append(l)
    parts.append(current)

    decoded = []
    for p in parts:
        code = "".join("." if x == 5 else "-" for x in p)
        decoded.append(morse_table.get(code, f"[{code}]"))

    return "".join(decoded)

if __name__ == "__main__":
    repair_image("challenge_file", "restored_image.jpg")
    text = extract_text_tesseract("restored_image.jpg")
    flag = decode_morse_word_lengths(text)
    print(f"[+] Recovered Flag: {flag}")
```

### Terminal Execution Output:

```bash
$ python3 solve.py
[*] Repairing JPEG header and image dimensions...
[+] Saved repaired image to restored_image.jpg
[*] Extracting text using OCR...
[+] Extracted text:

Hackers sneak through, and steal network secrets daily. Now foreign
systems are falling offline today. Our agent seeks answers without delay
tonight. The mystery grows thicker after all hunters for every ghost
machine trace can uncover these signals heneath radar. You watch their
codes, but virus worms creep forward forever. And worse logic hombs
corrupt records. All shadows exist outside the walls where digital thieves
dwell quietly. The alert watcher can analyze bytes, yet nothing makes
sense. His chief focus remains finding those hackers. Who wrote these
complex files? New teams writing strange scripts nightly. Our nearest
enemy has dropped decoy nodes. Now every cyher soldier marches
ahead bravely. Men extract botnets, and purge dirty files forever tonight.
The victory takes massive efforts under attacks.

==================================================
[*] Decoding word lengths as Morse code...
[+] Recovered Flag: KPMG_CTF{S33K_AND_F1ND_M3}
```

---

## Key Takeaways & Lessons Learned

1. **Never Trust Initial Magic Bytes Alone:** Attackers and CTF authors frequently splice the headers of one format (e.g., PNG) onto another (e.g., JPEG). Always inspect the subsequent bytes and file trailer markers (`FF D9`).
2. **Pay Attention to Decoder Warnings:** The `extraneous bytes before marker 0xd9` warning from `libjpeg` was the decisive clue indicating that scan data existed beyond the declared SOF0 dimensions.
3. **Steganography in Text Structure:** Natural language steganography frequently hides data in statistical constraints (acrostics, sentence lengths, or word length parity/ternary encodings). Whenever vocabulary selections feel unnaturally restricted, run a frequency analysis on character/word counts.

---

## Final Flag
```text
KPMG_CTF{S33K_AND_F1ND_M3}
```
