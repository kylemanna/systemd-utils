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
import select
import smtplib
import socket
import subprocess
import sys
from email.mime.text import MIMEText
import systemd.journal

import logging

logging.basicConfig(level=logging.INFO)
log_name = os.path.basename(__file__) if __name__ == '__main__' else __name__
logger = logging.getLogger(log_name)

#
# Class to monitor a systemd journal for exiting services and email them
#
class FailureMonitor(object):
    def __init__(self, email):
        self.email = email

    def run(self):
        reader = systemd.journal.Reader()
        reader.this_boot()
        reader.seek_tail()
        reader.get_previous()
        reader.log_level(systemd.journal.LOG_WARNING)

        p = select.poll()
        p.register(reader.fileno(), reader.get_events())

        while True:
            p.poll()

            if reader.process() == systemd.journal.APPEND:
                self.handle_journal_entries(reader)

        return True

    def handle_journal_entries(self, reader):
        for entry in reader:
            self.handle_journal_entry(entry)

    @staticmethod
    def failure_detected_msg(msg: str):
        # Currently unused, but common systemd failure strings
        search = ['entered failed state', 'Failed with result']
        return any([s in msg for s in search])

    @staticmethod
    def failure_detected(entry):
        # This seems to be the simplest check
        return (entry.get('CODE_FUNC', '') == 'unit_log_failure')

    def handle_journal_entry(self, entry):

        if not self.failure_detected(entry):
            return

        unit = entry.get('UNIT')
        systemctl_args = ['systemctl', 'status', unit]

        # If the command was run in this systemd user session, call status
        # in this manner as well
        if '--user' in entry['_CMDLINE'] and str(os.getuid()) == entry['_UID']:
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
        msg['Subject'] = "[%s] systemd: Unit '%s' entered failed state" % (socket.gethostname(), unit)

        server = smtplib.SMTP('localhost')
        #server.set_debuglevel(1)
        server.sendmail(args.email, args.email, msg.as_string())
        server.quit()

if __name__ == '__main__':

    email = os.environ.get('EMAIL', pwd.getpwuid(os.getuid()).pw_name)

    parser = argparse.ArgumentParser()
    parser.add_argument('email',
                        nargs='?',
                        help='destination email address for notifications',
                        default=email)
    args = parser.parse_args()

    logger.info(f'Email = {args.email}')

    monitor = FailureMonitor(args.email)
    success = monitor.run()

    sys.exit(0 if success else 1)
