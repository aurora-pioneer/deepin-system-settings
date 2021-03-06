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
import dbus
import dbus.service
import dbus.mainloop.glib

class MediaEndpoint(dbus.service.Object):

    def __init__(self, path = "/org/bluez/mediaendpoint", bus = None):
        if bus is None:
	    bus = dbus.SystemBus()    
    
        dbus.service.Object.__init__(self, bus, path)	

    @dbus.service.method("org.bluez.MediaEndpoint", in_signature="ov", out_signature="")
    def SetConfiguration(self, transport, properties):
	pass
    
    @dbus.service.method("org.bluez.MediaEndpoint", in_signature="o", out_signature="")
    def ClearConfiguration(self, transport):
	pass
    
    @dbus.service.method("org.bluez.MediaEndpoint", in_signature="", out_signature="")
    def Release(self):
	pass
    
if __name__ == '__main__':
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SystemBus()
    path = "/test/mediaplayer"

    mediaendpoint = MediaEndpoint(path, bus)
    mainloop = gobject.MainLoop()
    mainloop.run()
