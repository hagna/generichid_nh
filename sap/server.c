/*
 *  BlueZ - Bluetooth protocol stack for Linux
 *
 *  Copyright (C) 2010 ST-Ericsson SA
 *
 *  Author: Waldemar Rymarkiewicz <waldemar.rymarkiewicz@tieto.com> for ST-Ericsson.
 *
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; version 2 of the License.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program; if not, write to the Free Software
 *  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 */

#include "bluetooth.h"
#include "log.h"

#include "server.h"

int sap_server_register(const char *path, bdaddr_t *src)
{
	DBG("Register SAP server.");
	return 0;
}

int sap_server_unregister(const char *path)
{
	DBG("Unregister SAP server.");
	return 0;
}

int sap_server_init(DBusConnection *conn)
{
	DBG("Init SAP server.");
	return 0;
}

void sap_server_exit(void)
{
	DBG("Exit SAP server.");
}