import requests
import readline

BASE = "http://0.cloud.chals.io:25381"
URL = BASE + "/cmd"

print("PLCTERM-4 Interactive Console")
print("Type 'exit' to quit.\n")

s = requests.Session()

while True:
    try:
        cmd = input("root@plc4:~$ ").strip()
        if not cmd:
            continue
        if cmd.lower() in ("exit", "quit"):
            break
        if cmd == "clear":
            print("\033[2J\033[H", end="")
            continue

        r = s.post(URL, json={"command": cmd}, timeout=15)
        r.raise_for_status()
        data = r.json()

        for line in data.get("lines", []):
            print(line)

    except KeyboardInterrupt:
        print("\nUse 'exit' to quit.")
    except requests.RequestException as e:
        print(f"[HTTP ERROR] {e}")
    except ValueError:
        print("[ERROR] Server returned invalid JSON")
