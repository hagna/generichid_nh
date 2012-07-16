#!/usr/bin/python

import gobject

import sys
import dbus
import dbus.service
import dbus.mainloop.glib



def main(argv):
	dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

	bus = dbus.SystemBus()
	
	manager = dbus.Interface(bus.get_object("org.bluez", "/"),
							"org.bluez.Manager")
	

	# export BTADAPTER=`dbus-send --system --dest=org.bluez --print-reply / org.bluez.Manager.DefaultAdapter | tail -1 | sed 's/^.*"\(.*\)".*$/\1/'`
	path = manager.DefaultAdapter()

	# dbus-send --system --dest=org.bluez --print-reply $BTADAPTER org.freedesktop.DBus.Introspectable.Introspect

	adapter = dbus.Interface(bus.get_object("org.bluez", path),
							"org.bluez.GenericHID")
	def incoming_connection(*args, **kw):
		print "incoming connection %r %r" % (args, kw)


	def device_released(*args, **kw):
		print "device released %r %r" % (args, kw)

	def reconnected(*args, **kw):
		print "reconnected %r %r" % (args, kw)

	def disconnected(*args, **kw):
		print "disconnected %r %r" % (args, kw)

	in_device = dbus.Interface(bus.get_object("org.bluez",
		"/org/bluez/input/hci0/device1"),
		"org.bluez.GenericHIDInput")


	in_device.connect_to_signal("Reconnected", reconnected)
	in_device.connect_to_signal("Disconnected", disconnected)




	adapter.connect_to_signal("IncomingConnection",
			incoming_connection)
	adapter.connect_to_signal("DeviceReleased", device_released)


	in_device.SendEvent(dbus.Byte(1),
					dbus.UInt16(i), dbus.Byte(j))

	mainloop = gobject.MainLoop()

	mainloop.run()


if __name__ == '__main__':
	main(sys.argv)
