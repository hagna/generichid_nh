import gobject

import sys
import dbus
import dbus.service
import dbus.mainloop.glib
import time


import os

import pygame
import pygame.midi
from pygame.locals import *



class Demo(object):
    
    
    def __init__(self, hid, hidinput):
        self.hid = hid
        self.hidinput = hidinput

        self.hid.connect_to_signal("IncomingConnection",
                                    lambda : self.connectionMade("IncomingConnection"))
        self.hid.connect_to_signal("DeviceReleased",
                                    lambda : self.connectionLost("DeviceReleased"))
        self.hidinput.connect_to_signal("Reconnected", 
                                        lambda : self.connectionMade("Reconnected"))
        self.hidinput.connect_to_signal("Disconnected",
                                        lambda : self.connectionLost("Disconnected"))


    def sendKey(self, a, b, c):
        print( "sendKey %r %r %r" % (a, b, c))
        self.hidinput.SendEvent(dbus.Byte(a), dbus.UInt16(b), dbus.Byte(c))


    def connectionMade(self, reason):
        print( "connectionMade %r" % reason)
        #v = self.hidinput.GetProperties()
        #print "Properties are %r" % v


    def connectionLost(self, reason):
        print( "connectionLost %r" % reason)





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
        

class Keyer(object):
    """
    Use keyDown and keyUp as callbacks for triggering the decoder
    with the relevant chord of keys.


    @type  decoder: method
    @param decoder: called with the chord as a tuple like (0,1,2)

    """

    threshold = 1500
    decoder = lambda a, b: None


    def __init__(self, decoder, threshold=None):
        if decoder is not None:
            self.decoder = decoder
        self.maxtime = 0
        self.buffer = []
        self.keyDownbuffer = []
        if threshold is not None:
            self.threshold = threshold


    def keyUp(self, event, timestamp):
        if timestamp - self.maxtime > self.threshold:
            self.buffer = []
        self.maxtime = timestamp
        self.buffer.append(event)
        if event in self.keyDownbuffer:
            self.keyDownbuffer.remove(event)
        if self.all_keys_up():
            self.decoder(tuple(self.buffer))
            self.buffer = []


    def keyDown(self, event, timestamp):
        self.keyDownbuffer.append(event)


    def all_keys_up(self):
        return self.keyDownbuffer == []


class Statefull:
    def __init__(self):
        self.keyer = Keyer(self.strokeReceived)
        self.buf = []
        self.lastStrokeReceived = time.time()

    def _stroke2string(self, t):
        return str(t)

    _t = 0.550

    def tick(self):
        now = time.time()
        if (now - self.lastStrokeReceived) > self._t:
            if self.buf:
                print self.buf
                self.buf = []

    def strokeReceived(self, p):
        self.buf.append(self._stroke2string(p))
        self.lastStrokeReceived = time.time()
    # states return newstate, data and take data, e
    
    def _collectStroke(self, e):
        if e.type == pygame.midi.MIDIIN:
            note, status = e.data1, e.status
            if status == 144: #keydown
                self.keyer.keyDown(note, time.time())
            if status == 128:
                self.keyer.keyUp(note, time.time())
    
    def state_init(self, data, e):
        self._collectStroke(e)
        return 'init', data


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
    state = 'init'
    data = None
    statefull = Statefull()
    while going:
        events = event_get()
        statefull.tick()
        for e in events:
            m = getattr(statefull, 'state_' + state)
            state, data = m(data, e) 
            if e.type in [QUIT]:
                print (e)
            if e.type in [KEYDOWN]:
                if e.key in [K_ESCAPE]:
                    going = False
            #if e.type in [pygame.midi.MIDIIN]:
            #    print (e)

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
