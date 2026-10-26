import paramiko, sys
HOST="0.cloud.chals.io"; PORT=25140; USER="vboxuser"; PW="changeme"
cmd=sys.argv[1] if len(sys.argv)>1 else "id"
c=paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PW, timeout=15, allow_agent=False, look_for_keys=False)
stdin,stdout,stderr=c.exec_command(cmd)
out=stdout.read().decode(errors="replace"); err=stderr.read().decode(errors="replace")
print(out, end="")
if err.strip(): print("STDERR:", err, end="")
c.close()
