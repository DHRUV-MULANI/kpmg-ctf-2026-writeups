# Latitude of Injection — KPMG / KICyb3r CTF (Mobile, 20 pts)

**Target:** `http://kicyber-7849816404f5-latitude-of-injectio-0-0.chals.io` (redirects to HTTPS)
**Artifact:** `loi_v1.apk` (package `com.ctf.loi`, app label `Latitude of Injection`)
**Category:** Mobile / Web
**Difficulty:** Easy–Medium (20 points)

> An Android app and a small backend guard a secret. Analyze the app, interact with the
> server, and obtain the flag by demonstrating administrative access. The flag is returned
> by the web endpoint.

## Flag

```
KPMG_CTF{LLPs0wc8yOqktZ_2YCr4bGOmoMp6D69u1l3t553TUfOu}
```

## TL;DR

The APK is a Jetpack‑Compose demo app around a local SQLite database. The "sign up" flow
builds an `INSERT` statement by string concatenation, so a crafted name injects a row with
`is_admin = 1`. Logging in as that row reaches the (client‑side) **Admin Panel**, whose
"Privileged info" is the string resource `not_required7`, a base64 blob. Decoding it once
yields the backend's `secret`. The backend also gates on a `city`, which the app reveals via
its hardcoded geofence (`55.7558, 37.6173` → **Moscow**). Posting
`city=Moscow & secret=rGc7~49t7WWJ~hMf77` returns the flag.

| Field  | Value | Where it comes from |
|--------|-------|---------------------|
| city   | `Moscow` | app geofence `l1=55.7558`, `l2=37.6173` (`res/values/strings.xml`) |
| secret | `rGc7~49t7WWJ~hMf77` | base64‑decode of `not_required7` (`ckdjN340OXQ3V1dKfmhNZjc3`) |

---

## 1. Recon

### 1.1 Web endpoint

```bash
$ curl -sk -i https://kicyber-7849816404f5-latitude-of-injectio-0-0.chals.io/
HTTP/1.1 200 OK
Server: Werkzeug/3.1.3 Python/3.11.14
...
```

The root page is a Flask "CTF Flag Server" with a form:

```html
<h2>Enter Secret &amp; City</h2>
<form method="post">
    <input type="text" name="city"   placeholder="City"            required>
    <input type="text" name="secret" placeholder="Privileged Info" required>
    <button type="submit">Get Flag</button>
</form>
```

The placeholder `Privileged Info` is the exact phrase the Android app prints on its Admin
Panel — that is the link between the two halves of the challenge.

All incorrect attempts return the same generic message (no SQL error surface, no injection
here):

```html
<div class="message error">Invalid input!</div>
```

So the goal becomes: **find the correct `city` and `secret` by reversing the APK.**

### 1.2 APK triage

```bash
unzip loi_v1.apk -d apk_extract
# classes.dex, classes2..5.dex, resources.arsc, assets/img.jfif, lib/, res/, ...
strings classes4.dex | grep -iE "SELECT|INSERT|admin|http|flag"
```

`classes4.dex` holds all of `com.ctf.loi` (the challenge code, built in debug mode,
min-api 29). Immediate red flags:

```
INSERT INTO users (name, email, is_admin) VALUES ('   <- string-concatenated SQL
SELECT id, name, email, is_admin FROM users WHERE LOWER(name) = ? LIMIT 1   <- parameterized (safe)
admin@local
Admin Panel
Privileged info:
VULN_INSERT:
createUserVulnerable error:
you dont have the admin role.
```

Decompile with `jadx`:

```bash
jadx -d jadx_out --no-res --no-imports loi_v1.apk
jadx -d jadx_res --no-src --no-imports loi_v1.apk   # resources / AndroidManifest
```

### 1.3 AndroidManifest.xml (highlights)

```xml
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION"/>
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
<uses-permission android:name="android.permission.INTERNET"/>
<application android:label="@string/app_name" android:debuggable="true">
    <activity android:name="com.ctf.loi.MainActivity" android:exported="true"> ... </activity>
</application>
```

`android:debuggable="true"` and the location permissions tell us the app cares about
geolocation; the custom code is in `com.ctf.loi`.

### 1.4 The geofence and the encoded strings (`res/values/strings.xml`)

```xml
<string name="app_name">Latitude of Injection</string>
<string name="l1">55.7558</string>     <!-- allowed latitude  (Moscow) -->
<string name="l2">37.6173</string>     <!-- allowed longitude (Moscow) -->
<string name="al_r">300000.0</string>  <!-- allowed radius (m) -->
<string name="not_required1">ozhROjpOak15bjExOGtrOn03</string>
...
<string name="not_required7">ckdjN340OXQ3V1dKfmhNZjc3</string>
...
<string name="not_required10">VD43RjM2dDx1cHZiOHFcNC84</string>
```

`MainActivity.onCreate` reads `l1`, `l2`, `al_r` and passes them to the UI for the distance
check (`com.ctf.loi.Utils.distanceMeters`, a haversine). The app only lets you sign up / log
in while inside a **300 km** radius of **55.7558, 37.6173 → Moscow**.

