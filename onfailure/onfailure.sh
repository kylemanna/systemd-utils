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
# Set EMAIL environemental variable to override destination, see
# import-env.service for example of how to easily do this.
#
# Destiantion email priority: $2 -> $EMAIL -> $USER

svc=${1:-unknown}
#email=${2:-example@gmail.com}
email=${2:-${EMAIL:-$USER}}

cat <<EOF | sendmail -i "$email"
Subject: [$HOSTNAME] OnFailure Email for $svc

# Status

$(systemctl --user status -l -n 1000 "$svc")

EOF
