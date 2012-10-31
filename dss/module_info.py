#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Wang Yong
# 
# Author:     Wang Yong <lazycat.manatee@gmail.com>
# Maintainer: Wang Yong <lazycat.manatee@gmail.com>
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

from dtk.ui.config import Config
from dtk.ui.utils import get_parent_dir
import gtk
import os

MODULE_DIR = os.path.join(get_parent_dir(__file__, 2), "modules")        
FIRST_MODULE_NAMES = ["screen", "sound", "individuation", "date_time", "power"]
SECOND_MODULE_NAMES = ["keyboard", "mouse", "touchpad", "printer", "network", "bluetooth", "driver"]
THIRD_MODULE_NAMES = ["account", "auxiliary", "application_associate", "system_information"]

class ModuleInfo(object):
    '''
    class docs
    '''
	
    def __init__(self, module_path):
        '''
        init docs
        '''
        self.path = module_path
        self.config = Config(os.path.join(self.path, "config.ini"))
        self.config.load()
        self.id = self.config.get("main", "id")
        self.name = self.config.get("name", "zh_CN")
        self.icon_pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join(self.path, self.config.get("main", "icon")))
        self.menu_icon_pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join(self.path, self.config.get("main", "menu_icon")))
        
def get_module_infos():
    all_module_names = filter(lambda module_name: os.path.isdir(os.path.join(MODULE_DIR, module_name)), os.listdir(MODULE_DIR))        
    extend_module_names = list(set(all_module_names) - set(FIRST_MODULE_NAMES) - set(SECOND_MODULE_NAMES) - set(THIRD_MODULE_NAMES))
    
    return map(lambda names: 
               map(lambda name: ModuleInfo(os.path.join(MODULE_DIR, name)), names), 
                   [FIRST_MODULE_NAMES, SECOND_MODULE_NAMES, THIRD_MODULE_NAMES, extend_module_names])