#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012 Deepin, Inc.
#               2012 Zhai Xiang
# 
# Author:     Zhai Xiang <zhaixiang@linuxdeepin.com>
# Maintainer: Zhai Xiang <zhaixiang@linuxdeepin.com>
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

from dtk.ui.init_skin import init_skin
from dtk.ui.utils import get_parent_dir
import os

app_theme = init_skin(
    "deepin-bluetooth-settings", 
    "1.0",
    "01",
    os.path.join(get_parent_dir(__file__, 2), "skin"),
    os.path.join(get_parent_dir(__file__, 2), "app_theme"),
    )

from dtk.ui.scrolled_window import ScrolledWindow
from dtk.ui.iconview import IconView
from dtk.ui.label import Label
from dtk.ui.entry import InputEntry
from dtk.ui.combo import ComboBox
from dtk.ui.button import ToggleButton
from dtk.ui.constant import DEFAULT_FONT_SIZE, ALIGN_START, ALIGN_END
import gobject
import gtk

class DeviceIconView(ScrolledWindow):
    def __init__(self, items=None):
        ScrolledWindow.__init__(self, 0, 0)

        self.device_iconview = IconView()
        self.device_iconview.draw_mask = self.draw_mask

        if items != None:
            self.device_iconview.add_items(items)

        self.device_scrolledwindow = ScrolledWindow()
        self.device_scrolledwindow.add_child(self.device_iconview)

        self.add_child(self.device_scrolledwindow)

    def draw_mask(self, cr, x, y, w, h):
        cr.set_source_rgb(1, 1, 1)
        cr.rectangle(x, y, w, h)
        cr.fill()

    def add_items(self, items, clear=False):
        if clear:
            self.device_iconview.clear()
        
        self.device_iconview.add_items(items)

gobject.type_register(DeviceIconView)

class DeviceItem(gobject.GObject):
    __gsignals__ = {                                                             
        "redraw-request" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),     
    }
    
    def __init__(self):
        gobject.GObject.__init__(self)

        self.pixbuf = None

        self.__const_padding_y = 10

    def render(self, cr, rect):
        # Draw select background.
        if self.is_button_press == True:
            draw_vlinear(cr, rect.x ,rect.y, rect.width, rect.height, 
                         ui_theme.get_shadow_color("listview_select").get_color_info())

        # Draw device icon.
        draw_pixbuf(cr, self.pixbuf, 
                    rect.x + self.icon_size / 2,
                    rect.y + (rect.height - self.icon_size) / 2,
                    )
        
        # Draw device name.
        draw_text(cr, 
                  self.name, 
                  rect.x,
                  rect.y + self.icon_size + self.__const_padding_y * 2,
                  rect.width, 
                  DEFAULT_FONT_SIZE, 
                  DEFAULT_FONT_SIZE, 
                  alignment=pango.ALIGN_CENTER)
        
    def emit_redraw_request(self):
        '''
        Emit `redraw-request` signal.
        
        This is IconView interface, you should implement it.
        '''
        self.emit("redraw-request")
        
    def get_width(self):
        '''
        Get item width.
        
        This is IconView interface, you should implement it.
        '''
        return self.icon_size * 2
        
    def get_height(self):
        '''
        Get item height.
        
        This is IconView interface, you should implement it.
        '''
        return self.icon_size + DEFAULT_FONT_SIZE + self.__const_padding_y * 3
        
    def icon_item_motion_notify(self, x, y):
        '''
        Handle `motion-notify-event` signal.
        
        This is IconView interface, you should implement it.
        '''
        self.hover_flag = True
        
        self.emit_redraw_request()
        
    def icon_item_lost_focus(self):
        '''
        Lost focus.
        
        This is IconView interface, you should implement it.
        '''
        self.hover_flag = False
        
        self.emit_redraw_request()
        
    def icon_item_highlight(self):
        '''
        Highlight item.
        
        This is IconView interface, you should implement it.
        '''
        self.highlight_flag = True

        self.emit_redraw_request()
        
    def icon_item_normal(self):
        '''
        Set item with normal status.
        
        This is IconView interface, you should implement it.
        '''
        self.highlight_flag = False
        self.is_button_press = False
        
        self.emit_redraw_request()
    
    def icon_item_button_press(self, x, y):
        '''
        Handle button-press event.
        
        This is IconView interface, you should implement it.
        '''
        self.is_button_press = True
    
    def icon_item_button_release(self, x, y):
        '''
        Handle button-release event.
        
        This is IconView interface, you should implement it.
        '''
        self.is_button_press = True
    
    def icon_item_single_click(self, x, y):
        '''
        Handle single click event.
        
        This is IconView interface, you should implement it.
        '''
        pass

    def icon_item_double_click(self, x, y):
        '''
        Handle double click event.
        '''
        pass
    
    def icon_item_release_resource(self):
        '''
        Release item resource.

        If you have pixbuf in item, you should release memory resource like below code:

        >>> del self.pixbuf
        >>> self.pixbuf = None

        This is IconView interface, you should implement it.
        
        @return: Return True if do release work, otherwise return False.
        
        When this function return True, IconView will call function gc.collect() to release object to release memory.
        '''
        del self.pixbuf
        self.pixbuf = None    
        
        # Return True to tell IconView call gc.collect() to release memory resource.
        return True

