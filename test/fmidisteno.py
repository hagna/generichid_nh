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
import pickle


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
        

# do this clojure style
def send(agent, fn, *args):
    return fn(agent, *args)

def _get_stresses(v):
    o = v
    stress2 = -1
    stress1 = v.index(max(o))
    o.remove(max(o))
    if o:
        stress2 = v.index(max(o))
    if stress1 == stress2:
        stress2 = -1
    return stress1, stress2

def sendphon(agent):
    res = agent.copy()
    buf = [k[0] for k in res['buf']]
    vel = [k[1] for k in res['buf']]
    stress1, stress2 = _get_stresses(vel)
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
                                       'N': B(0x31),
                                       't': A(0x14),
                                       'r': A(0x13),
                                       's': A(0x1f),
                                       'S': B(0x1f),
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
                                       'EH': B(0x12, 0x23),
                                       'IY': B(0x17, 0x15),
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
                                       ('IH', 'r'): B(0x17, 0x2d) + A(0x13),
                                       ('y', 'UW'): A(0x15) + B(0x16, 0x11),
                                                  })
    #keymap = res.setdefault('keymap', KEYMAP)
    hidinput = res.get('hidinput')
    def sendkeys(a, b, c):
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
    for i, phon in enumerate(buf):
        keyb = phonmap.get(phon, [])
        if keyb:
            if i == stress1:
                s += A(0x2)
            if i == stress2:
                s += A(0x3)
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

def _lravg(v, ls, rs):
    # for finding the velocity of each hand
    lv = v[0:len(ls)]
    rv = v[len(ls):]
    l = 0
    r = 0
    if rs:
        r = sum(rv)/float(len(rs))
    if ls:
        l = sum(lv)/float(len(ls))
    return l, r

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
        (0,2,5):  ('IH', 'r'),
        (0,2,3,5): 'AW',
        (0,3,5):  ('y', 'UW'),
        (0,2,4,5): 'OY'}
    v = [k[2] for k in s]
    s = [k[1] for k in s]
    res = agent.copy()
    l = res.get('left')
    r = res.get('right')
    ls = [l.index(k) for k in s if k in l]
    rs = [r.index(k) for k in s if k in r]
    lv, rv = _lravg(v, ls, rs)
    ls.sort()
    rs.sort()
    ls = tuple(ls)
    rs = tuple(rs)
    left = d.get(ls, None)
    right = d.get(rs, None)
    if left:
        res['buf'].append((left, lv))
    if right:
        res['buf'].append((right, rv))
    res['lastStroke'] = time.time()
    return res



def keyUp(agent, event, timestamp):
    res = agent.copy()
    learn = res.setdefault('learn', False)
    if learn:
        if len(res['learnbuf']) == 12:
            res['left'] = res['learnbuf'][:6]
            res['left'].reverse()
            res['right'] = res['learnbuf'][6:]
            res['learnbuf'] = []
            res['learn'] = False
        return res
    sbuf = res.setdefault('sbuf', [])
    keydownbuffer = res.setdefault('keydownbuffer', [])
    threshold = 0.5
    newsbuf = []
    note, vel = [k for k in keydownbuffer if k[0] == event][0] # find the event
    keydownbuffer.remove((note,vel))
    for i in res['sbuf']:
        ts, e, v = i
        if timestamp - ts < threshold:
            newsbuf.append((ts, e, v))
    res['sbuf'] = newsbuf
    res['sbuf'].append((timestamp, event, vel))
    if keydownbuffer == []: # all keys are up
        res = send(res, decoder, tuple(res['sbuf']))
        res['sbuf'] = []
    res['keydownbuffer'] = keydownbuffer
    return res


def keyDown(agent, event, vel, timestamp):
    res = agent.copy()
    learn = res.setdefault('learn', False)
    if learn:
        lb = res.setdefault('learnbuf', [])
        lb.append(event)
        res['learnbuf'] = lb
        print lb
    else: 
        sbuf = res.setdefault('sbuf', [])
        keydownbuffer = res.setdefault('keydownbuffer', [])
        keydownbuffer.append((event, vel))
    return res

def keyb_event(agent, e):
    res = agent.copy()
    scancode, vel = e.scancode, 1
    l = res.setdefault('left', [56, 55, 27, 26, 25, 24])
    r = res.setdefault('right', [57, 58, 31, 32, 33, 34])
    learn = res.setdefault('learn', False)

    if scancode in l or scancode in r or learn:
        if e.type == KEYDOWN:
            res = send(res, keyDown, scancode, vel, time.time())
        if e.type == KEYUP:
            res = send(res, keyUp, scancode, time.time())
    return res

def midi_event(agent, e):
    res = agent.copy()
    l = res.setdefault('left', [59, 57, 56, 54, 51, 49])
    r = res.setdefault('right', [60, 62, 63, 66, 68, 70])
    note, status, vel = e.data1, e.status, e.data2
    learn = res.setdefault('learn', False)
    if note in l or note in r or learn:
        if status == 144 and vel != 0: #keydown
            res = send(res, keyDown, note, vel, time.time())
        if status == 128 or vel == 0: # hack for kawai
            res = send(res, keyUp, note, time.time())
    return res

def loadsteno(steno):
    res = steno.copy()
    try:
        fh = open('./stenostate.dat', 'r')
        res.update(pickle.load(fh))
        if not res:
            print "No file stenostate.dat"
        fh.close() 
    except Exception, e:
        print e
    return res



def writesteno(steno):
    try:
        fh = open('./stenostate.dat', 'w')
        steno.pop('hidinput')
        pickle.dump(steno, fh)
    except Exception, e:
        print "error writing steno object"
        print e
    show_steno(steno)


def show_steno(steno):
    s = steno.keys()
    s.sort()
    for i in steno.keys():
        print i
        print "\t%r" % steno[i]


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
    steno = loadsteno(steno) 
    while going:
        events = event_get()
        steno = send(steno, tick)
        for e in events:
            if e.type in [pygame.midi.MIDIIN]:
                steno = send(steno, midi_event, e)
            if e.type in [QUIT]:
                going = False
                break
            if e.type in [KEYDOWN]:
                if e.key in [K_ESCAPE]:
                    going = False
                    break
            if e.type == KEYUP:
                if e.key in [K_F1]:
                    steno['learn'] = True
                    print "learning 12 keys from left to right"
                    break
                if e.key in [K_F2]:
                    l = steno.pop('left')
                    r = steno.pop('right')
                    print "removing key mapping left was %r and right was %r" % ( l, r)
                    break
            if e.type in [KEYDOWN, KEYUP]:
                steno = send(steno, keyb_event, e)

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
    writesteno(steno)

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
