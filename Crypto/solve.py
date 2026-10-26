import re
import subprocess
from pathlib import Path

def repair_image(input_path: str, output_path: str):
    with open(input_path, "rb") as f:
        data = bytearray(f.read())

    # Step 1: Fix corrupted JPEG header (replaced with PNG header)
    # Original JFIF header prefix: FF D8 FF E0 00 10 4A 46
    data[:8] = bytes.fromhex("ffd8ffe000104a46")

    # Step 2: Fix altered height in SOF0 marker (at offset 158: FF C0 ...)
    # Offset 163-164 contains height (originally truncated to 550 -> 0x0226)
    # Correct height is 1000 -> 0x03e8
    data[163:165] = (1000).to_bytes(2, "big")

    with open(output_path, "wb") as f:
        f.write(data)

def extract_text_tesseract(image_path: str) -> str:
    res = subprocess.run(["tesseract", image_path, "stdout"], capture_output=True, text=True)
    return res.stdout

def decode_morse_word_lengths(text: str) -> str:
    # Morse code lookup table
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

    # Length 3: separator
    # Length 5: dot (.)
    # Length 7: dash (-)
    parts = []
    current = []
    for l in lengths:
        if l == 3:
            parts.append(current)
            current = []
        else:
            current.append(l)
    parts.append(current)

    decoded_chars = []
    for p in parts:
        code = "".join("." if x == 5 else "-" for x in p)
        char = morse_table.get(code, f"[{code}]")
        decoded_chars.append(char)

    return "".join(decoded_chars)

def main():
    input_file = "challenge_file"
    output_image = "restored_image.jpg"

    print("[*] Repairing JPEG header and image dimensions...")
    repair_image(input_file, output_image)
    print(f"[+] Saved repaired image to {output_image}")

    print("[*] Extracting text using OCR...")
    text = extract_text_tesseract(output_image)
    print("[+] Extracted text:\n")
    print(text.strip())
    print("\n" + "=" * 50)

    print("[*] Decoding word lengths as Morse code...")
    flag = decode_morse_word_lengths(text)
    print(f"[+] Recovered Flag: {flag}")

if __name__ == "__main__":
    main()
