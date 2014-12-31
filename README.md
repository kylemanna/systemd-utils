# systemd-utils

Random systemd utilities and unit files.

## Usage

Recommended location:

    cd $HOME/.config/systemd
    git clone https://github.com/kylemanna/systemd-utils.git

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
