# Golden Hour — "I never delete, I just stop pointing"

Full walkthrough: target recon, GitHub OSINT, the client-side vault, geo-location,
and how the final flag falls out of a photo's metadata.

- **Challenge:** Golden Hour (OSINT, 30 pts)
- **Target:** `https://kicyber-807ca136029b-goldenhour-0-0.chals.io`
  (A records `143.244.222.115`, `143.244.222.116`)
- **Category:** OSINT (web recon + geo-location + metadata)
- **Flag format:** `KPMG_CTF{...}`
- **Flag:**

```
KPMG_CTF{n0va_dr1ft3d_h0m3}
```

## Challenge text

> I never delete, I just stop pointing. Everything I walked away from is still out
> there, and the one thing worth keeping, I locked. The key's already yours.

The wording is a tell:

| Line | Meaning |
|---|---|
| "I never delete, I just stop pointing" | Data removed from a repo **is still in git history** |
| "Everything I walked away from is still out there" | Abandoned repos are part of the story |
| "the one thing worth keeping, I locked" | There is a locked object — "the vault" |
| "The key's already yours" | The passphrase is derivable from what you already found |

---

## 0. Recon — the site

`GET /` returns a small static page for a fictional indie dev / coastal photographer,
**Nova Keller**. Two links matter:

- `https://github.com/nova-drifts` — "Code"
- `drop.html` — "...the rest of the keepers live in **the vault**"

```
GET https://kicyber-807ca136029b-goldenhour-0-0.chals.io/
  200  4829 bytes   (index.html)
GET .../drop.html
  200  624159 bytes (the vault — mostly a huge base64 JS blob)
GET .../assets/gallery1..6.jpg
  200             (six gallery photos, no metadata)
```

Directory guessing on the host (`/robots.txt`, `/humans.txt`, `/sitemap.xml`,
`/.git/config`, `/vault.html`, ...) all return `404`/`403` (nginx). The only
servable paths are `/`, `/index.html`, `/drop.html`, and `/assets/*.jpg`.

### Perspective shift #1 — the target is not the webserver

A static nginx site with three pages is not where an OSINT challenge lives. The page
itself points at a **GitHub account**, and the challenge text is explicitly about
**deleted-but-recoverable data**. So the recon target becomes `github.com/nova-drifts`.

---

## 1. GitHub OSINT — `nova-drifts`

```
$ curl -s https://api.github.com/users/nova-drifts
login: nova-drifts     id: 114867635     created: 2022-10-02T14:21:41Z
public_repos: 5        public_gists: 0
name/company/location/blog/email: (all empty)
```

Five repos, no profile bio, no gists:

| Repo | What it is |
|---|---|
| `driftlog` | "personal site, built in the open" — the source of the page we came from |
| `config-archive` | "old dotfiles archive" |
| `dotfiles` | "shell + editor config" |
| `ld53-jam` | "ludum dare 53 prototype" |
| `shader-doodles` | "glsl shader experiments" |

All five are cloned. `driftlog` is the site's source; its `README.md` ends with
"**Shot on film, built in the open.**" — matching the site footer.

### 1.1 "I never delete, I just stop pointing" → git history

`driftlog` has exactly one interesting commit in the middle of its history:

```
437db6b  tidy repo, drop scratch notes     (deletes humans.txt)
70e32f7  initial static site skeleton      (adds humans.txt)
```

`humans.txt` is gone from the working tree but is still reachable from history:

```
$ git -C driftlog cat-file -p a51db964ff1c0c5cd7c55c2fcb572fdd032005ad
Nova Keller
# socials draft - decide which handle I am actually keeping
linkedin: https://www.linkedin.com/in/nova-drifts/
linkedin: https://www.linkedin.com/in/nova-keller-/
```

That is the "stopped pointing" artifact: a deleted socials file that still leaks her
handles. This is the OSINT hinge of the challenge.

### Perspective shift #2 — decoys are planted to catch greppers

Grepping history for `FLAG` yields **two** strings that look like flags. Both are bait:

