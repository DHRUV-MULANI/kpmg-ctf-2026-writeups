# Challenge Writeup: chall.enc

- **Category:** Crypto
- **Challenge File:** [chall.enc](file:///home/boss/Works/ctf/KPMG/Crypto/chall.enc)
- **Hint / Description:**  
  > *"Our old sysadmin loved stacking things - layer after layer, like he was trying to make you cry before you got to the middle. We found this on a decommissioned box. Peel it back."*

---

## Analysis & Layers

The hint mentions peeling back layers "like he was trying to make you cry" (referencing an onion's layers). Inspecting the file reveals multiple cascaded encodings:

### 1. Layer 1 — Binary to ASCII
The file contains space-separated 8-bit binary numbers.
- **Conversion:** Each 8-bit chunk is parsed into an ASCII character.
- **Output:**
  ```text
  NTA0YjRlNTQ1ZjU4NDc1NTdiNmIzMzMzNmY1ZjY3NzMzMzVmNmYzNDYyMzM2OTY4NWY2ZjMxNzAzMzVmMzQ2ZDVmMzA2ZDMxMzA2ZDdk
  ```

### 2. Layer 2 — Base64
The resulting ASCII string is a Base64-encoded string.
- **Conversion:** Standard Base64 decoding.
- **Output:**
  ```text
  504b4e545f5847557b6b33336f5f6773335f6f34623369685f6f3170335f346d5f306d31306d7d
  ```

### 3. Layer 3 — Hex to Text
The output is an ASCII hexadecimal string.
- **Conversion:** Hex-to-ASCII decoding (`bytes.fromhex(...)`).
- **Output:**
  ```text
  PKNT_XGU{k33o_gs3_o4b3ih_o1p3_4m_0m10m}
  ```

### 4. Layer 4 — Atbash Cipher
The format resembles a flag (`PKNT_XGU{...}`). Applying an **Atbash cipher** substitution ($A \leftrightarrow Z$, $B \leftrightarrow Y$, etc.):
- `P` $\rightarrow$ `K`
- `K` $\rightarrow$ `P`
- `N` $\rightarrow$ `M`
- `T` $\rightarrow$ `G`
- `_` $\rightarrow$ `_`
- `X` $\rightarrow$ `C`
- `G` $\rightarrow$ `T`
- `U` $\rightarrow$ `F`
- `k33o_gs3_o4b3ih_o1p3_4m_0m10m` $\rightarrow$ `p33l_th3_l4y3rs_l1k3_4n_0n10n`

---

## Python Solver

```python
import base64

# Step 1: Read binary data
with open("chall.enc", "r") as f:
    raw_data = f.read().strip()

# Layer 1: Binary to Text
layer1 = bytes([int(b, 2) for b in raw_data.split()]).decode()

# Layer 2: Base64 decode
layer2 = base64.b64decode(layer1).decode()

# Layer 3: Hex decode
layer3 = bytes.fromhex(layer2).decode()

# Layer 4: Atbash Cipher
flag = []
for c in layer3:
    if "a" <= c <= "z":
        flag.append(chr(ord("z") - (ord(c) - ord("a"))))
    elif "A" <= c <= "Z":
        flag.append(chr(ord("Z") - (ord(c) - ord("A"))))
    else:
        flag.append(c)

print("Flag:", "".join(flag))
```

---

## Flag

```
KPMG_CTF{p33l_th3_l4y3rs_l1k3_4n_0n10n}
```
