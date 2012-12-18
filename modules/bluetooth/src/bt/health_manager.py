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

from bus_utils import BusBase

class HealthManager(BusBase):

    def __init__(self):
        BusBase.__init__(self, path = "/org/bluez/", interface = "org.bluez.HealthManager")

    def create_application(self, config):
        return self.dbus_method("CreateApplication", config)
        
    def destroy_application(self, application):
        return self.dbus_method("DestroyApplication", application)

if __name__ == "__main__":
    pass
