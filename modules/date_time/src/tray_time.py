#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012 Deepin, Inc.
#               2012 Hailong Qiu
#
# Author:     Hailong Qiu <356752238@qq.com>
# Maintainer: Hailong Qiu <356752238@qq.com>
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

import time
from timer import Timer
import gobject
from nls import _
try:
    import deepin_gsettings
    deepin_gsettings_bool = 1
except:
    print "Please install deepin linux[www.linuxdeepin.com]..."
    deepin_gsettings_bool = 0


TRAY_TIME_12_HOUR = 1
TRAY_TIME_24_HOUR = 0

class TrayTime(gobject.GObject):
    __gsignals__ = {
        "send-time" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                      (gobject.TYPE_PYOBJECT, gobject.TYPE_INT)),
        "hour-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                      (gobject.TYPE_PYOBJECT, gobject.TYPE_INT)),
        }        
    def __init__(self):
        gobject.GObject.__init__(self)
        self.__timer = Timer(5000)
        self.__tray_time_hour_type = TRAY_TIME_12_HOUR
        self.__timer.connect("Tick", self.__update_time)
        # setting 12/24 hour.    
        if deepin_gsettings_bool:
            self.set_date = deepin_gsettings.new("com.deepin.dde.datetime")
            self.set_date.connect("changed", self.set_date_changed)
            self.set_deepin_dde_datetime()
        # start time.
        self.__timer.Enabled  = True 

    def set_date_changed(self, key):
        self.set_deepin_dde_datetime() 

    def set_hour_type(self, hour_type):
        self.__tray_time_hour_type = hour_type
        self.emit("hour-changed", self.get_time(), self.__tray_time_hour_type)

    def set_deepin_dde_datetime(self):
        if self.set_date.get_boolean("is-24hour"):
            self.set_hour_type(TRAY_TIME_24_HOUR)
        else:
            self.set_hour_type(TRAY_TIME_12_HOUR)

    def get_time(self):
        time_struct = time.localtime(time.time())
        #
        if self.__tray_time_hour_type == TRAY_TIME_12_HOUR: 
            time_show_text = time.strftime("%P %I %M", time.localtime()).split(" ")
            if time_show_text[0].startswith(("a", "p")):
                am = _("AM")
                pm = _("PM")
                if time_show_text[0].startswith("a"):
                    time_show_text[0] = am
                elif time_show_text[0].startswith("p"):
                    time_show_text[0] = pm
        elif self.__tray_time_hour_type == TRAY_TIME_24_HOUR:
            time_show_text = time.strftime("%H %M", time.localtime()).split(" ")
        #
        return time_show_text

    def __update_time(self, timer):
        # modify interval.
        if self.__timer.Interval == 1:
            self.__timer.Interval = 1000
        # emit event.
        self.emit("send-time", self.get_time(), self.__tray_time_hour_type)
        

if __name__ == "__main__":
    import gtk
    def test_time_show_text(traytime, time_text, time_type):
        time_p = ""
        if int(time_type) == TRAY_TIME_12_HOUR:
            time_p = time_text[0]

        hour = time_text[0 + int(time_type)]
        min  = time_text[1 + int(time_type)]

        print "%s %s:%s" % (time_p, hour, min)

    tray_time = TrayTime()
    tray_time.connect("send-time", test_time_show_text)
    gtk.main()
