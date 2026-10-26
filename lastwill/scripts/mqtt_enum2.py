#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import time, sys

HOST = "0.cloud.chals.io"
PORT = 16792

def on_connect(client, userdata, flags, rc, props=None):
    print(f"[+] CONNACK rc={rc}")
    for t in ["#", "$SYS/#", "plant/#", "+/+/will", "will/#", "lastwill/#", "gateway/#",
              "$SYS/broker/clients/connected", "$SYS/broker/clients/total",
              "$share/x/#"]:
        client.subscribe(t, qos=0)
    print("[+] subscribed")

def on_message(client, userdata, msg):
    p = msg.payload.decode('utf-8','replace')
    print(f"[MSG] {msg.topic} retain={msg.retain} :: {p}")

c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="enum2-"+str(int(time.time())))
c.on_connect = on_connect
c.on_message = on_message
c.connect(HOST, PORT, 30)
c.loop_start()
time.sleep(15)
c.loop_stop()
c.disconnect()
print("[+] done")
