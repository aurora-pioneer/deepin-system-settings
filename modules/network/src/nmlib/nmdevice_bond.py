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

class NMDeviceBond(NMDevice):
    '''NMDeviceBond'''

    def __init__(self, bond_device_object_path):
        NMDevice.__init__(self, bond_device_object_path, "org.freedesktop.NetworkManager.Device.Bond")

    def get_hw_address(self):
        return self.properties["HwAddress"]

    def get_carrier(self):
        return self.properties["Carrier"]

    