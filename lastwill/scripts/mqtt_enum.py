#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import sys, time

HOST = "0.cloud.chals.io"
PORT = 16792

def on_connect(client, userdata, flags, rc, props=None):
    print(f"[+] CONNACK rc={rc}")
    client.subscribe("#", qos=0)
    print("[+] subscribed to #")

def on_message(client, userdata, msg):
    try:
        p = msg.payload.decode('utf-8', 'replace')
    except Exception:
        p = msg.payload.hex()
    print(f"[MSG] topic={msg.topic!r} qos={msg.qos} retain={msg.retain} len={len(msg.payload)}")
    print(f"      payload={p}")

c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="enum-"+str(int(time.time())))
c.on_connect = on_connect
c.on_message = on_message
c.connect(HOST, PORT, 30)
c.loop_start()
time.sleep(12)
c.loop_stop()
c.disconnect()
print("[+] done")
