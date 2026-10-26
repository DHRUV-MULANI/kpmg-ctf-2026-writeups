#!/usr/bin/env python3
import struct

def extract_flag(binary_path="challenge2nd"):
    with open(binary_path, "rb") as f:
        elf = f.read()

    # Validate ELF header
    if elf[:4] != b"\x7fELF" or elf[4] != 2:
        raise ValueError("Invalid 64-bit ELF binary")

    e_phentsize = struct.unpack_from("<H", elf, 0x36)[0]
    e_phnum = struct.unpack_from("<H", elf, 0x38)[0]
    e_phoff = struct.unpack_from("<Q", elf, 0x20)[0]

    # Read p_paddr (offset 0x18 within Elf64_Phdr) from last 7 program headers
    p_paddrs = []
    for i in range(e_phnum - 7, e_phnum):
        phdr_offset = e_phoff + i * e_phentsize
        paddr = struct.unpack_from("<Q", elf, phdr_offset + 0x18)[0]
        p_paddrs.append(paddr)

    buf_80 = bytearray()
    for paddr in p_paddrs:
        buf_80.extend(struct.pack("<Q", paddr))

    # Calculate initial EDI state from ELF entry byte and e_phnum
    entry_low = elf[0x18]
    edi = entry_low ^ e_phnum ^ 0x37

    # Iterate over program headers
    ecx = 3
    for i in range(e_phnum):
        phdr_offset = e_phoff + i * e_phentsize
        p_type = struct.unpack_from("<I", elf, phdr_offset)[0]
        p_flags = elf[phdr_offset + 4]
        p_align = struct.unpack_from("<Q", elf, phdr_offset + 0x30)[0]

        if p_type == 1:  # PT_LOAD
            eax = (p_flags * ecx) & 0xffffffff
            esi = (p_align >> 12) & 0xffffffff
            eax ^= esi
            edi ^= eax
            edi &= 0xffffffff
        ecx += 1

    edi = (edi ^ 0xffffffa5) & 0xffffffff

    # Compute flag length
    first_dword = struct.unpack_from("<I", buf_80, 0)[0]
    r10d = (edi ^ first_dword ^ 0x5a) & 0xffffffff
    flag_len = r10d & 0xff

    # Decrypt bytes
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

    # In binary, characters are reversed into rsp+0x40
    flag = bytes(reversed(decrypted)).decode("utf-8")
    return flag

if __name__ == "__main__":
    flag = extract_flag()
    print(f"Decoded Flag: {flag}")
