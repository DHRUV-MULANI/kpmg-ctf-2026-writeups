# WESTBOUND — Evidence Index

Raw, reproducible artifacts supporting `../WESTBOUND_WRITEUP.md`.
All paths are relative to `westbound/`.

| File | What it contains |
|------|------------------|
| `proof_png_lsb.txt` | Verbatim message recovered from the LSBs of `proof.png` (incl. the bait flag). |
| `desk_jpg_ocr.txt` | Full Tesseract OCR of `desk.jpg` (`--psm 6` and `--psm 11`) → drop code `7c41f9a2e0b3`. |
| `email_headers.txt` | Raw headers of `phish.eml` (Postfix id `7C41F9A2E0B`, Message-ID `20260309030644.7c41f9a2`). |
| `pcap_http.txt` | `tshark` extraction of every HTTP request/response in `westbound.pcap` (incl. the `velvet-harbor` login). |
| `site_text.txt` | Full text of all five site pages (blog / files / git / vault / vault drop). |
| `call_wav_analysis.txt` | Measured `call.wav` timeline, the exact 1000 Hz beep, and the DTMF `0000` decode. |
| `drawn_text_ocr.txt` | OCR reading of the drawn spectrogram text → `ARCHIVE KEY: s4lt3d-t1d35`. |
| `export_container.txt` | `westbound-export.zip.enc` structure (header/salt/size/cipher). |
| `vault_phrase.txt` | Proof that `sha256("velvet-harbor")` equals the vault page's gate constant. |
| `file_hashes.txt` | MD5 + SHA-256 of every original challenge file. |
| `keys_tried.txt` | 40,013 export-key candidates tested against the `openssl` PBKDF2/AES oracle (all failed). |

## Reproduction one-liners

```bash
# proof.png LSB (bit 0 of RGB, MSB-first)
python3 - <<'EOF'
from PIL import Image; import numpy as np
im=np.array(Image.open('proof.png').convert('RGBA')).reshape(-1,4)
bits=(im[:,:3].reshape(-1)&1); out=bytearray()
for i in range(0,len(bits)-7,8):
    b=0
    for j in range(8): b=(b<<1)|int(bits[i+j])
    out.append(b)
print(bytes(out).split(b'\x00')[0].decode())
EOF

# vault phrase check
python3 -c "import hashlib;print(hashlib.sha256(b'velvet-harbor').hexdigest())"
#   -> 251eb9febd456d3f6b3e16aff9f0c90faec5c29ac2ed01cbfd143762a11c6eed  (matches page H)

# desk OCR
tesseract desk.jpg - --psm 6

# pcap HTTP transcript
tshark -r westbound.pcap -Y http -T fields \
  -e frame.number -e http.request.method -e http.host -e http.request.uri -e http.file_data

# export oracle (a real hit must start with PK\x03\x04)
python3 - <<'EOF'
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
d=open('westbound-export.zip.enc','rb').read(); SALT,CT=d[8:16],d[16:]
def oracle(pw):
    dk=hashlib.pbkdf2_hmac('sha256',pw.encode() if isinstance(pw,str) else pw,SALT,10000,48)
    c=Cipher(algorithms.AES(dk[:32]),modes.CBC(dk[32:])).decryptor()
    p=c.update(CT)+c.finalize(); pad=p[-1]
    return p[:-pad] if (1<=pad<=16 and p[-pad:]==bytes([pad])*pad) else None
print('0000 ->', oracle('0000') is not None, '(padding-passing only; never PK)')
EOF
```

## Flags / strings recovered

- **✅ REAL FLAG:** `KPMG_CTF{o_-ODQ02brB5QsTNAdKsWH7FSvp99ue50bXlSRGd2JOj}`
- **Bait flag (do NOT submit):** `KPMG_CTF{n0t_th3_r34l_0n3}`
- Door phrase: `velvet-harbor`
- Drop code: `7c41f9a2e0b3`
- Drawn bait value: `s4lt3d-t1d35`
- DTMF: `0000`
- **Result: SOLVED** — the real marker above was recovered from the decrypted export.
