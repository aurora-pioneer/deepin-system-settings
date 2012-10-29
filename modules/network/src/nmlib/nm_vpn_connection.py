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
from nm_active_connection import NMActiveConnection

class NMVpnConnection(NMActiveConnection):
    '''NMVpnConnection'''
        
    __gsignals__  = {
            "vpn-state-changed":(gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_UINT, gobject.TYPE_UINT)),
            }

    def __init__(self, vpn_connection_object_path):
        NMActiveConnection.__init__(self, vpn_connection_object_path, "org.freedesktop.NetworkManager.VPN.Connection")
        self.bus.add_signal_receiver(self.vpn_state_changed_cb, dbus_interface = self.object_interface, signal_name = "Vpnstatechanged")
        self.bus.add_signal_receiver(self.properties_changed_cb, dbus_interface = self.object_interface, signal_name = "PropertiesChanged")

        self.init_nmobject_with_properties()

    def get_banner(self):
        return self.properties["Banner"]

    def get_vpnstate(self):
        return self.properties["VpnState"]

    ###Signals###
    def vpn_state_changed_cb(self, arg1, arg2):
        self.emit("vpn-state-changed", arg1, arg2)

    
if __name__ == "__main__":
    pass
