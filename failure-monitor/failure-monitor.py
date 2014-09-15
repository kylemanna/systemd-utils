#!/usr/bin/env python
#
# Author: Kyle Manna <kyle@kylemanna.com>
#
# Monitor systemd-journal for events that fail and email someone.
#

import os
import re
import pwd
import sys
import json
import stat
import smtplib
import socket
import subprocess
from email.mime.text import MIMEText


def getjournal():
    mode = os.fstat(0).st_mode

    if stat.S_ISFIFO(mode):
        sys.stderr.write("Reading from stdin\n")
        return sys.stdin

    else:
        args = ['journalctl', '-f', '-o', 'json']
        #args = ['journalctl', '--boot', '-1', '-o', 'json']
        sys.stderr.write("Forking %s\n" % str(args))

        p = subprocess.Popen(args, stdout = subprocess.PIPE)

        return iter(p.stdout.readline,'')


if len(sys.argv) > 1 and sys.argv[1]:
    email = sys.argv[1]
elif os.environ['EMAIL']:
    email = os.environ['EMAIL']
else:
    email = pwd.getpwuid(os.getuid())[0]

sys.stderr.write("Email = %s\n" % email)

for line in getjournal():

    if not line: break

    # Attempt to work with python2 and python3
    if isinstance(line, bytes): line = line.decode('utf-8')

    j = json.loads('[' + line + ']');

    if 'MESSAGE' in j[0] and 'entered failed state' in j[0]['MESSAGE']:
        #print j[0]['MESSAGE']

        # "Unit lvm2-pvscan@8:1.service entered failed state."
        m = re.search("^Unit (([\w:-]+)(\@([\w:-]+))?\.(\w+)) entered failed state\.$", j[0]['MESSAGE'])

        if not m:
            continue

        print("Event: %s" % str(m.groups()))

        full_name = m.groups()[0]
        #prefix_name = m.groups()[1]
        #instance_name = m.groups()[3]
        #systemd_type = m.groups()[4]

        try:
            body = subprocess.check_output(['systemctl', 'status', full_name])
        except Exception as e:
            body = "Exception: %s" % e
            sys.stderr.write(body + '\n')

        msg = MIMEText(body, _charset='utf-8')
        msg['From'] = email
        msg['To'] = email
        msg['Subject'] = "[%s] systemd: Unit '%s' entered failed state" % (socket.gethostname(), full_name)

        server = smtplib.SMTP('localhost')
        #server.set_debuglevel(1)
        server.sendmail(email, email, msg.as_string())
        server.quit()
