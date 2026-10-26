# KPMG CTF - Challenge 2nd Solution & Writeup

## Challenge Overview
- **Binary**: `challenge2nd`
- **Architecture**: ELF 64-bit LSB PIE executable, x86-64
- **Category**: Reverse Engineering

---

## Results

- **Flag**: `KPMG_CTF{1tDhlCmXbPiKSgAvAqfzWTLTWxOtsIEETWfvb83rOTQI}`

---

## Execution Verification

```bash
$ ./challenge2nd "KPMG_CTF{1tDhlCmXbPiKSgAvAqfzWTLTWxOtsIEETWfvb83rOTQI}"
correct
$ echo $?
0
```

Any incorrect string results in:
```bash
$ ./challenge2nd "wrong_flag"
wrong
```

---

## Detailed Reversing & Analysis

### 1. Anti-Analysis & Decoy / Honeypot Architecture

The binary contains two distinct branches depending on `argc`:

```
main (0x1220):
    cmp edi, 2          ; check if argc == 2
    je  0x1278          ; TRUE -> Real Flag Verification Path
    jmp 0x16d0          ; FALSE -> Decoy Vault (Honeypot Path)
```

1. **The Decoy / Honeypot Branch (`argc != 2`)**:
   - Running `./challenge2nd` without arguments prompts `ENTER PASSWORD > ` and displays an ASCII vault banner.
   - It hashes the input using OpenSSL SHA-256 (`EVP_sha256`) and compares it against a hardcoded hash (`936a185c...`).
   - If solved or forced, it decrypts a fake decoy flag at `0x2340` (XOR `0x55`):
     `KPMG_CTF{y0ur_4r3_w45t1g_t1m3_1_d3c0y_fl4g}` ("you are wasting time, I am decoy flag").

2. **Debugger Evasion**:
   - The ELF section header table (`e_shoff = 0`) and note headers are deliberately corrupted (`bad note description size`).
   - This causes standard debuggers (such as GDB) to crash on assertion failures (`Assertion 'this->section_offsets.size() > idx' failed`).

---

### 2. The Real Flag Path (`argc == 2`)

When invoked with exactly one argument (`./challenge2nd <flag>`), control jumps to `0x1278`:

#### Step 1: Self-Inspection of ELF Headers
The binary reads its own in-memory ELF image:
- Checks `ELF` magic (`0x464c457f`), `EI_CLASS == 2` (64-bit), and `e_phentsize == 0x38`.
- Extracts `e_phnum` (13) and `e_phoff` (`0x40`).
- Gathers data from the last 7 `Elf64_Phdr` structures (`phdrs[6..12]`). Specifically, it extracts the 8-byte `p_paddr` fields (offset `0x18`) into a 56-byte buffer `buf_80`:
  - `p_paddrs = [0xeed9abfe7a474d75, 0x3046c865e590ba1a, 0xc1cf6322542a3383, 0x6405ed93154cbf06, 0xd093265aa2e5c39d, 0x93d8cde6676e54c1, 0x0070c477fca1e37e]`

#### Step 2: Deriving Key and Length
- Reads lowest byte of `e_entry` (`0xa0` at offset `0x18`).
- Computes initial key:
  $$\text{edi}_0 = \text{entry\_low} \oplus e\_phnum \oplus 0x37 = 0xa0 \oplus 13 \oplus 0x37 = 0x9a$$
- Iterates over all 13 program headers with counter $c$ starting at 3:
  - For each `PT_LOAD` segment:
    $$\text{edi} \leftarrow \text{edi} \oplus \left((p\_flags \times c) \oplus (p\_align \gg 12)\right)$$
- Final mixing: $\text{edi} \leftarrow \text{edi} \oplus \mathtt{0xffffffa5} = \mathtt{0xffffff19}$.
- Calculates flag length:
  $$\text{len} = (\text{edi} \oplus \text{buf\_80}[0..3] \oplus 0x5a) \ \& \ 0xff = 54$$

#### Step 3: Byte Decryption Routine
- For each character index $i$ from 0 to 53:
  - $\text{rot} = \text{rol8}(\text{edi} \ \& \ 0xff, i \ \& \ 7)$
  - $\text{val} = \text{buf\_80}[i + 1] \oplus (s_i \ \& \ 0xff) \oplus \text{rot}$
  - where $s_0 = 0x29$, $s_{i+1} = s_i + 0x13$.
- The resulting decrypted bytes are reversed to produce the target string:
  $$\text{flag} = \text{reverse}(\text{decrypted})$$

#### Step 4: Comparison
- Compares `strlen(argv[1]) == 54`.
- Compares `argv[1]` character-by-character against the reversed buffer.
- Prints `correct` if matched, otherwise `wrong`.

---

## Standalone Python Solver (`solve2.py`)

```python
#!/usr/bin/env python3
import struct

def extract_flag(binary_path="challenge2nd"):
    with open(binary_path, "rb") as f:
        elf = f.read()

    e_phentsize = struct.unpack_from("<H", elf, 0x36)[0]
    e_phnum = struct.unpack_from("<H", elf, 0x38)[0]
    e_phoff = struct.unpack_from("<Q", elf, 0x20)[0]

    p_paddrs = []
    for i in range(e_phnum - 7, e_phnum):
        phdr_offset = e_phoff + i * e_phentsize
        paddr = struct.unpack_from("<Q", elf, phdr_offset + 0x18)[0]
        p_paddrs.append(paddr)

    buf_80 = bytearray()
    for paddr in p_paddrs:
        buf_80.extend(struct.pack("<Q", paddr))

    entry_low = elf[0x18]
    edi = entry_low ^ e_phnum ^ 0x37

    ecx = 3
    for i in range(e_phnum):
        phdr_offset = e_phoff + i * e_phentsize
        p_type = struct.unpack_from("<I", elf, phdr_offset)[0]
        p_flags = elf[phdr_offset + 4]
        p_align = struct.unpack_from("<Q", elf, phdr_offset + 0x30)[0]

        if p_type == 1:
            eax = (p_flags * ecx) & 0xffffffff
            esi = (p_align >> 12) & 0xffffffff
            eax ^= esi
            edi ^= eax
            edi &= 0xffffffff
        ecx += 1

    edi = (edi ^ 0xffffffa5) & 0xffffffff
    first_dword = struct.unpack_from("<I", buf_80, 0)[0]
    r10d = (edi ^ first_dword ^ 0x5a) & 0xffffffff
    flag_len = r10d & 0xff

    def rol8(val, n):
        val &= 0xff
        n &= 7
        return ((val << n) | (val >> (8 - n))) & 0xff

    esi = 0x29
    decrypted = bytearray()
    for ebx in range(flag_len):
        shift = ebx & 7
        dl = rol8(edi & 0xff, shift)
        byte_val = buf_80[ebx + 1]
        byte_val ^= (esi & 0xff)
        esi = (esi + 0x13) & 0xffffffff
        byte_val ^= dl
        decrypted.append(byte_val & 0xff)

    return bytes(reversed(decrypted)).decode("utf-8")

if __name__ == "__main__":
    print(f"Decoded Flag: {extract_flag()}")
```