The ten `not_requiredN` values are base64.

---

## 2. Static analysis of the vulnerable code

### 2.1 `LocalDbHelper` — the SQL injection

`analysis/sources/LocalDbHelper.java`:

```java
@Override
public void onCreate(SQLiteDatabase db) {
    db.execSQL("CREATE TABLE users (" +
        "id INTEGER PRIMARY KEY AUTOINCREMENT," +
        "name TEXT, email TEXT, is_admin INTEGER DEFAULT 0)");
    db.execSQL("INSERT INTO users (name, email, is_admin) VALUES ('alice', 'alice@example.com', 0)");
    db.execSQL("INSERT INTO users (name, email, is_admin) VALUES ('bob',   'bob@example.com',   0)");
}

// NOTE: never called anywhere -> the DB starts with NO admin.
public final void seedAdmin() {
    Cursor c = getWritableDatabase().rawQuery(
        "SELECT id FROM users WHERE is_admin = 1 LIMIT 1", null);
    if (!c.moveToFirst()) {
        ContentValues v = new ContentValues();
        v.put("name", ""); v.put("email", "admin@local"); v.put("is_admin", 1);
        getWritableDatabase().insert("users", null, v);
    }
}

/** VULNERABLE: user input concatenated straight into SQL. */
public final void createUser(String name, String email) {
    String sql = "INSERT INTO users (name, email, is_admin) VALUES ('"
               + name + "', '" + email + "', 0);";
    Log.i("LocalDbHelper", "VULN_INSERT: " + sql);
    getWritableDatabase().execSQL(sql);
}

/** SAFE: parameterised. */
public final UserRow safeFindByName(String name) {
    Cursor c = getReadableDatabase().rawQuery(
        "SELECT id, name, email, is_admin FROM users WHERE LOWER(name) = ? LIMIT 1",
        new String[]{ name.toLowerCase(Locale.ROOT) });
    ...
}
```

`SignupScreen` calls `dbHelper.createUser(name, email)` with fully attacker-controlled
`name`. Because the `is_admin` literal is fixed to `0` only *outside* the injection point,
a name that closes the string literal can rewrite the whole row:

```
name  = x', 'x@x.com', 1) -- 
email = anything

resulting SQL:
INSERT INTO users (name, email, is_admin) VALUES ('x', 'x@x.com', 1) -- ', 'anything', 0);
                                                                     ^^^ rest commented out
```

This inserts a row with `is_admin = 1`. This is the "**demonstrating administrative access**"
step the challenge describes.

### 2.2 The login → admin flow

`ScreensKt$AppRoot$2$2` (decompiled lambda):

```java
// login success
if (userRow.isAdmin() != 1) {                          // not admin
    snackbar("Welcome, " + userRow.getName());
    screen = "home";
} else {                                               // admin
    currentAdminUser = userRow;
    screen = "admin";                                  // -> AdminScreen
}
```

`safeFindByName` is parameterized, so the login itself is not injectable — you just log in
with the plain-name part of your injected row (`x`).

### 2.3 `AdminScreen` and the "Privileged info"

`ScreensKt.AdminScreen` builds a `ScreensKt$AdminScreen$1$1` with the hardcoded placeholders
`("admin", "admin@local")`, then renders `privilegedInfo`:

```java
// ScreensKt.AdminScreen  (debug decompilation, Screens.kt:336-402)
Button("Admin Panel");
Text("Privileged info:");
Text(privilegedInfo);          // <-- the secret
```

`ScreensKt$AdminScreen$1$1.invokeSuspend`:

```java
if (adminUser == null || adminUser.isAdmin() != 1) {
    // (dead branch in practice) query the DB for the first admin's email,
    // suppressing it only when name=="admin" && email=="admin@local"
} else {
    privilegedInfo = ctx.getString(R.string.not_required7);
}
```

Since the screen is only reachable *after* logging in as an admin (`isAdmin == 1`), the value
shown to a legitimate administrator is exactly:

```
R.string.not_required7 = "ckdjN340OXQ3V1dKfmhNZjc3"
```

That base64 blob, decoded once, is the backend secret:

```bash
$ echo ckdjN340OXQ3V1dKfmhNZjc3 | base64 -d
rGc7~49t7WWJ~hMf77
```

For completeness, all ten `not_requiredN` values decode to:

| res | base64 | decoded (raw) |
|-----|--------|---------------|
| 1  | `ozhROjpOak15bjExOGtrOn03` | `\xa38Q::NjMyn118kk:}7` |
| 2  | `bVdMPSMuIVAzO1ZrMic2YnA5` | `mWL=#.!P3;Vk2'6bp9` |
| 3  | `b0lfWkY2UjhwUjp7MTAweTYw` | `oI_ZF6R8pR:{100y60` |
| 4  | `TTcwTWI5RDJlNFEuPDd5XWoz` | `M70Mb9D2e4Q.<7y]j3` |
| 5  | `Rz85KHc1VjA0SW4/Kj43RTYy` | `G?9(w5V04In?*>7E62` |
| 6  | `aW9ESDRYPk9rJHB2TzY4Il1g` | `ioDH4X>Ok$pvO68"]\`` |
| **7** | **`ckdjN340OXQ3V1dKfmhNZjc3`** | **`rGc7~49t7WWJ~hMf77`**  ← used |
| 8  | `Tn1jPCokL3hNazMxTUJNbDRu` | `N}c<*$/xMk31MBMl4n` |
| 9  | `eWcoQ1RCNyZcJGUlNlE0VHxK` | `yg(CTB7&\$e%6Q4T|J` |
| 10 | `VD43RjM2dDx1cHZiOHFcNC84` | `T>7F36t<upvb8q\4/8` |

