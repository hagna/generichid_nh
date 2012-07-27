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
#include <gdbus.h>
#include <dbus/dbus.h>
#include "plugin.h"
#include "adapter.h"

#define GENERIC_HID_INTERFACE "org.bluez.GenericHID"

static GSList *adapters = NULL;

static DBusConnection *connection;

struct device_data {
};

struct adapter_data {
	struct btd_adapter *adapter;
	struct device_data *dev;
	int pending;
	char active;
};

static const GDBusSignalTable ghid_adapter_signals[] = {
	{ GDBUS_SIGNAL("IncomingConnection", NULL) },
	{ GDBUS_SIGNAL("DeviceReleased", NULL) },
	{ }
};

static const GDBusMethodTable ghid_adapter_methods[] = {
	{ }
};

static void register_interface(const char *path, struct adapter_data *adapt)
{
	if (g_dbus_register_interface(connection, path, GENERIC_HID_INTERFACE,
					ghid_adapter_methods, ghid_adapter_signals,
					NULL, adapt, NULL) == FALSE) {
		error("D-Bus failed to register %s interface",
				GENERIC_HID_INTERFACE);
		return;
	}

	btd_debug("Registered interface %s path %s", GENERIC_HID_INTERFACE, path);

}

static int ghid_probe(struct btd_adapter *adapter)
{
	struct adapter_data *adapt;

	adapt = g_try_new0(struct adapter_data, 1);
	if (adapt == NULL)
		return -ENOMEM;

	adapt->dev = g_try_new0(struct device_data, 1);
	if (adapt->dev == NULL) {
		g_free(adapt);
		return -ENOMEM;
	}

	adapt->pending = 0;
	adapt->adapter = adapter;
	adapt->active = 0;

	register_interface(adapter_get_path(adapter), adapt);

	adapters = g_slist_append(adapters, adapt);

	return 0;
}

static struct btd_adapter_driver ghid_driver = {
	.name	= "generic-hid",
	.probe	= ghid_probe,
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
