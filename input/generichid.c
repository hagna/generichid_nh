/*
 *
 *  BlueZ - Bluetooth protocol stack for Linux
 *
 *  Copyright (C) 2006-2007  Nokia Corporation
 *  Copyright (C) 2004-2009  Marcel Holtmann <marcel@holtmann.org>
 *
 *
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program; if not, write to the Free Software
 *  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 *
 */

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <errno.h>
#include <stdlib.h>
#include <string.h>

#include <bluetooth/bluetooth.h>
#include <bluetooth/hci.h>
#include <bluetooth/hci_lib.h>
#include <bluetooth/sdp.h>
#include <bluetooth/sdp_lib.h>

#include <gdbus.h>

#include "plugin.h"
#include "adapter.h"
#include "error.h"
#include "logging.h"

#define GENERIC_HID_INTERFACE "org.bluez.GenericHID"

static DBusConnection *connection;

struct generic_hid_adapter {
	struct btd_adapter *adapter;
	struct btd_device *device;
};

static inline DBusMessage *not_implemented(DBusMessage *msg)
{
	return g_dbus_create_error(msg, ERROR_INTERFACE ".NotImplemented",
							"Not Implemented (yet)");
}

static DBusMessage *send_event(DBusConnection *conn,
		DBusMessage *msg, void *data)
{
	return not_implemented(msg);
}

static DBusMessage *get_properties(DBusConnection *conn,
		DBusMessage *msg, void *data)
{
	return not_implemented(msg);
}

static GDBusMethodTable ghid_adapter_methods[] = {
	{ "SendEvent",		"u",	"",	send_event	},
	{ "GetProperties",	"",	"a{sv}",get_properties	},
	{ }
};

static int register_interface(const char *path, struct btd_adapter *adapter)
{
	struct generic_hid_adapter *ghid_adapter;

	DBG("path %s", path);

	ghid_adapter = g_try_new0(struct generic_hid_adapter, 1);
	if (ghid_adapter == NULL)
		return -ENOMEM;

	ghid_adapter->adapter = adapter;

	if (g_dbus_register_interface(connection, path, GENERIC_HID_INTERFACE,
					ghid_adapter_methods, NULL, NULL,
					ghid_adapter, NULL) == FALSE) {
		error("D-Bus failed to register %s interface",
				GENERIC_HID_INTERFACE);
		g_free(ghid_adapter);
		return -EIO;
	}

	debug("Registered interface %s on path %s", GENERIC_HID_INTERFACE, path);

	return 0;
}

static void unregister_interface(const char *path)
{
	DBG("path %s", path);

	g_dbus_unregister_interface(connection, path, GENERIC_HID_INTERFACE);
}

static int ghid_probe(struct btd_adapter *adapter)
{
	register_interface(adapter_get_path(adapter), adapter);

	return 0;
}

static void ghid_remove(struct btd_adapter *adapter)
{
	unregister_interface(adapter_get_path(adapter));
}

static struct btd_adapter_driver ghid_driver = {
	.name	= "generic-hid",
	.probe	= ghid_probe,
	.remove	= ghid_remove,
};

static int generic_hid_init(void)
{
	int err;

	connection = dbus_bus_get(DBUS_BUS_SYSTEM, NULL);
	if (connection == NULL)
		return -EIO;

	err = btd_register_adapter_driver(&ghid_driver);
	if (err < 0) {
		dbus_connection_unref(connection);
		return err;
	}

	return 0;
}

static void generic_hid_exit(void)
{
	btd_unregister_adapter_driver(&ghid_driver);

	dbus_connection_unref(connection);
}

BLUETOOTH_PLUGIN_DEFINE(generichid, VERSION,
		BLUETOOTH_PLUGIN_PRIORITY_LOW, generic_hid_init, generic_hid_exit)
