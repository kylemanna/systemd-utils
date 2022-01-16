#!/usr/bin/env python
"""Python Lockscreen / Screensaver NumLock Manager for GNOME

Listen to DBus events for screensaver and lockscreen activation and toggle the numlock LED so that it's
always off when locked and is turned back on when the user deactivates the screen saver and unlocks the
system.
"""

import dbus
import pathlib

from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib


class GnomeLedMgr:

    def __init__(self, device):
        self.device_path = device
        self.last_screensaver_active = None
        self.timeout_timer = None

    def signal_cb(self, screensaver_active):

        if self.timeout_timer:
            GLib.source_remove(self.timeout_timer)
            self.timeout_timer = None

        # Convert from dbus.boolean()
        screensaver_active = bool(screensaver_active)

        # Duplicate signal (not sure why there are two senders of the same signal, the login
        # manager/screensaver + active user?)
        if self.last_screensaver_active == screensaver_active:
            return

        self.last_screensaver_active = screensaver_active

        # Shell hackery: /sys/class/leds/$(readlink /sys/class/input/$(readlink /dev/input/by-id/usb-Logitech_Logitech_G710_Keyboard-event-if01 | awk -F/ '{ print $2 }')/device | awk -F/ '{ print $3}'):white:keys/brightness"
        event = pathlib.Path(self.device_path).readlink().name
        input = pathlib.Path(f"/sys/class/input/{event}/device").readlink().name

        if screensaver_active:
            brightness = 0
        elif not screensaver_active:
            brightness = 1

        print(f"Screensaver status = {screensaver_active}, setting brightness {brightness}")

        for key_type in ('keys', 'wasd'):
            path = pathlib.Path(f"/sys/class/leds/{input}:white:{key_type}/brightness")
            with path.open('w') as f:
                f.write(f"{brightness}")

    def timeout_leds(self):
        """Called when the user fails to complete the login and turns LEDs back off after the screen is
        woken by the WakeUpScreen signal.
        """
        print(f"Wake Signal timeout")
        self.signal_cb(True)
        return False

    def wake_signal_cb(self):
        """Detect the screens turning on to enable keyboard LEDs"""
        print(f"Wake Signal received")
        self.timeout_timer = GLib.timeout_add_seconds(2, self.timeout_leds)
        self.signal_cb(False)

if __name__ == '__main__':


    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()

    mgr = GnomeLedMgr('/dev/input/by-id/usb-Logitech_Logitech_G710_Keyboard-event-if01')
    # Initial state is no screensaver
    mgr.signal_cb(False)

    bus.add_signal_receiver(mgr.signal_cb, 'ActiveChanged', 'org.gnome.ScreenSaver')

    # TODO: This doesn't fire when monitors turn on, but when the screensave is unlocked, kind of
    # useless.
    bus.add_signal_receiver(mgr.wake_signal_cb, 'WakeUpScreen', 'org.gnome.ScreenSaver')


    loop = GLib.MainLoop()
    loop.run()
