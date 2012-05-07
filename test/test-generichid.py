#!/usr/bin/python

import gobject

import sys
import dbus
import dbus.service
import dbus.mainloop.glib
import time


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


    def sendKey(self, k):
        print "sendKey %r" % k
        self.hidinput.SendEvent(dbus.Byte(1), dbus.Int16(k), dbus.Byte(1))
        time.sleep(3)
        self.hidinput.SendEvent(dbus.Byte(1), dbus.Int16(k), dbus.Byte(0))


    def connectionMade(self, reason):
        print "connectionMade %r" % reason
        #v = self.hidinput.GetProperties()
        #print "Properties are %r" % v
        for i in xrange(55, 100):
            self.sendKey(i << 8)


    def connectionLost(self, reason):
        print "connectionLost %r" % reason



def main(argv):
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SystemBus()
    
    manager = dbus.Interface(bus.get_object("org.bluez", "/"),
                            "org.bluez.Manager")
    
    # export BTADAPTER=`dbus-send --system --dest=org.bluez --print-reply / org.bluez.Manager.DefaultAdapter | tail -1 | sed 's/^.*"\(.*\)".*$/\1/'`
    path = manager.DefaultAdapter()

    # dbus-send --system --dest=org.bluez --print-reply $BTADAPTER org.freedesktop.DBus.Introspectable.Introspect

    adapter = dbus.Interface(bus.get_object("org.bluez", path), "org.bluez.GenericHID")

    adapter.Activate()
    print "Acitvated keyboard device class"

    in_device = dbus.Interface(bus.get_object("org.bluez",
                                              "/org/bluez/input/hci0/device1"),
                              "org.bluez.GenericHIDInput")

    d = Demo(adapter, in_device)
    if len( argv ) > 1:
        d.connectionMade(argv[1])

    mainloop = gobject.MainLoop()

    try:
        mainloop.run()
    finally:
        adapter.Deactivate()
        print "Deactivated keyboard device class"


if __name__ == '__main__':
    main(sys.argv)