Only `not_required7` is referenced by the admin panel; the others are distractors.

---

## 3. Server interaction → flag

With `city = Moscow` (from the geofence) and `secret = rGc7~49t7WWJ~hMf77`:

```bash
$ curl -sk -X POST https://kicyber-7849816404f5-latitude-of-injectio-0-0.chals.io/ \
       --data-urlencode "city=Moscow" \
       --data-urlencode "secret=rGc7~49t7WWJ~hMf77"
```

Response:

```html
<div class="message success">Here is your flag: KPMG_CTF{LLPs0wc8yOqktZ_2YCr4bGOmoMp6D69u1l3t553TUfOu}</div>
```

Any other value (including the raw base64 `ckdjN340OXQ3V1dKfmhNZjc3`) yields
`Invalid input!`, confirming the single extra base64 step.

---

## 4. Complete attack chain (as a real device would see it)

1. **Bypass / satisfy the geofence.** Install the APK and mock the device location inside a
   300 km radius of Moscow, or set coordinates near `55.7558, 37.6173` (emulator / Frida /
   "Retry Location"). The app otherwise locks signup and login
   (`"Services not available in your country."`).
2. **SQL injection on sign‑up.** Name = `x', 'x@x.com', 1) -- `, email = anything.
   `createUser()` concatenates the name into the `INSERT`, creating an admin row.
   (The app logs the payload: `V4 VULN_INSERT: INSERT INTO users (name, email, is_admin)
   VALUES ('x', 'x@x.com', 1) -- ', '...', 0);`.)
3. **Log in** with name `x`. `safeFindByName` returns the row with `is_admin = 1`; `AppRoot`
   routes to the **Admin Panel**.
4. **Read the "Privileged info":** `ckdjN340OXQ3V1dKfmhNZjc3` → base64‑decode →
   `rGc7~49t7WWJ~hMf77`.
5. **Submit** `city=Moscow`, `secret=rGc7~49t7WWJ~hMf77` to the Flask endpoint → **flag**.

Automated (no device required) replica of steps 3–5 lives in `exploit.py` / `exploit.sh`.

---

## 5. Root cause & remediation

**Root cause.** The Android client writes to SQLite with string‑concatenated SQL
(`createUser`), and the "privileged" value that guards the backend is shipped as a static
string resource inside the APK. Both the vulnerable row creation and the secret are fully
recoverable by static analysis — no runtime needed.

**Remediation.**

- Use parameterised writes / `ContentValues` on the client, e.g.
  `db.insert("users", null, values)` or `execSQL(sql, args)` — never concatenate input.
  (`safeFindByName` already shows the correct pattern.)
- Never treat client‑side state (an `is_admin` column in a local, `debuggable` DB) as a
  security boundary. Authorisation must be enforced server‑side.
- Do not ship secrets in resources/strings; use a secret store and rotate on leakage.
- Ship release builds with `android:debuggable="false"`; consider stripping logging
  (`VULN_INSERT`, location debug logs) and obfuscation.

---

## 6. Repository layout

```
Mobile/
├── loi_v1.apk                     # challenge artifact (original)
├── WRITEUP.md                     # this file
├── exploit.py                     # automated flag retrieval
├── exploit.sh                     # same, shell/curl one-liner
├── flag.txt                       # recovered flag
├── evidence/
│   └── flag_response.html         # raw successful server response
├── analysis/
│   ├── AndroidManifest.xml        # decoded manifest
│   ├── sources/                   # jadx decompiled com.ctf.loi/*
│   │   ├── LocalDbHelper.java     # the SQL injection (createUser)
│   │   ├── MainActivity.java      # geofence wiring
│   │   ├── ScreensKt.java         # UI / login / admin routing
│   │   ├── ScreensKt.debug.java   # debug-level decompilation (AdminScreen etc.)
│   │   ├── ScreensKt$AdminScreen$1$1.java
│   │   ├── ScreensKt$AdminScreen$1$1$adminEmail$1.java
│   │   └── UserRow.java, Utils.java, R.java, ...
│   └── res/strings.xml            # l1/l2/al_r + not_required1..10
└── work/                          # raw extraction/decompilation workspace
```

## 7. Reproduce

```bash
cd Mobile
python3 exploit.py
# [*] City   (from app geofence 55.7558,37.6173) : Moscow
# [*] Secret (base64-decoded not_required7)      : rGc7~49t7WWJ~hMf77
# [+] Here is your flag: KPMG_CTF{LLPs0wc8yOqktZ_2YCr4bGOmoMp6D69u1l3t553TUfOu}
```
