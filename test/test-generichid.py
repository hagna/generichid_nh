#!/usr/bin/python

import gobject

import sys
import dbus
import dbus.service
import dbus.mainloop.glib
from optparse import OptionParser

class Rejected(dbus.DBusException):
	_dbus_error_name = "org.bluez.Error.Rejected"

class Agent(dbus.service.Object):
	exit_on_release = True

	def set_exit_on_release(self, exit_on_release):
		self.exit_on_release = exit_on_release

	@dbus.service.method("org.bluez.Agent",
					in_signature="", out_signature="")
	def Release(self):
		print "Release"
		if self.exit_on_release:
			mainloop.quit()

	@dbus.service.method("org.bluez.Agent",
					in_signature="os", out_signature="")
	def Authorize(self, device, uuid):
		print "Authorize (%s, %s)" % (device, uuid)
		authorize = raw_input("Authorize connection (yes/no): ")
		if (authorize == "yes"):
			return
		raise Rejected("Connection rejected by user")

	@dbus.service.method("org.bluez.Agent",
					in_signature="o", out_signature="s")
	def RequestPinCode(self, device):
		print "RequestPinCode (%s)" % (device)
		return raw_input("Enter PIN Code: ")

	@dbus.service.method("org.bluez.Agent",
					in_signature="o", out_signature="u")
	def RequestPasskey(self, device):
		print "RequestPasskey (%s)" % (device)
		passkey = raw_input("Enter passkey: ")
		return dbus.UInt32(passkey)

	@dbus.service.method("org.bluez.Agent",
					in_signature="ou", out_signature="")
	def DisplayPasskey(self, device, passkey):
		print "DisplayPasskey (%s, %06d)" % (device, passkey)

	@dbus.service.method("org.bluez.Agent",
					in_signature="os", out_signature="")
	def DisplayPinCode(self, device, pincode):
		print "DisplayPinCode (%s, %s)" % (device, pincode)

	@dbus.service.method("org.bluez.Agent",
					in_signature="ou", out_signature="")
	def RequestConfirmation(self, device, passkey):
		print "RequestConfirmation (%s, %06d)" % (device, passkey)
		confirm = raw_input("Confirm passkey (yes/no): ")
		if (confirm == "yes"):
			return
		raise Rejected("Passkey doesn't match")

	@dbus.service.method("org.bluez.Agent",
					in_signature="s", out_signature="")
	def ConfirmModeChange(self, mode):
		print "ConfirmModeChange (%s)" % (mode)
		authorize = raw_input("Authorize mode change (yes/no): ")
		if (authorize == "yes"):
			return
		raise Rejected("Mode change by user")

	@dbus.service.method("org.bluez.Agent",
					in_signature="", out_signature="")
	def Cancel(self):
		print "Cancel"

def create_device_reply(device):
	print "New device (%s)" % (device)
	mainloop.quit()

def create_device_error(error):
	print "Creating device failed: %s" % (error)
	mainloop.quit()

def incoming_connection(*args, **kw):
	print "incoming connection %r %r" % (args, kw)


def _incoming_connection():
	print "incoming connection"

def device_released():
	print "device released"


def main(argv):
	dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

	bus = dbus.SystemBus()
	
	manager = dbus.Interface(bus.get_object("org.bluez", "/"),
							"org.bluez.Manager")
	

	path = manager.DefaultAdapter()

	adapter = dbus.Interface(bus.get_object("org.bluez", path),
							"org.bluez.GenericHID")

	adapter.connect_to_signal("IncomingConnection", incoming_connection)
	adapter.connect_to_signal("DeviceReleased", device_released)

	mainloop = gobject.MainLoop()
	print adapter


	#if len(args) > 1:
	#	if len(args) > 2:
	#		device = adapter.FindDevice(args[1])
	#		adapter.RemoveDevice(device)

	#	agent.set_exit_on_release(False)
	#	adapter.CreatePairedDevice(args[1], path, capability,
	#				reply_handler=create_device_reply,
	#				error_handler=create_device_error)
	#else:
	#	adapter.RegisterAgent(path, capability)
	#	print "Agent registered"

	mainloop.run()

	#adapter.UnregisterAgent(path)
	#

if __name__ == '__main__':
	main(sys.argv)
