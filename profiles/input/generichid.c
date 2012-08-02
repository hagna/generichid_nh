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

#include <bluetooth/sdp.h>
#include <bluetooth/sdp_lib.h>

#include <gdbus.h>
#include <dbus/dbus.h>
#include "plugin.h"
#include "adapter.h"
#include "btio.h"
#include "../profiles/input/device.h"

#define GENERIC_HID_INTERFACE "org.bluez.GenericHID"

static GSList *adapters = NULL;

static DBusConnection *connection;

struct device_data {
	GIOChannel *ctrl;
	GIOChannel *intr;
	bdaddr_t dst;
	unsigned int intr_watch;
	char *input_path;
};

struct adapter_data {
	struct btd_adapter *adapter;
	struct device_data *dev;
	uint32_t sdp_record_handle;
	GIOChannel *listen_ctrl;
	GIOChannel *listen_intr;
	int pending;
	char active;
};

static void add_lang_attr(sdp_record_t *r)
{
	sdp_lang_attr_t base_lang;
	sdp_list_t *langs = 0;

	/* UTF-8 MIBenum (http://www.iana.org/assignments/character-sets) */
	base_lang.code_ISO639 = (0x65 << 8) | 0x6e;
	base_lang.encoding = 106;
	base_lang.base_offset = SDP_PRIMARY_LANG_BASE;
	langs = sdp_list_append(0, &base_lang);
	sdp_set_lang_attr(r, langs);
	sdp_list_free(langs, 0);
}

