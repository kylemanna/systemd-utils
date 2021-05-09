#!/usr/bin/env python
"""Python Lockscreen / Screensaver NumLock Manager for GNOME

Listen to DBus events for screensaver and lockscreen activation and toggle the numlock LED so that it's
always off when locked and is turned back on when the user deactivates the screen saver and unlocks the
system.
"""

import dbus
import evdev

from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib


class GnomeNumlockMgr:
    ui = None
    e = evdev.ecodes

    def __init__(self, device):
        self.device_path = device
        #self.dev = evdev.InputDevice(device)
        # Open on demand to avoid this strange issue on first boot:
        # Traceback (most recent call last):
        #  File "/usr/lib/python3.8/site-packages/dbus/connection.py", line 232, in maybe_handle_message
        #    self._handler(*args, **kwargs)
        #  File "/home/nitro/.config/systemd/utils/scripts/gnome-numlock-mgr.py", line 59, in signal_cb
        #    if screensaver_active and self.get_numlock():
        #  File "/home/nitro/.config/systemd/utils/scripts/gnome-numlock-mgr.py", line 50, in get_numlock
        #    return self.e.LED_NUML in self.dev.leds()
        #  File "/usr/lib/python3.8/site-packages/evdev/device.py", line 262, in leds
        #    leds = _input.ioctl_EVIOCG_bits(self.fd, ecodes.EV_LED)
        #SystemError: <built-in function ioctl_EVIOCG_bits> returned NULL without setting an error
        self.dev = None
        self.cleared_numlock = False


    def ui_thing(self):
        pass
        # Toggling numlock while the screensaver activates due to timeout will cause it to reset and
        # instantly wake and never sleep!  Don't do this.
        #if not self.ui:
        #    self.ui = evdev.UInput(name='GNOME NumLock Manager')
        #    print(f"Created {self.ui}")
        #
        #self.ui.write(e.EV_KEY, e.KEY_NUMLOCK, 1)
        #self.ui.write(e.EV_KEY, e.KEY_NUMLOCK, 0)
        #self.ui.syn()

    def init_dev(self):
        if not self.dev:
            self.dev = evdev.InputDevice(self.device_path)
            print(f"Opened {self.dev}")

        # HACK Test until I can figure out why this needs to happen
        try:
            leds = self.dev.leds()
        except Exception as e:
            print(f"Failed to get LEDs, re-opening...")
            self.dev = evdev.InputDevice(self.device_path)


    def set_numlock(self, val = 1):
        # Hack, why?
        self.init_dev()
        # Seems that toggling numlock on the lock screen fails to turn off the LED, perhaps because the
        # terminal has changed and the user input fails?  Will the LED and internal numlock state ever get
        # out of sync?
        # FIXME get rid of the following when it's better understood.
        self.dev.set_led(self.e.LED_NUML, val)
        self.cleared_numlock = not bool(val)


    def get_numlock(self):
        # Hack, why?
        self.init_dev()
        return self.e.LED_NUML in self.dev.leds()

    def signal_cb(self, screensaver_active):
        # Convert from dbus.boolean()
        screensaver_active = bool(screensaver_active)
        numlock = None

        if screensaver_active and self.get_numlock():
            numlock = 0
        elif not screensaver_active and self.cleared_numlock:
            numlock = 1

        print(f"Screensaver status = {screensaver_active}, setting NumLock {numlock}")

        if numlock != None:
            self.set_numlock(numlock)

if __name__ == '__main__':

    mgr = GnomeNumlockMgr('/dev/input/by-id/usb-Logitech_Logitech_G710_Keyboard-event-kbd')

    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    bus.add_signal_receiver(mgr.signal_cb, 'ActiveChanged', 'org.gnome.ScreenSaver')

    loop = GLib.MainLoop()
    loop.run()
