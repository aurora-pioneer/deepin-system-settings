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

from pulseaudio import BusBase
import gobject

class Module(BusBase):
    
    __gsignals__  = {
            "property-list-updated":(gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))
            }
    
    def __init__(self, path , interface = "org.PulseAudio.Core1.Module"):
        BusBase.__init__(self, path, interface)

        self.dbus_proxy.connect_to_signal("PropertyListUpdated", self.property_list_updated_cb, dbus_interface = 
                                          self.object_interface, arg0 = None)
        
    ###Props    
    def get_index(self):
        return int(self.get_property("Index"))

    def get_name(self):
        return str(self.get_property("Name"))
        
    def get_arguments(self):
        return dict(self.get_property("Arguments"))

    def get_usage_counter(self):
        return int(self.get_property("UsageCounter"))

    def get_property_list(self):
        return dict(self.get_property("PropertyList"))
    ###Methods
    def unload(self):
        self.call_async("Unload", reply_handler = None, error_handler = None)

    ###Signals
    def property_list_updated_cb(self, property_list):
        self.emit("property-list-updated", property_list)

    
if __name__ == "__main__":
    pass