static int sdp_keyboard_service(struct adapter_data *adapt)
{
	bdaddr_t src;
	sdp_record_t *record;
	sdp_list_t *svclass_id, *pfseq, *apseq, *root;
	uuid_t root_uuid, hidkb_uuid, l2cap_uuid, hidp_uuid;
	sdp_profile_desc_t profile[1];
	sdp_list_t *aproto, *proto[3];
	sdp_data_t *psm, *lang_lst, *lang_lst2, *hid_spec_lst, *hid_spec_lst2;
	unsigned int i;
	uint8_t dtd = SDP_UINT16;
	uint8_t dtd2 = SDP_UINT8;
	uint8_t dtd_data = SDP_TEXT_STR8;
	void *dtds[2];
	void *values[2];
	void *dtds2[2];
	void *values2[2];
	int leng[2];
	uint8_t hid_spec_type = 0x22;
	uint16_t hid_attr_lang[] = { 0x409, 0x100 };
	static const uint16_t ctrl = 0x11;
	static const uint16_t intr = 0x13;
	static const uint16_t hid_attr[] = { 0x100, 0x111, 0x40,
						0x0d, 0x01, 0x01 };
	static const uint16_t hid_attr2[] = { 0x0, 0x01, 0x100,
						0x1f40, 0x01, 0x01 };
	const uint8_t hid_spec[] = {
		0x05, 0x01, /*	Usage Page (Generic Desktop)		*/
		0x09, 0x06, /*	Usage (Keyboard)			*/
		0xA1, 0x01, /*	Collection (Application)		*/
		0x85, 0x01, /*	Report ID				*/
		0x05, 0x07, /*	Usage (Key codes)			*/
		0x19, 0xE0, /*	Usage Minimum (224)			*/
		0x29, 0xE7, /*	Usage Maximum (231)			*/
		0x15, 0x00, /*	Logical Minimum (0)			*/
		0x25, 0x01, /*	Logical Maximum (1)			*/
		0x75, 0x01, /*	Report Size (1)				*/
		0x95, 0x08, /*	Report Count (8)			*/
		0x81, 0x02, /*	Input (Data, Variable, Absolute)	*/
		0x95, 0x01, /*	Report Count (1)			*/
		0x75, 0x08, /*	Report Size (8)				*/
		0x81, 0x01, /*	Input (Constant)    ;5 bit padding	*/
		0x95, 0x05, /*	Report Count (5)			*/
		0x75, 0x01, /*	Report Size (1)				*/
		0x05, 0x08, /*	Usage Page (Page# for LEDs)		*/
		0x19, 0x01, /*	Usage Minimum (01)			*/
		0x29, 0x05, /*	Usage Maximum (05)			*/
		0x91, 0x02, /*	Output (Data, Variable, Absolute)	*/
		0x95, 0x01, /*	Report Count (1)			*/
		0x75, 0x03, /*	Report Size (3)				*/
		0x91, 0x01, /*	Output (Constant)			*/
		0x95, 0x06, /*	Report Count (1)			*/
		0x75, 0x08, /*	Report Size (3)				*/
		0x15, 0x00, /*	Logical Minimum (0)			*/
		0x25, 0x65, /*	Logical Maximum (101)			*/
		0x05, 0x07, /*	Usage (Key codes)			*/
		0x19, 0x00, /*	Usage Minimum (00)			*/
		0x29, 0x65, /*	Usage Maximum (101)			*/
		0x81, 0x00, /*	Input (Data, Array)			*/
		0xC0,
		0x09, 0x02, /* mouse part starts here */
		0xa1, 0x01,
		0x09, 0x01,
		0xa1, 0x00,
		0x85, 0x02,
		0x05, 0x09,
		0x19, 0x01,
		0x29, 0x05,
		0x15, 0x00,
		0x25, 0x01,
		0x95, 0x05,
		0x75, 0x01,
		0x81, 0x02,
		0x95, 0x01,
		0x75, 0x03,
		0x81, 0x01,
		0x05, 0x01,
		0x09, 0x30,
		0x09, 0x31,
		0x09, 0x38,
		0x15, 0x81,
		0x25, 0x7f,
		0x75, 0x08,
		0x95, 0x03,
		0x81, 0x06,
		0x05, 0x0c,
		0x0a, 0x38, 0x02,
		0x15, 0x81,
		0x25, 0x7f,
		0x75, 0x08,
		0x95, 0x01,
		0x81, 0x06,
		0xc0,
		0xc0
	};

	record = sdp_record_alloc();
	memset(record, 0, sizeof(sdp_record_t));
	record->handle = 0xffffffff;
	bacpy(&src, BDADDR_ANY);

	sdp_uuid16_create(&root_uuid, PUBLIC_BROWSE_GROUP);
	root = sdp_list_append(0, &root_uuid);
	sdp_set_browse_groups(record, root);

	add_lang_attr(record);

	sdp_uuid16_create(&hidkb_uuid, HID_SVCLASS_ID);
	svclass_id = sdp_list_append(0, &hidkb_uuid);
	sdp_set_service_classes(record, svclass_id);

	sdp_uuid16_create(&profile[0].uuid, HID_PROFILE_ID);
	profile[0].version = 0x0100;
	pfseq = sdp_list_append(0, profile);
	sdp_set_profile_descs(record, pfseq);

	/* protocols */
	sdp_uuid16_create(&l2cap_uuid, L2CAP_UUID);
	proto[1] = sdp_list_append(0, &l2cap_uuid);
	psm = sdp_data_alloc(SDP_UINT16, &ctrl);
	proto[1] = sdp_list_append(proto[1], psm);
	apseq = sdp_list_append(0, proto[1]);

	sdp_uuid16_create(&hidp_uuid, HIDP_UUID);
	proto[2] = sdp_list_append(0, &hidp_uuid);
	apseq = sdp_list_append(apseq, proto[2]);

	aproto = sdp_list_append(0, apseq);
	sdp_set_access_protos(record, aproto);

	sdp_list_free(root, 0);
	sdp_list_free(aproto, 0);
	sdp_list_free(apseq, 0);
	sdp_list_free(proto[1], 0);
	sdp_list_free(proto[2], 0);
	sdp_data_free(psm);

	/* additional protocols */
	proto[1] = sdp_list_append(0, &l2cap_uuid);
	psm = sdp_data_alloc(SDP_UINT16, &intr);
	proto[1] = sdp_list_append(proto[1], psm);
	apseq = sdp_list_append(0, proto[1]);

	sdp_uuid16_create(&hidp_uuid, HIDP_UUID);
	proto[2] = sdp_list_append(0, &hidp_uuid);
	apseq = sdp_list_append(apseq, proto[2]);

	aproto = sdp_list_append(0, apseq);
	sdp_set_add_access_protos(record, aproto);

	sdp_list_free(svclass_id, 0);
	sdp_list_free(proto[1], 0);
	sdp_list_free(proto[2], 0);
	sdp_list_free(pfseq, 0);
	sdp_list_free(apseq, 0);
	sdp_list_free(aproto, 0);
	sdp_data_free(psm);

	sdp_set_info_attr(record, "HID Keyboard", NULL, NULL);

	for (i = 0; i < sizeof(hid_attr) / 2; i++)
		sdp_attr_add_new(record,
					SDP_ATTR_HID_DEVICE_RELEASE_NUMBER + i,
					SDP_UINT16, &hid_attr[i]);

	dtds[0] = &dtd2;
	values[0] = &hid_spec_type;
	dtds[1] = &dtd_data;
	values[1] = (uint8_t *) hid_spec;
	leng[0] = 0;
	leng[1] = sizeof(hid_spec);
	hid_spec_lst = sdp_seq_alloc_with_length(dtds, values, leng, 2);
	hid_spec_lst2 = sdp_data_alloc(SDP_SEQ8, hid_spec_lst);
	sdp_attr_add(record, SDP_ATTR_HID_DESCRIPTOR_LIST, hid_spec_lst2);

	for (i = 0; i < sizeof(hid_attr_lang) / 2; i++) {
		dtds2[i] = &dtd;
		values2[i] = &hid_attr_lang[i];
	}

	lang_lst = sdp_seq_alloc(dtds2, values2, sizeof(hid_attr_lang) / 2);
	lang_lst2 = sdp_data_alloc(SDP_SEQ8, lang_lst);
	sdp_attr_add(record, SDP_ATTR_HID_LANG_ID_BASE_LIST, lang_lst2);

	sdp_attr_add_new(record, SDP_ATTR_HID_SDP_DISABLE,
				SDP_UINT16, &hid_attr2[0]);

	for (i = 0; i < sizeof(hid_attr2) / 2 - 1; i++)
		sdp_attr_add_new(record, SDP_ATTR_HID_REMOTE_WAKEUP + i,
						SDP_UINT16, &hid_attr2[i + 1]);

	if (add_record_to_server(&src, record) < 0)
		return -1;

	adapt->sdp_record_handle = record->handle;

	btd_debug("HID service registered with record handle %x", record->handle);

	return 0;
}

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

