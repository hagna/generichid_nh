# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
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


# do this clojure style
def send(agent, fn, *args):
    return fn(agent, *args)


def sendphon(agent):
    res = agent.copy()
    buf = res['buf']
    # keyboard macro language is the tuple of arguments to SendEvent
    # but for the simple case it's just one argument
    # for the slightly more complex case it is two
    # but three is fine too
    #
    def A(*a):
        res = []
        for i in a:
            res += [(i, 1)]
            res += [(i, 0)]
        return res

    def B(*a):
        res = []
        res += [(0x36, 1)]
        res += A(*a)
        res += [(0x36, 0)]
        return res


    phonmap = res.setdefault('phonmap', {'D': B(0x20),  
                                       'n': A(0x31),
                                       't': A(0x14),
                                       'r': A(0x13),
                                       's': A(0x1f),
                                       'd': A(0x20),
                                       'l': A(0x26),
                                       'z': A(0x2c),
                                       'm': A(0x32),
                                       'k': A(0x25),
                                       'v': A(0x2f),
                                       'w': A(0x11),
                                       'p': A(0x19),
                                       'f': A(0x21),
                                       'b': A(0x30),
                                       'h': A(0x23),
                                       'g': A(0x22),
                                       'y': A(0x15),
                                       'J': B(0x24),
                                       'T': B(0x14),
                                       'C': B(0x2e),
                                       'Z': B(0x2c),
                                       'AX': B(0x1e, 0x2d),
                                       'IX': B(0x17, 0x2d),
                                       'AO': B(0x1e, 0x18),
                                       'IH': B(0x17, 0x23),
                                       'AE': B(0x1e, 0x12),
                                       'OW': B(0x18, 0x11),
                                       'EY': B(0x12, 0x15),
                                       'UX': B(0x16, 0x2d),
                                       'UW': B(0x16, 0x11),
                                       'AY': B(0x1e, 0x15),
                                       'UH': B(0x16, 0x23),
                                       'AW': B(0x1e, 0x11),
                                       'OY': B(0x18, 0x15),
                                                  })
    #keymap = res.setdefault('keymap', KEYMAP)
    hidinput = res.get('hidinput')
    def sendkeys(a, b, c):
        print "sendkeys", a, b, c
        try:
            hidinput.SendEvent(dbus.Byte(a), dbus.UInt16(b), dbus.Byte(c))
        except Exception, e:
            print e

    _type = 1
    def send_s(s):
        for i in s:
            _code, _value = i
            sendkeys(_type, _code, _value)

    s = []
    pre = A(0x1a, 0x1a, 0x17, 0x31, 0x19, 0x14, 0x39)
    pre += B(0x19, 0x23, 0x18, 0x31)
    pre += A(0x1b, 0x1b)
    post = A(0x1c)

    for phon in buf:
        keyb = phonmap.get(phon, [])
        if keyb:
            s += keyb 
    s = pre + s + post
    for i in s:
        _code, _value = i 
        sendkeys(_type, _code, _value)
    res['buf'] = []
    return res


def tick(agent, *args):
    _t = 0.55
    res = agent.copy()
    lastStroke = res.setdefault('lastStroke', None)
    buf = res.setdefault('buf', [])
    if lastStroke:
        now = time.time()
        if (now - lastStroke) > _t:
            if buf:
                res = send(res, sendphon)
    return res


def decoder(agent, s):
    d = {(4,): 'n', # consonants
        (3,): 't',
        (1,): 'r',
        (2,): 's',
        (5,): 'd',
        (1,4): 'l',
        (2,3): 'D',
        (3,4): 'z',
        (1,2): 'm',
        (2,3,4): 'k',
        (1,3): 'v',
        (1,2,3,4): 'w',
        (1,2,3): 'p',
        (1,5): 'f',
        (4,5): 'b',
        (2,4): 'h',
        (2,3,4,5): 'N',
        (1,3,4): 'S',
        (3,4,5): 'g',
        (1,2,3,4,5): 'y',
        (2,5): 'C',
        (1,4,5): 'J',
        (1,2,4): 'T',
        (1,3,4,5): 'Z',
        (0,): 'AX', # vowels
        (0,4): 'IX',
        (0,2): 'AO',
        (0,1): 'IH',
        (0,3): 'AE',
        (0,2,3,4): 'EH',
        (0,2,3): 'IY',
        (0,2,4): 'OW',
        (0,5): 'EY',
        (0,3,4): 'UX',
        (0,2,3,4,5): 'UW',
        (0,4,5): 'AY',
        (0,3,4,5): 'UH',
        (0,2,5): None,
        (0,2,3,5): 'AW',
        (0,3,5): None,
        (0,2,4,5): 'OY'}
    res = agent.copy()
    r = res.setdefault('left', [59, 57, 56, 54, 51, 49])
    l = res.setdefault('right', [60, 62, 63, 66, 68, 70])
    ls = [l.index(k) for k in s if k in l]
    rs = [r.index(k) for k in s if k in r]
    ls.sort()
    rs.sort()
    ls = tuple(ls)
    rs = tuple(rs)
    print "right", rs
    print "left", ls
    for k in [d.get(rs, None), d.get(ls, None)]:
        if k:
            res['buf'].append(k)
    res['lastStroke'] = time.time()
    return res



def keyUp(agent, event, timestamp):
    res = agent.copy()
    sbuf = res.setdefault('sbuf', [])
    keydownbuffer = res.setdefault('keydownbuffer', [])
    threshold = 0.5
    newsbuf = []
    for i in res['sbuf']:
        ts, e = i
        if timestamp - ts < threshold:
            newsbuf.append((ts, e))
    res['sbuf'] = newsbuf
    res['sbuf'].append((timestamp, event))
    if event in keydownbuffer:
        keydownbuffer.remove(event)
    if keydownbuffer == []: # all keys are up
        res = send(res, decoder, tuple([e[1] for e in res['sbuf']]))
        res['sbuf'] = []
    return res


def keyDown(agent, event, timestamp):
    res = agent.copy()
    sbuf = res.setdefault('sbuf', [])
    keydownbuffer = res.setdefault('keydownbuffer', [])
    keydownbuffer.append(event)
    return res


def midi_event(agent, e):
    res = agent.copy()
    note, status = e.data1, e.status
    if status == 144: #keydown
        res = send(res, keyDown, note, time.time())
    if status == 128:
        res = send(res, keyUp, note, time.time())
    return res


def input_main(device_id = None):
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SystemBus()
    
    manager = dbus.Interface(bus.get_object("org.bluez", "/"),
                            "org.bluez.Manager")
    
    # export BTADAPTER=`dbus-send --system --dest=org.bluez --print-reply / org.bluez.Manager.DefaultAdapter | tail -1 | sed 's/^.*"\(.*\)".*$/\1/'`
    path = manager.DefaultAdapter()

    # dbus-send --system --dest=org.bluez --print-reply $BTADAPTER org.freedesktop.DBus.Introspectable.Introspect

    adapter = dbus.Interface(bus.get_object("org.bluez", path), "org.bluez.GenericHID")

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

    steno = {'state':0,
             'ts': time.time(),
             'hidinput': in_device}
    while going:
        events = event_get()
        steno = send(steno, tick)
        for e in events:
            if e.type in [pygame.midi.MIDIIN]:
                steno = send(steno, midi_event, e)
            if e.type in [QUIT]:
                print (e)
            if e.type in [KEYDOWN]:
                print "['%s', 0x%x]" % (e.unicode, e.scancode)
                if e.key in [K_ESCAPE]:
                    going = False
            if e.type in [KEYUP]:
                pass

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