**`config-archive/old.env`** (repo is deliberately self-aware):

```
# I was pretty sure this was the puzzle flag at one point:
FLAG=KPMG_CTF{n0va_dr1fted_h0m3}
# ...it wasn't. left it here on purpose to catch scrapers. this is a DEAD END.
```

**`driftlog` annotated tag `backup-2024`** (tag object `21c4ead`):

```
pre-cleanup backup, do not ship. leftover prod: FLAG=KPMG_CTF{g0ld3n_h0ur_k33p3r}
tagger: nvk_dev <nvk_dev@users.noreply.github.com>  2026-10-08T20:38:33Z
```

Both literally tell you they are not the answer ("DEAD END", "do not ship"). A hunter
who stops at `git log`/`grep FLAG` submits a decoy. The real flag is only reachable by
finishing the vault chain, so we ignore both and keep going.

> Note also the near-miss: decoy `n0va_dr1fted_h0m3` vs real `n0va_dr1ft3d_h0m3`
> (`ed` → `3d`). Classic "you skimmed the flag" trap.

Other repos (`dotfiles/NOTES.md`, `ld53-jam`, `shader-doodles`) contain only more
"wrong repo / DEAD END" red herrings.

---

## 2. The vault (`drop.html`)

The vault is a **client-side** lock: all crypto happens in the browser. The page loads a
single `var D={...}` blob and two decryption steps.

### 2.1 The crypto (verbatim from the page)

```js
function b64(b){var s=atob(b),u=new Uint8Array(s.length),i=0;for(;i<s.length;i++){u[i]=s.charCodeAt(i);}return u;}
function norm(s){return s.toLowerCase().replace(/[^a-z0-9]/g,'');}
function derive(p,salt,it){
  return crypto.subtle.importKey('raw',new TextEncoder().encode(p),{name:'PBKDF2'},false,['deriveKey'])
    .then(function(base){
      return crypto.subtle.deriveKey(
        {name:'PBKDF2',salt:b64(salt),iterations:it,hash:'SHA-256'},
        base,{name:'AES-GCM',length:256},false,['decrypt']);});
}
function dec(p,blob){return derive(p,blob.s,blob.it).then(function(k){
  return crypto.subtle.decrypt({name:'AES-GCM',iv:b64(blob.iv)},k,b64(blob.d));});}
```

- **KDF:** PBKDF2-HMAC-SHA256, **200000** iterations, 24-byte random salt, 256-bit key.
- **Cipher:** AES-GCM-256 (16-byte IV), authenticated — a wrong key throws, so the key
  is unambiguous.
- **Input normalisation:** `norm(s)` lowercases and strips everything but `[a-z0-9]`.

Two blobs and two keys:

```js
// step 1
dec(norm(input1), D.b1)                      // -> {img, msg}  (stage-1 photo)
// step 2
dec(pass1 + '|' + norm(input2), D.b2)        // -> {img, msg}  (the keeper)
```

- **b1 key** = `norm(passphrase)`
- **b2 key** = `norm(passphrase) + "|" + norm(place)`   (the `pass1` captured from step 1)

Blobs live in `vault.json` / `drop.html` as `{s, iv, d, it}` and were re-implemented
locally with Python `cryptography` (`brute1.py`, `brute2.py`).

### 2.2 Opening step 1 — the passphrase

"The key's already yours." The natural OSINT source for the passphrase is the
**LinkedIn handles** from the deleted `humans.txt` — but LinkedIn serves an auth
wall/redirect to logged-out clients, so the profile content is not directly reachable.

We therefore re-implemented the KDF/cipher and tested a **curated dictionary** built
from the challenge's own vocabulary (persona, repos, captions, handles, story words).
Exactly one candidate authenticates against AES-GCM `b1`:

```
$ python3 brute1.py
FOUND: 'driftwood' norm= driftwood
```

> Passphrase: **`driftwood`** — a coastal/"drift" theme word consistent with the persona
> (`nova-drifts`, `driftlog`). Because GCM authenticates, this is provably *the* key,
> not a lucky guess.