static void confirm_event_cb(GIOChannel *chan, GError *err, gpointer data)
{
	uint16_t psm;
	GError *gerr = NULL;
	bdaddr_t dst;
	struct adapter_data *adapt = data;
	struct device_data *dev = adapt->dev;

	if (err) {
		error("%s\n", err->message);
		return;
	}

	bt_io_get(chan, BT_IO_L2CAP, &gerr,
			BT_IO_OPT_DEST_BDADDR, &dst,
			BT_IO_OPT_PSM, &psm,
			BT_IO_OPT_INVALID);
	if (gerr) {
		error("%s on PSM %d\n", gerr->message, psm);
		g_error_free(gerr);
		g_io_channel_shutdown(chan, TRUE, NULL);
		return;
	}

	if (dev->input_path != NULL &&
			(bacmp(&(dev->dst), &dst) != 0 ||
			dev->intr != NULL)) {

		btd_debug("Incoming request blocked due to existing input device");
		g_io_channel_shutdown(chan, TRUE, NULL);
		return;
	}

	btd_debug("Incoming connection on PSM number %d", psm);

	if (psm == 17)
		adapt->pending = 1;

	/* TODO if (!bt_io_accept(chan, connect_cb, data, NULL, NULL))
		btd_debug("Can not accept connection on psm %d", psm); */
}

static int adapt_start(struct adapter_data *adapt)
{
	GError *err = NULL;
	bdaddr_t src;
	struct device_data *dev = adapt->dev;

	adapter_get_address(adapt->adapter, &src);

	adapt->listen_ctrl = bt_io_listen(BT_IO_L2CAP, confirm_event_cb,
						NULL, adapt, NULL, &err,
						BT_IO_OPT_SOURCE_BDADDR, &src,
						BT_IO_OPT_PSM, L2CAP_PSM_HIDP_CTRL,
						BT_IO_OPT_INVALID);
	if (!adapt->listen_ctrl) {
		error("Failed to listen on control channel");
		g_error_free(err);
		g_free(adapt);
		return -ENOTCONN;
	}

	adapt->listen_intr = bt_io_listen(BT_IO_L2CAP, confirm_event_cb,
						NULL, adapt, NULL, &err,
						BT_IO_OPT_SOURCE_BDADDR, &src,
						BT_IO_OPT_PSM, L2CAP_PSM_HIDP_INTR,
						BT_IO_OPT_INVALID);
	if (!adapt->listen_intr) {
		error("Failed to listen on interrupt channel");
		/* TODO: fix this */
		g_io_channel_unref(dev->ctrl);
		dev->ctrl = NULL;
		g_error_free(err);
		g_free(adapt);
		return -ENOTCONN;
	}

	return 0;
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

    if (sdp_keyboard_service(adapt) < 0) {
		btd_debug("Adding HID SDP service failed");
		g_free(adapt);
		return -1;
	}

    if (adapt_start(adapt) < 0)
		return -ENOTCONN;

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