gobject.type_register(DeviceItem)

class BlueToothView(gtk.VBox):
    '''
    class docs
    '''
	
    def __init__(self):
        '''
        init docs
        '''
        gtk.VBox.__init__(self)

        self.box_spacing = 10

        self.timeout_items = [("10分钟", 1)]

        '''
        enable open
        '''
        self.enable_align = self.__setup_align(padding_top=30)
        self.enable_box = gtk.HBox(spacing=self.box_spacing)
        self.enable_open_label = self.__setup_label("蓝牙是否开启")
        self.enable_open_toggle = self.__setup_toggle()
        self.__widget_pack_start(self.enable_box, [self.enable_open_label, self.enable_open_toggle])
        self.enable_align.add(self.enable_box)
        '''
        display
        '''
        self.display_align = self.__setup_align()
        self.display_box = gtk.HBox(spacing=self.box_spacing)
        self.display_device_label = self.__setup_label("显示设备名称")
        self.display_device_entry = InputEntry("Sirtoozee PC")
        self.display_device_entry.set_size(150, 24)
        self.__widget_pack_start(self.display_box, [self.display_device_label, self.display_device_entry])
        self.display_align.add(self.display_box)
        '''
        enable searchable
        '''
        self.search_align = self.__setup_align()
        self.search_box = gtk.HBox(spacing=self.box_spacing)
        self.search_label = self.__setup_label("是否可被发现")
        self.search_toggle = self.__setup_toggle()
        self.__widget_pack_start(self.search_box, [self.search_label, self.search_toggle])
        self.search_align.add(self.search_box)
        '''
        device timeout
        '''
        self.timeout_align = self.__setup_align()
        self.timeout_box = gtk.HBox(spacing=self.box_spacing)
        self.timeout_label = self.__setup_label("可检测到设备的时间超时")
        self.timeout_combo = ComboBox(self.timeout_items, max_width = 150)
        self.__widget_pack_start(self.timeout_box, [self.timeout_label, self.timeout_combo])
        self.timeout_align.add(self.timeout_box)
        '''
        device iconview
        '''
        self.device_align = self.__setup_align(padding_top=40)
        self.device_iconview = DeviceIconView()
        self.device_iconview.set_size_request(400, 260)
        self.device_align.add(self.device_iconview)
        '''
        this->gtk.VBox pack_start
        '''
        self.__widget_pack_start(self, 
                                 [self.enable_align, 
                                  self.display_align, 
                                  self.search_align, 
                                  self.timeout_align, 
                                  self.device_align])
    
    def __combo_item_selected(self, widget, item_text=None, item_value=None, item_index=None, object=None):
        pass

    def __setup_label(self, text="", width=140, align=ALIGN_START):
        label = Label(text, None, DEFAULT_FONT_SIZE, align, width)
        return label

    def __setup_combo(self, items=[], width=120):
        combo = ComboBox(items, None, 0, width)
        return combo

    def __setup_toggle(self):
        toggle = ToggleButton(app_theme.get_pixbuf("inactive_normal.png"), 
            app_theme.get_pixbuf("active_normal.png"))
        return toggle

    def __setup_align(self, xalign=0.5, yalign=0.5, xscale=1.0, yscale=1.0, 
                      padding_top=10, padding_bottom=0, padding_left=20, padding_right=20):
        align = gtk.Alignment()
        align.set(xalign, yalign, xscale, yscale)
        align.set_padding(padding_top, padding_bottom, padding_left, padding_right)
        return align

    def __widget_pack_start(self, parent_widget, widgets=[], expand=False, fill=False):
        if parent_widget == None:
            return
        for item in widgets:
            parent_widget.pack_start(item, expand, fill)

gobject.type_register(BlueToothView)