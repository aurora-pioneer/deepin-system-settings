#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012 ~ 2013 Deepin, Inc.
#               2012 ~ 2013 Long Wei
#
# Author:     Long Wei <yilang2007lw@gmail.com>
# Maintainer: Long Wei <yilang2007lw@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import gobject
import gudev
import os
import glib
import traceback
from nmobject import NMObject
from nmcache import get_cache
from nm_utils import TypeConvert
try:
    from network.src.nmlib.nm_dispatcher import nm_events
except:
    from nm_dispatcher import nm_events

udev_client = gudev.Client("net")

class NMDevice(NMObject):
    '''NMDevice'''

    __gsignals__  = {
            "state-changed":(gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_UINT, gobject.TYPE_UINT, gobject.TYPE_UINT)),
            "device-active":(gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_UINT, gobject.TYPE_UINT, gobject.TYPE_UINT)),
            "device-deactive":(gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_UINT, gobject.TYPE_UINT, gobject.TYPE_UINT)),
            "device-available":(gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_UINT, gobject.TYPE_UINT, gobject.TYPE_UINT)),
            "device-unavailable":(gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_UINT, gobject.TYPE_UINT, gobject.TYPE_UINT)),
            "activate-start":(gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_UINT, gobject.TYPE_UINT, gobject.TYPE_UINT)),
            "activate-failed":(gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_UINT, gobject.TYPE_UINT, gobject.TYPE_UINT))
            }

    def __init__(self, device_object_path, device_interface = "org.freedesktop.NetworkManager.Device"):
        NMObject.__init__(self, device_object_path, device_interface)

        self.prop_list = ["Capabilities", "DeviceType", "ActiveConnection", "Dhcp4Config", "Dhcp6Config", "Driver", "FirmwareMissing", "Interface", "IpInterface", "Ip4Config", "Ip6Config", "Managed", "State"]

        self.state_match = self.bus.add_signal_receiver(self.state_changed_cb, dbus_interface = self.object_interface, 
                                     path = self.object_path, signal_name = "StateChanged")

        self.init_nmobject_with_properties()
        self.udev_device = ""
        self.state_id = 0
        self.new_state = 0
        
        try:
            self.is_dsl = self.get_real_active_connection().get_setting('connection').type == 'pppoe'
        except:
            self.is_dsl = False

    def remove_signals(self):
        try:
            self.bus.remove_signal_receiver(self.state_match, dbus_interface = self.object_interface,
                                         path = self.object_path, signal_name = "StateChanged")
        except:
            print "remove signals failed"

    def get_capabilities(self):
        return self.properties["Capabilities"]

    def get_device_type(self):
        return self.properties["DeviceType"]

    def get_active_connection(self):
        '''return active connection object'''
        if self.properties["ActiveConnection"]:
            return get_cache().getobject(self.properties["ActiveConnection"])
        else:
            return None

    def get_available_connections(self):
        return map(lambda c: get_cache().getobject(c) , self.properties["AvailableConnections"])

    def is_active(self):
        try:
            if self.get_active_connection() and self.get_active_connection().get_state() == 2:
                return True
            else:
                return False
        except:
            return False

    def is_connection_active(self, connection_path):
        return connection_path == self.get_real_active_connection()

    def get_real_active_connection(self):
        if self.get_active_connection():
            return self.get_active_connection().get_connection()

    def get_ip4address(self):
        return TypeConvert.ip4_net2native(self.properties["Ip4Address"])

    def get_dhcp4_config(self):
        return get_cache().getobject(self.properties["Dhcp4Config"])

    def get_dhcp6_config(self):
        return get_cache().getobject(self.properties["Dhcp6Config"])

    def get_driver(self):
        return self.properties["Driver"]

    def get_firmware_missing(self):
        return self.properties["FirmwareMissing"]

    def get_iface(self):
        return self.properties["Interface"]

    def get_ip_iface(self):
        return self.properties["IpInterface"]

    def get_ip4_config(self):
        return get_cache().getobject(self.properties["Ip4Config"])

    def get_ip6_config(self):
        return get_cache().getobject(self.properties["Ip6Config"])

    def get_managed(self):
        return self.properties["Managed"]

    def get_state(self):
        return self.properties["State"]
    
    def get_udi(self):
        return self.properties["Udi"]

    def get_udev_device(self):
        if self.udev_device:
            pass
        else:
            try:
                if self.get_udi():
                    self.udev_device =  udev_client.query_by_sysfs_path(self.get_udi())
                elif self.get_iface():
                    self.udev_device =  udev_client.query_by_subsystem_and_name("net", self.get_iface())
                else:
                    pass
                if not self.udev_device:
                    raise Exception
            except:
                traceback.print_exc()
        return self.udev_device    

    def get_vendor(self):
        if self.get_udev_device().has_property("ID_VENDOR_FROM_DATABASE"):
            return self.get_udev_device().get_property("ID_VENDOR_FROM_DATABASE")

    def get_product(self):
        if self.get_udev_device().has_property("ID_MODEL_FROM_DATABASE"):
            return self.get_udev_device().get_property("ID_MODEL_FROM_DATABASE")

    def get_device_desc(self):
        self.udev_device = self.get_udev_device()

        if not self.udev_device:
            return "unknown device"

        if self.udev_device.has_property("ID_BUS"):

            if self.udev_device.get_property("ID_BUS") == "pci":

                if self.udev_device.has_property("ID_VENDOR_FROM_DATABASE") and self.udev_device.has_property(
                    "ID_MODEL_FROM_DATABASE"):
                    return self.udev_device.get_property("ID_VENDOR_FROM_DATABASE") + " "+ self.udev_device.get_property("ID_MODEL_FROM_DATABASE")
                elif self.udev_device.has_property("ID_MODEL_FROM_DATABASE"):
                    return self.udev_device.get_property("ID_MODEL_FROM_DATABASE")

                elif self.udev_device.has_property("ID_MODEL_ID"):
                    cmd = "lspci -s %s" % self.udev_device.get_property("ID_MODEL_ID").split("/")[-1]
                    return os.popen(cmd).read().split(":")[-1].split("(")[0]
        
                elif self.udev_device.has_property("DEVPATH"):
                    cmd = "lspci -s %s" % self.udev_device.get_property("DEVPATH").split("/")[-3]
                    return os.popen(cmd).read().split(":")[-1].split("(")[0]

                elif self.udev_device.has_property("ID_VENDOR_FROM_DATABASE"):
                    return self.udev_device.get_property("ID_VENDOR_FROM_DATABASE")
        
                else:
                    cmd = "lspci -s %s" % self.udev_device.get_sysfs_path().split("/")[-3]
                    return os.popen(cmd).read().split(":")[-1].split("(")[0]

            elif self.udev_device.get_property("ID_BUS") == "usb":

                if self.udev_device.has_property("ID_VENDOR_FROM_DATABASE") and self.udev_device.has_property("ID_MODEL"):
                    return self.udev_device.get_property("ID_VENDOR_FROM_DATABASE") + " "+self.udev_device.get_property("ID_MODEL")

                elif self.udev_device.has_property("ID_MODEL"):
                    return self.udev_device.get_property("ID_MODEL")

                elif self.udev_device.has_property("ID_VENDOR"):
                    return self.udev_device.get_property("ID_VENDOR")
        else:
            return "unknown device"

    def nm_device_disconnect(self):
        self.dbus_method("Disconnect", reply_handler = self.disconnect_finish, error_handler = self.disconnect_error)

    def disconnect_finish(self, *reply):
        pass
        
    def disconnect_error(self, *error):
        pass

    def emit_cb(self):
        self.state_id = 0
        return False

    def emit_in_time(self, *args):
        if args[1] != self.new_state and self.new_state != 0:
            if self.state_id:
                glib.source_remove(self.state_id)
            self.state_id = 0

        if self.state_id > 0:
            return
        else:
            if self.is_dsl:
                #print "Debug[nmdevice]+ dsl", args, self.state_id
                nm_events.emit("dsl-" + args[0], args[1:])
            else:
                #print "Debug[nmdevice]", args, self.state_id
                self.emit(*args)
            if args[1] != 100 and args[1] != 40:
                self.is_dsl = False
            self.state_id = glib.timeout_add(300, self.emit_cb)
        self.new_state = args[1]

    def state_changed_cb(self, new_state, old_state, reason):
        if new_state > 90 or new_state < 70:
            self.init_nmobject_with_properties()
        #print new_state, old_state, reason

        if new_state == 30 and old_state < 30:
            self.emit_in_time("device-available", new_state, old_state, reason)
            return
        
        #if old_state == 100 or reason ==39 or reason == 42 or reason == 36:
        if new_state == 30 and old_state > 30:
            self.emit_in_time("device-deactive", new_state, old_state, reason)
            return 

        if new_state == 40:
            try:
                self.is_dsl = self.get_real_active_connection().get_setting('connection').type == 'pppoe'
            except:
                self.is_dsl = False
            self.emit_in_time("activate-start", new_state, old_state, reason)
            return 

        if new_state == 100:
            try:
                conn_uuid = self.get_real_active_connection().settings_dict["connection"]["uuid"]
                self.emit_in_time("device-active", new_state, old_state, reason)
                nm_remote_settings = get_cache().getobject("/org/freedesktop/NetworkManager/Settings")
                try:
                    priority = int(nm_remote_settings.cf.getint("conn_priority", conn_uuid) + 1 )
                except:
                    priority = 1

                nm_remote_settings.cf.set("conn_priority", conn_uuid, priority)
                nm_remote_settings.cf.write(open(nm_remote_settings.config_file, "w"))
            except:
                pass
            return 

        if new_state == 120:
            self.emit_in_time("activate-failed", new_state, old_state, reason)
            return 

        if new_state == 10 or new_state == 20:
            self.emit_in_time("device-unavailable", new_state, old_state, reason)
            return 

if __name__ == "__main__":
    nmdevice = NMDevice("/org/freedesktop/NetworkManager/Devices/1")
    print nmdevice.get_product()
    # print nmdevice.properties
    # nmdevice.nm_device_disconnect()
    print nmdevice.get_state()
