#!/bin/bash
#
# Author: Kyle Manna <kyle@kylemanna.com>
#
# Simple systemd script used to be called via something like:
#
# Example Unit section of a service file:
#
# [Unit]
# ...
# Onfailure=failure-email@%i.service
#
#
# failure-email@.service:
#
# [Unit]
# Description=OnFailure for %i
#
# [Service]
# Type=oneshot
# ExecStart=/path/to/onfailure.sh %i
#
#
# Current magic to forward to real email is to setup email /etc/postfix/alias
# for $USER@$HOSTNAME and that way no copies are needed.

svc=${1-unknown}
#email=${2-example@gmail.com}
email=${2-$USER}

cat <<EOF | sendmail -i "$email"
Subject: [$HOSTNAME] OnFailure Email for $svc

# Status

$(systemctl --user status -l -n 1000 "$svc")

EOF
