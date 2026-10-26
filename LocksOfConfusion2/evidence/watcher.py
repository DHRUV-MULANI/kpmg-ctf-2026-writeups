#!/usr/bin/env python3
"""Tails sshd's auth log, scores per-IP suspicion, and reacts."""
import os
import re
import subprocess
import threading
import time
from collections import defaultdict, deque

AUTH_LOG = os.environ.get("AUTH_LOG", "/var/log/auth.log")
INCIDENTS_DIR = os.environ.get("INCIDENTS_DIR", "/var/log/watcher/incidents")

THRESHOLD = int(os.environ.get("WATCHER_THRESHOLD", "100"))
WINDOW_SECONDS = int(os.environ.get("WATCHER_WINDOW", "10"))
RATE_LIMIT = int(os.environ.get("WATCHER_INVALID_USER_LIMIT", "5"))
FAIL_PUBKEY_LIMIT = int(os.environ.get("WATCHER_FAIL_LIMIT", "3"))
BAN_COOLDOWN = int(os.environ.get("WATCHER_BAN_COOLDOWN", "20"))

# Common default/scanner usernames -- credential-stuffing bots try these first.
SCANNER_USERNAMES = [
    "root", "admin", "test", "ubuntu", "pi", "guest", "oracle", "postgres",
    "git", "deploy", "jenkins",
]

# Bait: looks like a plausible secondary service account. Hitting it is a much
# harsher penalty than plain scanning -- a red herring for anyone who goes for
# "obvious" wins first.
BAIT_USERNAME = "backup-admin"

SCORE_SCANNER_USERNAME = 30
SCORE_INVALID_RATE = 10
SCORE_FAILED_PUBKEY = 20
SCORE_BAIT = 50

INVALID_USER_RE = re.compile(r"Invalid user (.*) from ([0-9a-fA-F:.]+) port \d+")
FAILED_PUBKEY_RE = re.compile(r"Failed publickey for (\S+) from ([0-9a-fA-F:.]+) port \d+")

state_lock = threading.Lock()
ip_score = defaultdict(int)
ip_invalid_times = defaultdict(deque)
ip_fail_pubkey_times = defaultdict(deque)
banned_until = {}


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def ban_ip(ip):
    check = sh(["iptables", "-C", "INPUT", "-s", ip, "-j", "DROP"])
    if check.returncode != 0:
        sh(["iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"])
    banned_until[ip] = time.time() + BAN_COOLDOWN


def unban_expired():
    now = time.time()
    for ip, until in list(banned_until.items()):
        if now >= until:
            sh(["iptables", "-D", "INPUT", "-s", ip, "-j", "DROP"])
            del banned_until[ip]


def sanitize_username_for_filename(name):
    # Only strip path separators and null bytes -- nothing else.
    return name.replace("/", "").replace("\x00", "")


def write_incident(ip, username, score):
    os.makedirs(INCIDENTS_DIR, exist_ok=True)
    name = sanitize_username_for_filename(username).strip()
    if not name:
        name = "unknown_user"
    dest = os.path.join(INCIDENTS_DIR, name)
    try:
        with open(dest, "w") as f:
            f.write(f"ip={ip}\nscore={score}\nusername={username}\nts={time.time()}\n")
    except OSError as e:
        print(f"[watcher] failed to write incident {dest}: {e}")


def react(ip, username, score):
    print(f"[watcher] threshold reached ip={ip} score={score} username={username!r}")
    write_incident(ip, username, score)
    ban_ip(ip)


def handle_invalid_user(username, ip):
    username_l = username.lower()

    with state_lock:
        if username == BAIT_USERNAME:
            ip_score[ip] += SCORE_BAIT

        if username_l in SCANNER_USERNAMES:
            ip_score[ip] += SCORE_SCANNER_USERNAME

        dq = ip_invalid_times[ip]
        dq.append(time.time())
        cutoff = time.time() - WINDOW_SECONDS
        while dq and dq[0] < cutoff:
            dq.popleft()
        if len(dq) > RATE_LIMIT:
            ip_score[ip] += SCORE_INVALID_RATE

        score = ip_score[ip]
        if score >= THRESHOLD:
            react(ip, username, score)


def handle_failed_pubkey(account, ip):
    with state_lock:
        dq = ip_fail_pubkey_times[ip]
        dq.append(time.time())
        cutoff = time.time() - WINDOW_SECONDS
        while dq and dq[0] < cutoff:
            dq.popleft()
        if len(dq) >= FAIL_PUBKEY_LIMIT:
            ip_score[ip] += SCORE_FAILED_PUBKEY

        score = ip_score[ip]
        if score >= THRESHOLD:
            react(ip, account, score)


def handle_line(line):
    m = INVALID_USER_RE.search(line)
    if m:
        handle_invalid_user(m.group(1), m.group(2))
        return

    m = FAILED_PUBKEY_RE.search(line)
    if m:
        handle_failed_pubkey(m.group(1), m.group(2))
        return


def tail_auth_log():
    while not os.path.exists(AUTH_LOG):
        time.sleep(0.5)
    with open(AUTH_LOG, "r") as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.3)
                continue
            line = line.strip()
            if not line:
                continue
            handle_line(line)


def unban_loop():
    while True:
        with state_lock:
            unban_expired()
        time.sleep(2)


def main():
    os.makedirs(INCIDENTS_DIR, exist_ok=True)
    threading.Thread(target=unban_loop, daemon=True).start()
    tail_auth_log()


if __name__ == "__main__":
    main()
