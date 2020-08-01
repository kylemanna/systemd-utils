#!/usr/bin/env python
"""Python Lockscreen / Screensaver Numlock Manager for GNOME

Listen to DBus events for screensaver and lockscreen activation and toggle the numlock LED so that it's
always off when locked and is turned back on when the user deactivates the screen saver and unlocks the
system.
"""

import dbus
import evdev

from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

def toggle_numlock(dev):
    e = evdev.ecodes

    # Seems that toggling numlock on the lock screen fails to turn off the LED, perhaps because the
    # terminal has changed and the user input fails?  Will the LED and internal numlock state ever get
    # out of sync?
    # FIXME get rid of the following when it's better understood.
    dev.set_led(e.LED_NUML, 0)

    ui.write(e.EV_KEY, e.KEY_NUMLOCK, 1)
    ui.write(e.EV_KEY, e.KEY_NUMLOCK, 0)
    ui.syn()

def get_numlock(dev):
    return evdev.ecodes.LED_NUML in dev.leds()

def signal_cb(screensaver_active):
    # Convert from dbus.boolean()
    screensaver_active = bool(screensaver_active)
    print(f"Screensaver status = {screensaver_active}")

    if screensaver_active == get_numlock(dev):
        print('Toggling NUMLOCK')
        toggle_numlock(dev)

if __name__ == '__main__':

    dev = evdev.InputDevice('/dev/input/by-id/usb-Logitech_Logitech_G710_Keyboard-event-kbd')
    print(f"Opened {dev}")
    ui = evdev.UInput(name='GNOME Numlock Manager')
    print(f"Created {ui}")

    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    bus.add_signal_receiver(signal_cb, 'ActiveChanged', 'org.gnome.ScreenSaver')

    loop = GLib.MainLoop()
    loop.run()
