#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2013 Deepin, Inc.
#               2013 Zhai Xiang
#
# Author:     Zhai Xiang <zhaixiang@linuxdeepin.com>
# Maintainer: Zhai Xiang <zhaixiang@linuxdeepin.com>
#             Wang Yaohua <mr.asianwang@gmail.com>
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

import sys
import os
from deepin_utils.file import get_parent_dir
sys.path.append(os.path.join(get_parent_dir(__file__, 4), "dss"))

from theme import app_theme
from dtk.ui.utils import cairo_disable_antialias, color_hex_to_cairo
from dtk.ui.draw import draw_text
from dtk.ui.box import ImageBox
from dtk.ui.label import Label
from dtk.ui.constant import ALIGN_START
from dtk.ui.button import ToggleButton
from dtk.ui.line import HSeparator
from dtk.ui.treeview import TreeItem, TreeView
from vtk.button import SelectButton
from deepin_utils.process import run_command
import gobject
import gtk
from nls import _
from my_bluetooth import MyBluetooth
from bluetooth_sender import BluetoothSender
from bt.device import AudioSink, Input
from helper import notify_message
from servicemanager import servicemanager
from permanent_settings import permanent_settings
from bt.utils import is_bluetooth_audio_type, is_bluetooth_file_type, is_bluetooth_input_type

class DeviceItem(TreeItem):
    ITEM_HEIGHT = 22
    NAME_WIDTH = 160

    def __init__(self, PluginPtr, adapter, device):
        TreeItem.__init__(self)
        self.PluginPtr = PluginPtr
        self.adapter = adapter
        self.device = device
        self.is_hover = False

    def hover(self, column, offset_x, offset_y):
        self.is_hover = True
        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def unhover(self, column, offset_x, offset_y):
        self.is_hover = False
        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def single_click(self, column, offset_x, offset_y):
        self.PluginPtr.hide_menu()

        action = self.__get_action_by_device_class()
        if action:
            action()
        else:
            run_command("deepin-system-settings bluetooth")

    def __get_action_by_device_class(self):
        def do_send_file():
            sender = BluetoothSender(self.adapter, self.device)
            sender.do_send_file()

        def do_connect_audio_sink():
            try:
                self.audio_sink_service = AudioSink(self.device.device_path)
                self.audio_sink_service.as_connect()
                if self.audio_sink_service.get_state() == "connected":
                    notify_message(_("Bluetooth Audio"),
                                   _("Successfully connected to the Bluetooth audio device."))
                else:
                    notify_message(_("Connection Failed"), _("An error occured when connecting to the device."))
                    self.emit_redraw_request()
            except Exception, e:
                print "Exception:", e

        def do_connect_input_service():
            try:
                self.input_service = Input(self.device.device_path)
                self.input_service.i_connect()
                if self.input_service.get_connected():
                    notify_message(_("Bluetooth Input Service"),
                                   _("Successfully connected to the Bluetooth input device."))
                else:
                    notify_message(_("Connection Failed"), _("An error occured when connecting to the device."))
                    self.emit_redraw_request()
            except Exception, e:
                print "Exception:", e

        if is_bluetooth_audio_type(self.device):
            return do_connect_audio_sink
        elif is_bluetooth_file_type(self.device):
            return do_send_file
        elif is_bluetooth_input_type(self.device):
            return do_connect_input_service
        else:
            return None

    def __render_name(self, cr, rect):
        name_width = 130

        cr.set_source_rgb(1, 1, 1)
        cr.rectangle(rect.x, rect.y, rect.width, rect.height)
        cr.fill()

        if self.is_hover:
            with cairo_disable_antialias(cr):
                cr.set_source_rgb(*color_hex_to_cairo("#EBF4FD"))
                cr.rectangle(rect.x, rect.y, name_width, rect.height)
                cr.fill()
                cr.set_source_rgb(*color_hex_to_cairo("#7DA2CE"))
                cr.set_line_width(1)
                cr.rectangle(rect.x + 1, rect.y + 1, name_width, rect.height - 1)
                cr.stroke()

        draw_text(cr,
                  self.device.get_name(),
                  rect.x + 5,
                  rect.y,
                  name_width - 6,
                  rect.height)

    def get_height(self):
        return self.ITEM_HEIGHT

    def get_column_widths(self):
        return [self.NAME_WIDTH]

    def get_column_renders(self):
        return [self.__render_name]

