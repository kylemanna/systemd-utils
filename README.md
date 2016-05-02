# systemd-utils

Random systemd utilities and unit files.

## Usage

Recommended location:

    cd $HOME/.config/systemd
    git clone https://github.com/kylemanna/systemd-utils.git utils

Symlink or hardlink unit files into `$HOME/.config/systemd/user`.  Systemd appears to have some issues with symlinked unit files at the time of writing.

## Scripts

### On Failure

* Allows users to specify `OnFailure=failure-email@%i.service` under `[Unit]` section of systemd files.
* The `failure-email` service will email the user when a service fails unexpectedly and include the `systemd status <svc>` output.
* Example configuration systemd file:

        [Unit]
        ...
        OnFailure=failure-email@%i.service


### Failure Monitor

* Systemd service that runs and parses the output of journalctl.  When a task fails, an email is sent to the user at the configured email address.
* The `failure-monitor` service will email the user when a service fails unexpectedly and include the `systemd status <svc>` output.
* Example configuration:

        $ systemctl --user start failure-monitor@test@gmail.com.service

### Email Journal Log

Upon completion of a script (i.e. a daily backup script), send an email of the log output.  The following code should be used to save a cursor before the execution of the service and send all the data followign that cursor.

    ExecStartPre=/bin/sh -c 'journalctl -o cat -n 0 -u %n --show-cursor | cut -f3 -d" " > /run/%n.cursor'

    ExecStart=...

    ExecStopPost=/bin/sh -c '/etc/systemd/scripts/systemd-email you@example.com %n $(cat /run/%n.cursor)'
    ExecStopPost=/bin/rm -f /run/%n.cursor

It would be nice if systemd provided a reference to a cursor prior to the most recent invocation of the service (like the --boot option refers to this boot).  Until then hack around it.
