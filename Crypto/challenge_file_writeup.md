# Challenge Writeup: challenge_file

- **Category:** Crypto / Steganography / Forensics
- **Challenge File:** [challenge_file](file:///home/boss/Works/ctf/KPMG/Crypto/challenge_file)
- **Solver Script:** [solve.py](file:///home/boss/Works/ctf/KPMG/Crypto/solve.py)
- **Restored Image:** [restored_image.jpg](file:///home/boss/Works/ctf/KPMG/Crypto/restored_image.jpg)

---

## 1. File Inspection & Header Repair

Inspecting the initial bytes of `challenge_file`:
```
89 50 4E 47 0D 0A 1A 0A 49 46 00 01 01 00 ...
```
- The first 8 bytes (`\x89PNG\r\n\x1a\n`) represent a PNG header signature.
- However, the bytes immediately following are `49 46` ("IF") followed by JFIF marker structure and quantization tables (`FF DB`), ending with JPEG EOI marker `FF D9`.
- The first 8 bytes were intentionally overwritten with PNG magic bytes over what should have been `FF D8 FF E0 00 10 4A 46` (JFIF SOI + APP0).

Restoring the first 8 bytes turns the file into a valid JPEG image:
```python
data[:8] = bytes.fromhex("ffd8ffe000104a46")
```

---

## 2. Dimension Repair (SOF0 Marker)

Upon decoding, libjpeg reports:
```
Corrupt JPEG data: 179702 extraneous bytes before marker 0xd9
```
Inspecting the SOF0 marker (`FF C0`) at offset `158`:
- Dimensions are defined as `800 x 550` (offset `163-164` has `0x0226` = 550).
- This cropped out roughly half of the image where the hidden text paragraph resides.
- Testing the MCU decoding boundaries indicates the true height is **1000 pixels** (`0x03E8`).

Restoring the height at offset `163:165` to `1000` (`\x03\xe8`) fully reveals the hidden paragraph.

---

## 3. Cryptographic Pattern in Text (Word Length Morse Code)

The revealed text contains 125 words:
> *"Hackers sneak through, and steal network secrets daily. Now foreign systems are falling offline today..."*

Analyzing the lengths of each word:
- Lengths consist exclusively of odd numbers: **3, 5, and 7**.
- Frequency distribution:
  - Length `3`: Exactly 25 occurrences (acts as character/token separator)
  - Length `5`: 49 occurrences
  - Length `7`: 51 occurrences

Mapping to **Morse Code**:
- Length `3` = Delimiter (Space)
- Length `5` = Dot (`.`)
- Length `7` = Dash (`-`)

### Decoding Table:
| Part | Word Lengths | Morse Pattern | Decoded Character |
| :--- | :--- | :--- | :--- |
| 0 | 7, 5, 7 | `-.-` | `K` |
| 1 | 5, 7, 7, 5 | `.--.` | `P` |
| 2 | 7, 7 | `--` | `M` |
| 3 | 7, 7, 5 | `--.` | `G` |
| 4 | 5, 5, 7, 7, 5, 7 | `..--.-` | `_` |
| 5 | 7, 5, 7, 5 | `-.-.` | `C` |
| 6 | 7 | `-` | `T` |
| 7 | 5, 5, 7, 5 | `..-.` | `F` |
| 8 | 7, 5, 7, 7, 5 | `-.--.` | `{` (or `(`) |
| 9 | 5, 5, 5 | `...` | `S` |
| 10 | 5, 5, 5, 7, 7 | `...--` | `3` |
| 11 | 5, 5, 5, 7, 7 | `...--` | `3` |
| 12 | 7, 5, 7 | `-.-` | `K` |
| 13 | 5, 5, 7, 7, 5, 7 | `..--.-` | `_` |
| 14 | 5, 7 | `.-` | `A` |
| 15 | 7, 5 | `-.` | `N` |
| 16 | 7, 5, 5 | `-..` | `D` |
| 17 | 5, 5, 7, 7, 5, 7 | `..--.-` | `_` |
| 18 | 5, 5, 7, 5 | `..-.` | `F` |
| 19 | 5, 7, 7, 7, 7 | `.----` | `1` |
| 20 | 7, 5 | `-.` | `N` |
| 21 | 7, 5, 5 | `-..` | `D` |
| 22 | 5, 5, 7, 7, 5, 7 | `..--.-` | `_` |
| 23 | 7, 7 | `--` | `M` |
| 24 | 5, 5, 5, 7, 7 | `...--` | `3` |
| 25 | 7, 5, 7, 7, 5, 7 | `-.--.-` | `}` (or `)`) |

---

## Flag

```text
KPMG_CTF{S33K_AND_F1ND_M3}
```
