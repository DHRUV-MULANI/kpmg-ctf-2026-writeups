import socket, struct
HOST="0.cloud.chals.io"; PORT=16792
def enc_len(n):
    out=b""
    while True:
        d=n%128; n//=128
        if n>0: out+=bytes([d|0x80])
        else: out+=bytes([d]); break
    return out
def pkt(t, body): return bytes([t])+enc_len(len(body))+body
def mqtt_string(s): return struct.pack(">H",len(s))+s.encode()

for ver in [4,3,5]:
    s=socket.socket(); s.settimeout(6); s.connect((HOST,PORT))
    payload=mqtt_string("MQTT") if ver==4 else mqtt_string("MQIsdp")
    if ver==5:
        payload=mqtt_string("MQTT")+bytes([5,2,0,60,0])
    body=payload+bytes([ver,0x02])+struct.pack(">H",60)+mqtt_string("probe-"+str(ver))
    s.send(pkt(0x10, body))
    print("ver",ver,"resp",s.recv(64).hex())
    s.close()
