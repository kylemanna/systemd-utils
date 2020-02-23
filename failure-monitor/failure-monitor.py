#!/usr/bin/env python
#
# Author: Kyle Manna <kyle[at]kylemanna[dot]com>
#
# Monitor systemd-journal for events that fail and email someone.
#

import argparse
import json
import os
import pwd
import re
import smtplib
import socket
import stat
import subprocess
import sys
from email.mime.text import MIMEText

import logging

logging.basicConfig(level=logging.INFO)
log_name = os.path.basename(__file__) if __name__ == '__main__' else __name__
logger = logging.getLogger(log_name)

def getjournal():
    mode = os.fstat(0).st_mode

    if stat.S_ISFIFO(mode):
        logger.info('Reading from stdin')
        return sys.stdin

    else:
        args = ['journalctl', '-f', '-o', 'json']
        #args = ['journalctl', '--boot', '-1', '-o', 'json']
        logger.info(f'Forking {args}')

        p = subprocess.Popen(args, stdout = subprocess.PIPE)

        return iter(p.stdout.readline,'')

if __name__ == '__main__':

    email = os.environ.get('EMAIL', pwd.getpwuid(os.getuid()).pw_name)

    parser = argparse.ArgumentParser()
    parser.add_argument('email',
                        nargs='?',
                        help='destination email address for notifications',
                        default=email)
    args = parser.parse_args()

    logger.info(f'Email = {args.email}')

    for line in getjournal():

        if not line: break

        # Attempt to work with python2 and python3
        if isinstance(line, bytes): line = line.decode('utf-8')

        j = json.loads('[' + line + ']');

        if 'MESSAGE' in j[0] and 'Failed with result' in j[0]['MESSAGE']:
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

            systemctl_args = ['systemctl', 'status', full_name]

            # If the command was run in this systemd user session, call status
            # in this manner as well
            if '--user' in j[0]['_CMDLINE'] and str(os.getuid()) == j[0]['_UID']:
                systemctl_args.append('--user')

            try:
                body = subprocess.check_output(systemctl_args)
            except subprocess.CalledProcessError as e:
                # No clue why systemctl status returns 3 when the status msg
                # returns fine, tip toe around this.
                if e.returncode != 3:
                    logger.error(f'CalledProcessError: {e}')
                else:
                    body = e.output

            msg = MIMEText(body, _charset='utf-8')
            msg['From'] = args.email
            msg['To'] = args.email
            msg['Subject'] = "[%s] systemd: Unit '%s' entered failed state" % (socket.gethostname(), full_name)

            server = smtplib.SMTP('localhost')
            #server.set_debuglevel(1)
            server.sendmail(args.email, args.email, msg.as_string())
            server.quit()
