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

from nmdevice import NMDevice
from nm_utils import TypeConvert
from nm_remote_settings import nm_remote_settings
from nmclient import nmclient
from nmcache import cache

class NMDeviceEthernet(NMDevice):
    '''NMDeviceEthernet'''

    def __init__(self, ethernet_device_object_path):
        NMDevice.__init__(self, ethernet_device_object_path, "org.freedesktop.NetworkManager.Device.Wired")
        self.prop_list = ["Carrier", "HwAddress", "PermHwAddress", "Speed"]
        self.init_nmobject_with_properties()
        self.bus.add_signal_receiver(self.properties_changed_cb, dbus_interface = self.object_interface, signal_name = "PropertiesChanged")

    ###Methods###
    def get_carrier(self):
        return self.properties["Carrier"]

    def get_hw_address(self):
        return self.properties["HwAddress"]

    def get_perm_hw_address(self):
        return self.properties["PermHwAddress"]

    def get_speed(self):
        return self.properties["Speed"]

    def auto_connect(self):
        if cache.getobject(self.object_path).is_active():
            return True
        if cache.getobject(self.object_path).get_state() < 30:
            return False

        wired_connections = nm_remote_settings.get_wired_connections()
        if len(wired_connections) != 0:
            for conn in wired_connections:
                try:
                    nmclient.activate_connection(conn.object_path, self.object_path, "/")
                    if cache.getobject(self.object_path).is_active():
                        return True
                    else:
                        continue
                except:
                    continue
        else:        
            try:
                conn = nm_remote_settings.new_wired_connection()
                nmclient.activate_connection(conn.object_path, self.object_path, "/")
                if cache.getobject(self.object_path).is_active():
                    return True
                else:
                    return False
            except:
                return False

    def properties_changed_cb(self, prop_dict):
        self.init_nmobject_with_properties()

if __name__ == "__main__":
    ethernet_device = NMDeviceEthernet ("/org/freedesktop/NetworkManager/Devices/0")
    print ethernet_device.properties