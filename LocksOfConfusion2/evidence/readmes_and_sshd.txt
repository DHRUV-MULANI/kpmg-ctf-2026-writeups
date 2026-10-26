diagnostics sandbox -- restricted shell

=== jail README in home ===
cat: can't open 'README': No such file or directory

=== sshd_config ===
Port 22
Protocol 2

HostKey /etc/ssh/ssh_host_rsa_key
HostKey /etc/ssh/ssh_host_ed25519_key

PermitRootLogin no
PubkeyAuthentication yes
PasswordAuthentication no
KbdInteractiveAuthentication no
ChallengeResponseAuthentication no
UsePAM no

AllowUsers svc-legacydb

X11Forwarding no
AllowTcpForwarding no
AllowAgentForwarding no
PermitTunnel no

LogLevel INFO

Subsystem sftp internal-sftp