gobject.type_register(DeviceItem)

class TrayBluetoothPlugin(object):
    def __init__(self):
        self.width = DeviceItem.NAME_WIDTH
        self.ori_height = 93
        self.height = self.ori_height
        self.device_items = []
        self.__init_my_bluetooth_and_start_service()
        
        servicemanager.connect("service-start", self.__on_bluetooth_service_start)
        servicemanager.connect("service-stop", self.__on_bluetooth_service_stop)
        
    def __init_my_bluetooth_and_start_service(self):
        try:
            self.my_bluetooth = MyBluetooth(self.__on_adapter_removed,
                                            self.__on_default_adapter_changed)
            if self.my_bluetooth.adapter:
                self.my_bluetooth.adapter.connect("property-changed", self.__on_adapter_property_changed)
        except Exception, e:
            print e
        if self.my_bluetooth.adapter:
            self.__start_service()
        
    def __on_bluetooth_service_start(self, gobj, path):
        print "service_start"
        self.tray_icon.set_visible(True)
        self.__init_my_bluetooth_and_start_service()
        
    def __on_bluetooth_service_stop(self, gobj, path):
        self.tray_icon.set_visible(False)
        
    def __on_adapter_property_changed(self, gobj, key, value):
        if key == "Powered":
            print self.my_bluetooth.adapter.get_powered()
            theme = "enable" if self.my_bluetooth.adapter.get_powered() else "enable_disconnect" 
            self.tray_icon.set_icon_theme(theme)
        
    def __on_adapter_removed(self):
        print "adapter removed"
        self.tray_icon.set_visible(False)
        if hasattr(self, "service_process"):
            try:
                os.kill(self.service_process.pid, 9)
                os.kill(self.service_process.pid + 1, 9)
            except Exception, e:
                print "DEBUG ", e
        
    def __on_default_adapter_changed(self):
        print "adapter changed"
        self.tray_icon.set_visible(True)
        
        if not self.my_bluetooth.adapter:
            self.__init_my_bluetooth_and_start_service()
        
    def __start_service(self):
        import subprocess
        
        if hasattr(self, "service_process"):
            try:
                os.kill(self.service_process.pid, 9)
                os.kill(self.service_process.pid + 1, 9)
            except Exception, e:
                print "DEBUG ", e
        self.service_process = subprocess.Popen("python %s/tray_bluetooth_service.py" % os.path.dirname(__file__), 
                                                stderr=subprocess.STDOUT, shell=True)

    def init_values(self, this_list):
        self.this = this_list[0]
        self.tray_icon = this_list[1]
        self.tray_icon.set_icon_theme("enable")

        if self.my_bluetooth.adapter:
        #     if not self.my_bluetooth.adapter.get_powered():
        #         self.tray_icon.set_no_show_all(True)
            self.my_bluetooth.adapter.set_powered(permanent_settings.get_powered())
            powered = self.my_bluetooth.adapter.get_powered()
            theme = "enable" if powered else "enable_disconnect"
            self.tray_icon.set_icon_theme(theme)
        else:
            self.tray_icon.set_no_show_all(True)

    def id(self):
        return "deepin-bluetooth-plugin-hailongqiu"

    def run(self):
        return True

    def insert(self):
        pass

    def __adapter_toggled(self, widget):
        if self.my_bluetooth.adapter == None:
            return

        self.this.hide_menu()
        self.my_bluetooth.adapter.set_powered(widget.get_active())
        if widget.get_active():
            self.tray_icon.set_icon_theme("enable")
            permanent_settings.set_powered(True)
        else:
            self.tray_icon.set_icon_theme("enable_disconnect")
            permanent_settings.set_powered(False)
        self.tray_icon.emit("popup-menu-event", TrayBluetoothPlugin.__class__) # Hacked by hualet :)
            
    def __bluetooth_selected(self, widget):
        self.this.hide_menu()
        run_command("deepin-system-settings bluetooth")

    def __get_devices(self):
        if self.my_bluetooth.adapter.get_powered():
            devices = self.my_bluetooth.get_devices()
            device_count = len(filter(lambda x : x.get_paired(), devices))

            self.device_items = []
            for d in devices:
                if d.get_paired():
                    self.device_items.append(DeviceItem(self, self.my_bluetooth.adapter, d))
        else:
            device_count = 0
            self.device_items = []

        self.height = self.ori_height
        if device_count:
            self.height += device_count * DeviceItem.ITEM_HEIGHT

    def plugin_widget(self):
        self.__get_devices()
        plugin_box = gtk.VBox()
        adapter_box = gtk.HBox(spacing = 5)
        adapter_image = ImageBox(app_theme.get_pixbuf("bluetooth/enable_open.png"))
        adapter_label = self.__setup_label(_("Adapter"))
        adapter_toggle = self.__setup_toggle()
        if self.my_bluetooth.adapter:
            adapter_toggle.set_active(self.my_bluetooth.adapter.get_powered())
            if self.my_bluetooth.adapter.get_powered():
                self.tray_icon.set_icon_theme("enable")
            else:
                self.tray_icon.set_icon_theme("enable_disconnect")
        adapter_toggle.connect("toggled", self.__adapter_toggled)
        separator_align = self.__setup_align(padding_bottom = 0)
        separator = self.__setup_separator()
        separator_align.add(separator)
        '''
        devices treeview
        '''
        device_treeview = TreeView()
        device_separator_align = self.__setup_align()
        device_separator = self.__setup_separator()
        device_separator_align.add(device_separator)
        device_count = len(self.device_items)
        if device_count:
            device_treeview.delete_all_items()
            device_treeview.add_items(self.device_items)
            device_treeview.set_size_request(self.width, device_count * DeviceItem.ITEM_HEIGHT)
        else:
            device_treeview.set_child_visible(False)
            device_separator_align.set_size_request(-1, 0)
            device_separator_align.set_child_visible(False)
        '''
        select button
        '''
        select_button_align = self.__setup_align()
        select_button = SelectButton(_("Advanced options..."),
                                     font_size = 10,
                                     ali_padding = 5)
        select_button.set_size_request(self.width, 25)
        select_button.connect("clicked", self.__bluetooth_selected) # I don't know why, but replacing "button-press-event" with 
        select_button_align.add(select_button)                      # clicked really works...

        adapter_box.pack_start(adapter_image, False, False)
        adapter_box.pack_start(adapter_label, False, False)
        adapter_box.pack_start(adapter_toggle, False, False)

        plugin_box.pack_start(adapter_box, False, False)
        plugin_box.pack_start(separator_align, False, False)
        plugin_box.pack_start(device_treeview, False, False)
        plugin_box.pack_start(device_separator_align, False, False)
        plugin_box.pack_start(select_button_align, False, False)

        return plugin_box
    
    def show_menu(self):
        self.this.set_size_request(self.width, self.height)

    def hide_menu(self):
        pass

    def __setup_align(self,
                      xalign=0,
                      yalign=0,
                      xscale=0,
                      yscale=0,
                      padding_top=5,
                      padding_bottom=0,
                      padding_left=0,
                      padding_right=0):
        align = gtk.Alignment()
        align.set(xalign, yalign, xscale, yscale)
        align.set_padding(padding_top, padding_bottom, padding_left, padding_right)
        return align

    def __setup_label(self, text="", width=50, align=ALIGN_START):
        return Label(text, None, 9, align, width, False, False, False)

    def __setup_toggle(self):
        toggle_button = ToggleButton(app_theme.get_pixbuf("toggle_button/inactive_normal.png"),
                                     app_theme.get_pixbuf("toggle_button/active_normal.png"),
                                     inactive_disable_dpixbuf = app_theme.get_pixbuf("toggle_button/inactive_normal.png"))
        toggle_button.set_active(self.my_bluetooth.adapter.get_powered())
        return toggle_button

    def __setup_separator(self):
        hseparator = HSeparator(app_theme.get_shadow_color("hSeparator").get_color_info(), 0, 0)
        hseparator.set_size_request(100, 3)
        return hseparator

def return_insert():
    pass

def return_id():
    return "bluetooth"

def return_plugin():
    return TrayBluetoothPlugin
