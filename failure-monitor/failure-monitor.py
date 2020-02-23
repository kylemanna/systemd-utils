#!/usr/bin/env python
#
# Author: Kyle Manna <kyle[at]kylemanna[dot]com>
#
# Monitor systemd-journal for events that fail and email someone.
#

import argparse
import json
import logging
import os
import pwd
import select
import smtplib
import sys
import systemd.journal
import email

from email.mime.text import MIMEText

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
        hostname = entry.get('_HOSTNAME')
        invoke_id = entry.get('INVOCATION_ID')

        logger.warning(f'Unit "{unit}" failed with invocation id "{invoke_id}"')

        filter_list = [
                'CODE_FUNC',
                'INVOCATION_ID'
                'MESSAGE',
                'PRIORITY',
                'UNIT',
                'UNIT_RESULT',
                '_BOOT_ID',
                '_HOSTNAME',
                '__REALTIME_TIMESTAMP'
                ]
        entry2 = { k: str(v) for k, v in entry.items() if k in filter_list}

        body  = ['']
        body += ['Failure Info:']
        body += ['    ' + x for x in json.dumps(entry2, sort_keys=True, indent=4).split('\n')]
        body += ['']
        body += ['Logs:']
        body += ['    ' + x for x in self.fetch_logs_for_invocation_id(invoke_id)]

        body = '\n'.join(body)

        msg = MIMEText(body)
        msg['From'] = args.email
        msg['To'] = args.email
        msg['Subject'] = f"[{hostname}] systemd: Unit '{unit}' failed"

        server = smtplib.SMTP('localhost')
        #server.set_debuglevel(1)
        server.sendmail(args.email, args.email, msg.as_string())
        server.quit()

    @staticmethod
    def format_logs(entry):
        msg = entry.get('MESSAGE')
        time = entry.get('__REALTIME_TIMESTAMP')
        unit = entry.get('_SYSTEMD_UNIT')
        pid = entry.get('_PID')
        return f'{time:%Y-%m-%d %H:%M:%m}  {unit}[{pid}]  {msg}'

    def fetch_logs_for_invocation_id(self, invoke_id):
        reader = systemd.journal.Reader()
        reader.this_boot()
        reader.add_match(_SYSTEMD_INVOCATION_ID=invoke_id)

        logs = [self.format_logs(entry) for entry in reader]

        reader.close()

        return logs


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
