from generichid_keyb import *

import sys
import os

import pygame
import pygame.midi
from pygame.locals import *



def print_device_info():
    pygame.midi.init()
    _print_device_info()
    pygame.midi.quit()


def _print_device_info():
    for i in range( pygame.midi.get_count() ):
        r = pygame.midi.get_device_info(i)
        (interf, name, input, output, opened) = r

        in_out = ""
        if input:
            in_out = "(input)"
        if output:
            in_out = "(output)"

        print ("%2i: interface :%s:, name :%s:, opened :%s:  %s" %
               (i, interf, name, opened, in_out))
        

def input_main(device_id = None):
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SystemBus()
    
    manager = dbus.Interface(bus.get_object("org.bluez", "/"),
                            "org.bluez.Manager")
    
    # export BTADAPTER=`dbus-send --system --dest=org.bluez --print-reply / org.bluez.Manager.DefaultAdapter | tail -1 | sed 's/^.*"\(.*\)".*$/\1/'`
    path = manager.DefaultAdapter()

    # dbus-send --system --dest=org.bluez --print-reply $BTADAPTER org.freedesktop.DBus.Introspectable.Introspect

    adapter = dbus.Interface(bus.get_object("org.bluez", path), "org.bluez.GenericHID")

    adapter.Activate()
    print( "Acitvated keyboard device class")

    in_device = dbus.Interface(bus.get_object("org.bluez","/org/bluez/input/hci0/device1"),"org.bluez.GenericHIDInput")


    d = Demo(adapter, in_device)
    devices = get_devices()
    for i, dev in enumerate(devices):
        print("%d %s" % (i, dev))

    print("\n")
    i = raw_input("which device do you want to try? [0]")
    if not i:
        i = 0
    i = int(i)
    key_e = devices[i]

    #midi stuff
    pygame.init()
    pygame.fastevent.init()
    event_get = pygame.fastevent.get
    event_post = pygame.fastevent.post

    pygame.midi.init()

    _print_device_info()


    if device_id is None:
        input_id = pygame.midi.get_default_input_id()
    else:
        input_id = device_id

    print ("using input_id :%s:" % input_id)
    mi = pygame.midi.Input( input_id )

    pygame.display.set_mode((1,1))


    going = True
    while going:
        events = event_get()
        for e in events:
            if e.type in [KEYDOWN]:
                print (e)
            if e.type in [QUIT]:
                going = False
            if e.type in [pygame.midi.MIDIIN]:
                print (e)

        if mi.poll():
            midi_events = mi.read(10)
            # convert them into pygame events.
            midi_evs = pygame.midi.midis2events(midi_events, mi.device_id)

            for m_e in midi_evs:
                event_post( m_e )
        #ev = key_e.read()
        #print ev
        #for i in key_e.readall():
        # 1 scancode 1 for keydown 0 for keyup
        #    print("%d %d %d" % (i.evtype, i.code, i.value))
        #    d.sendKey(i.evtype, i.code, i.value)


    adapter.Deactivate()
    print( "Deactivated keyboard device class")
    del mi
    pygame.midi.quit()


def usage():
    print ("--input [device_id] : Midi message logger")
    print ("--list : list available midi devices")


def main(argv):
    try:
        device_id = int( sys.argv[-1] )
    except:
        device_id = None

    if "--input" in sys.argv or "-i" in sys.argv:
        input_main(device_id)
    elif "--list" in sys.argv or "-l" in sys.argv:
        print_device_info()
    else:
        usage()

if __name__ == '__main__':
    main(sys.argv)