Decrypting `b1` with `driftwood` yields a JSON object containing a base64 JPEG and a
message:

```json
{"img":"data:image/jpeg;base64,/9j/...","msg":"Not done yet - one more step to go! Guess the place in this shot to unlock the flag."}
```

Saved as `stage1.raw` → `stage1_photo.jpeg` (1280x640, **no useful EXIF**).

### Perspective shift #3 — step 2 is not a crypto problem, it is a geo problem

The stage-1 photo carries no metadata and no text. The message is explicit: *"Guess the
place in this shot."* The intended work is **image geo-location**, not more git digging.

---

## 3. Geo-locating the stage-1 photo

The photo (`stage1_photo.jpeg`) shows a squat, tapered white-and-red lighthouse on a
granite point, with a small cove/harbour behind and Atlantic surf. No text, no plates.

Method: **reverse image search**. Yandex Images (`yandex.com/images/search?rpt=imageview&url=<imgurl>`)
returned visually identical photos; Bing/Lens did not. Every match pointed at the same
landmark:

> **Peggy's Cove Lighthouse** (officially **Peggy's Point Lighthouse**),
> Peggy's Cove, Nova Scotia, Canada.

The vault's step-2 input placeholder is the giveaway for the expected format —
`e.g. robberscove` — i.e. **a lower-case, no-space place name**.

### 3.1 Opening step 2 — the place

b2 key = `norm("driftwood") + "|" + norm("peggyscove")` = `driftwood|peggyscove`.

```
$ python3 brute2.py peggyscove
FOUND key='driftwood|peggyscove' input='peggyscove'
{"img":"data:image/jpeg;base64,/9j/...","msg":"Unlocked. Here's the keeper, full resolution - it's yours. (a good photo carries more than the pixels.)"}
```

Saved as `keeper.out` → `keeper.jpeg` (1280x640). A wrong answer produces
`not the place. look at the photo again.`, confirming the check.

---

## 4. The keeper — flag is in the metadata

The step-2 message is the final hint:

> "Here's the keeper, full resolution - it's yours. **(a good photo carries more than
> the pixels.)**"

That is a direct pointer to **image metadata**. The download link in the page is even
named `golden-hour.jpg`. Running `exiftool` on the keeper:

```
$ exiftool keeper.jpeg
...
User Comment : KPMG_CTF{n0va_dr1ft3d_h0m3}
...
Image Size   : 1280x640
```

The flag is stored in the JPEG **EXIF `UserComment`** field:

```
KPMG_CTF{n0va_dr1ft3d_h0m3}
```

("nova drifted home" — `dr1ft3d` with `3` for `e`, matching the leet-speak style of the
near-miss decoy but with the correct letters.)

---

## 5. Complete reproduction (one shot)

```bash
BASE=https://kicyber-807ca136029b-goldenhour-0-0.chals.io

# 1) site + vault
curl -sk "$BASE/"           -o index.html
curl -sk "$BASE/drop.html"  -o drop.html          # contains  var D={...}

# 2) GitHub OSINT
git clone https://github.com/nova-drifts/driftlog
git -C driftlog log --all --oneline
git -C driftlog cat-file -p a51db964ff1c0c5cd7c55c2fcb572fdd032005ad   # deleted humans.txt
curl -s https://api.github.com/repos/nova-drifts/driftlog/git/tags/21c4ead42887023018627f1509557aaad8f0bab8

# 3) vault step 1: passphrase "driftwood"  (PBKDF2-SHA256 200k -> AES-GCM-256)
python3 brute1.py                                  # writes stage1.raw (contains the base64 photo)

# 4) geo-locate stage1_photo.jpeg  ->  Peggy's Cove, Nova Scotia

# 5) vault step 2: key "driftwood|peggyscove"
python3 brute2.py peggyscove                        # prints FOUND line + JSON; saved to keeper.out

# 6) flag is in the keeper EXIF
exiftool keeper.jpeg | grep 'User Comment'
# User Comment : KPMG_CTF{n0va_dr1ft3d_h0m3}
```

