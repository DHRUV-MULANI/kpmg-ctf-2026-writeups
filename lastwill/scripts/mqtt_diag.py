#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import time, threading

HOST = "0.cloud.chals.io"; PORT = 16792

topics = [
    "$internal/#", "$internal", "$diag/#", "$diag", "$diagnostics/#", "$diagnostics",
    "$sys/#", "$SYS/#", "$broker/#", "$audit/#", "$gateway/#", "$plant/#",
    "$status/#", "$status", "$private/#", "$secret/#", "$will/#", "$lastwill/#",
    "$flag/#", "$greenleaf/#", "$green/#", "$monitor/#", "$metrics/#",
    "$alert/#", "$alerts/#", "$device/#", "$devices/#", "$heartbeat/#",
    "plant/gateway/heartbeat_lost", "plant/gateway/#", "plant/#",
]
seen = set()
def on_connect(c, u, f, rc, props=None):
    print("[+] connected rc", rc)
    for t in topics:
        c.subscribe(t, 0)
    print("[+] subscribed", len(topics))
def on_message(c, u, msg):
    p = msg.payload.decode('utf-8', 'replace')
    print(f"[+] MSG {msg.topic} retain={msg.retain}: {p}", flush=True)
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="diag-"+str(int(time.time())))
client.on_connect = on_connect
client.on_message = on_message
client.connect(HOST, PORT, 30)
client.loop_start()
time.sleep(18)
client.loop_stop()
client.disconnect()
print("done")