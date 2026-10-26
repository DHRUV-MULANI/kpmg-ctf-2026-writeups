# KPMG CTF - Challenge Solution & Writeup

## Challenge Overview
- **Binary**: `challenge`
- **Architecture**: ELF 64-bit LSB executable, x86-64
- **Category**: Reverse Engineering

---

## Results

- **Access Key**: `S4f3-BYPASS42`
- **Flag**: `KPMG_CTF{Y22Uz_coNpabbVfyPwovv7_s7jHm_13-ZxFfkf7rVD3P}`

---

## Execution Verification

```bash
$ ./challenge <<< "S4f3-BYPASS42"
====================================
        LOGIC BYPASS // AUTH        
====================================
A secret is protected by a local check.
Your goal is to make the binary approve access.
Enter access key: [ACCESS GRANTED]
Flag: KPMG_CTF{Y22Uz_coNpabbVfyPwovv7_s7jHm_13-ZxFfkf7rVD3P}
```

---

## Detailed Reversing & Analysis

### 1. Program Flow
The `main` function performs the following steps:
1. Prompts for an access key via `fgets()`.
2. Trims trailing newlines using `strcspn()`.
3. Calls `validate_password(input)`.
4. If validation succeeds:
   - Prints `[ACCESS GRANTED]`.
   - Calls `decode_flag(buffer, 0x37)`.
   - Displays `Flag: %s`.

### 2. Flag Decoding Routine (`decode_flag`)
The disassembly of `decode_flag` reveals that the decryption logic does not depend on user input:
- **Encrypted Flag Buffer**: Located at `0x402040` (`ENC_FLAG`), length 54 bytes (`0x36`).
- **Decryption Key**: Located at `0x402020` (`FLAG_KEY`), length 8 bytes (`b"Z\x17\xc0\xde\x137Bi"`).
- **Operation**:
  $$\text{flag}[i] = \text{ENC\_FLAG}[i] \oplus \text{FLAG\_KEY}[i \pmod 8] \quad \text{for } 0 \le i < 54$$

### 3. Access Key Validation (`validate_password`)
The input is checked in three phases:
1. **Sanity Check (`looks_reasonable`)**:
   - $6 \le \text{length} \le 48$.
   - Must contain at least one uppercase letter, one lowercase letter, and one digit.
   - Must not contain whitespace.

2. **Hash Check**:
   - Computes FNV-1a 32-bit hash: $H = \text{fnv1a32}(\text{password})$.
   - Checks:
     $$H \oplus \text{weird\_mix}(H, \mathtt{0x5a17c0de}) == \mathtt{0x46b31fef}$$
   - Exhaustive search over the 32-bit state space yields only two matching candidates, with $H = \mathtt{0x8b05f10a}$ being valid for printable text.

3. **Mixing Transformation (`transform_password`)**:
   - Initializes $\text{state}_0 = H \oplus \mathtt{0xc0dec0de}$.
   - For $i = 0 \dots 15$:
     - Byte $c_i = \text{password}[i]$ if $i < \text{len}$ else $(i \oplus \mathtt{0xa5})$.
     - $\text{state} \leftarrow \text{state} \oplus (c_i \times (i \times 97 + \mathtt{0x45d9}))$.
     - $\text{state} \leftarrow \text{state} + \mathtt{0x7f4a7c15}$.
     - $\text{state} \leftarrow \text{rol32}(\text{state}, (i \pmod 7) + 1)$.
     - $\text{state} \leftarrow \text{state} + (\text{state} \gg 16)$.
     - Output byte verified against $\text{table}[i] \oplus \text{expected}[i]$.
   - Solving step-by-step for printable ASCII yields the key: `S4f3-BYPASS42`.

---

## Standalone Python Solver

```python
#!/usr/bin/env python3

def extract_flag(binary_path="challenge"):
    with open(binary_path, "rb") as f:
        # FLAG_KEY is at virtual address 0x402020 (file offset 0x2020)
        f.seek(0x2020)
        flag_key = f.read(8)
        
        # ENC_FLAG is at virtual address 0x402040 (file offset 0x2040)
        f.seek(0x2040)
        enc_flag = f.read(54)

    flag = bytes([enc_flag[i] ^ flag_key[i % 8] for i in range(54)])
    return flag.decode("utf-8")

if __name__ == "__main__":
    flag = extract_flag()
    print(f"Decoded Flag: {flag}")
```