---

## 6. Attack-chain summary

1. **Recon the site** → static "Nova Keller" page with a GitHub link and a link to
   `drop.html` ("the vault").
2. **GitHub OSINT** → `nova-drifts`, 5 repos.
3. **"I never delete, I just stop pointing"** → deleted `humans.txt` recovered from
   history; leaks LinkedIn handles (the OSINT hinge).
4. **Ignore planted decoys** → `config-archive old.env` ("DEAD END") and `driftlog` tag
   `backup-2024` ("do not ship / leftover prod") both contain fake flags.
5. **Vault step 1** → PBKDF2-SHA256(200k)+AES-GCM-256; passphrase **`driftwood`** unlocks
   the stage-1 photo.
6. **Geo-locate** the stage-1 photo → **Peggy's Cove Lighthouse, Nova Scotia**.
7. **Vault step 2** → key `driftwood|peggyscove` unlocks the full-resolution keeper.
8. **Flag in metadata** → keeper EXIF `UserComment` = `KPMG_CTF{n0va_dr1ft3d_h0m3}`.

---

## 7. Flags encountered (and why two are wrong)

| Where | String | Verdict |
|---|---|---|
| `config-archive/old.env` | `KPMG_CTF{n0va_dr1fted_h0m3}` | **Decoy** — labeled "DEAD END ... catch scrapers" |
| `driftlog` tag `backup-2024` | `KPMG_CTF{g0ld3n_h0ur_k33p3r}` | **Decoy** — "pre-cleanup backup, do not ship" |
| keeper JPEG EXIF `UserComment` | `KPMG_CTF{n0va_dr1ft3d_h0m3}` | **Real** — end of the intended vault chain |

---

## 8. Lessons / perspective shifts

1. **Follow the story, not the page.** The webserver was a dead end; the challenge text
   ("never delete", "walked away from") pointed at git history and abandoned repos.
2. **Deleted ≠ gone.** `git log --all`, `rev-list --objects --all`, and `cat-file` on the
   dangling blob are the whole OSINT trick.
3. **Decoys are deliberate.** Two "flags" were planted with explicit "do not ship / DEAD
   END" annotations. A grep-and-submit hunter loses. Only the object obtained through the
   full chain is trustworthy.
4. **Read the hint inside the artefact.** "a good photo carries more than the pixels" =
   EXIF. The flag was in metadata, not the image.
5. **Geo-location is OSINT too.** Reverse image search (Yandex worked here) resolved the
   photo to Peggy's Cove; the field's example placeholder confirmed the answer format.

---

## 9. Artefacts in this folder

```
golden_hour/
├── index.html              # site landing page (Nova Keller)
├── drop.html               # the vault (contains var D={...} + decryption JS)
├── vault.json              # extracted {s,iv,d,it} blobs b1/b2
├── brute1.py               # PBKDF2+AES-GCM tester for step 1 (finds "driftwood")
├── brute2.py               # PBKDF2+AES-GCM tester for step 2 (finds "peggyscove")
├── stage1.raw              # decrypted step-1 JSON {img,msg}
├── stage1_photo.jpeg       # the photo to geo-locate  -> Peggy's Cove Lighthouse
├── keeper.out              # decrypted step-2 JSON {img,msg} (+ FOUND key line)
├── keeper.jpeg             # the keeper image; EXIF UserComment = the flag
├── github-recon.txt        # full git history / blobs / decoys dump
├── assets/                 # six gallery photos from the site (no metadata)
└── repos/                  # clones of all five nova-drifts repos
    ├── config-archive/     # old.env -> decoy flag (DEAD END)
    ├── dotfiles/
    ├── driftlog/           # deleted humans.txt + tag backup-2024 (decoy flag)
    ├── ld53-jam/
    └── shader-doodles/
```

## 10. Flag

```
KPMG_CTF{n0va_dr1ft3d_h0m3}
```
