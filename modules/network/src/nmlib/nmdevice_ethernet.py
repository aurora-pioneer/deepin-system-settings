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
from nmcache import cache
import time
import threading
nm_remote_settings = cache.getobject("/org/freedesktop/NetworkManager/Settings")
nmclient = cache.getobject("/org/freedesktop/NetworkManager")

class ThreadWiredAuto(threading.Thread):

    def __init__(self, device_path, connections):
        threading.Thread.__init__(self)
        self.device = cache.get_spec_object(device_path)
        self.conns = connections
        self.run_flag = True

    def run(self):
        while self.run_flag:
            for conn in self.conns:
                try:
                    active_conn = nmclient.activate_connection(conn.object_path, self.device.object_path, "/")
                    while(active_conn.get_state() == 1):
                        time.sleep(1)
 
                    if active_conn.get_state() == 2:
                        self.stop_run()
                        return True
                    else:
                        continue
                except:
                    pass

    def stop_run(self):
        self.run_flag = False

class NMDeviceEthernet(NMDevice):
    '''NMDeviceEthernet'''
    def __init__(self, ethernet_device_object_path):
        NMDevice.__init__(self, ethernet_device_object_path, "org.freedesktop.NetworkManager.Device.Wired")
        self.prop_list = ["Carrier", "HwAddress", "PermHwAddress", "Speed"]
        self.init_nmobject_with_properties()
        self.bus.add_signal_receiver(self.properties_changed_cb, dbus_interface = self.object_interface, 
                                     path = self.object_path, signal_name = "PropertiesChanged")

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

        if nm_remote_settings.get_wired_connections():

            wired_prio_connections = sorted(nm_remote_settings.get_wired_connections(),
                                    key = lambda x: int(nm_remote_settings.cf.get("conn_priority", x.settings_dict["connection"]["uuid"])),
                                    reverse = True)

            t = ThreadWiredAuto(self.object_path, wired_prio_connections)
            t.setDaemon(True)
            t.start()

        else:
            try:
                nmconn = nm_remote_settings.new_wired_connection()
                conn = nm_remote_settings.new_connection_finish(nmconn.settings_dict)
                nmclient.activate_connection(conn.object_path, self.object_path, "/")
            except:
                return False

    def dsl_auto_connect(self):
        if not cache.getobject(self.object_path).is_active():
            return False

        elif not nm_remote_settings.get_pppoe_connections():
            return False
        else:
            pppoe_prio_connections = sorted(nm_remote_settings.get_pppoe_connections(),
                                    key = lambda x: int(nm_remote_settings.cf.get("conn_priority", x.settings_dict["connection"]["uuid"])),
                                    reverse = True)

            t = ThreadWiredAuto(self.object_path, pppoe_prio_connections)
            t.setDaemon(True)
            t.start()

    def properties_changed_cb(self, prop_dict):
        self.init_nmobject_with_properties()

if __name__ == "__main__":
    ethernet_device = NMDeviceEthernet ("/org/freedesktop/NetworkManager/Devices/0")
    print ethernet_device.properties
