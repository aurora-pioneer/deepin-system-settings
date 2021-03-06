#!/usr/bin/env python
#-*- coding:utf-8 -*-
# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Zeng Zhi
# 
# Author:     Zeng Zhi <zengzhilg@gmail.com>
# Maintainer: Zeng Zhi <zengzhilg@gmail.com>
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
from theme import app_theme
from dtk.ui.theme import ui_theme
from dtk.ui.treeview import TreeItem, TreeView
from dtk.ui.draw import draw_vlinear, draw_pixbuf, draw_text
from dtk.ui.utils import get_content_size, cairo_disable_antialias, color_hex_to_cairo, cairo_state
from deepin_utils.file import get_parent_dir
from dtk.ui.constant import DEFAULT_FONT_SIZE
from dtk.ui.entry import EntryBuffer
#from nm_modules import cache
from shared_methods import net_manager
from widgets import AskPasswordDialog
from nmlib.nm_remote_connection import NMRemoteConnection

from nm_modules import nm_module

import threading
import gtk
import pango
from style import string_markup

import sys,os
sys.path.append(os.path.join(get_parent_dir(__file__, 4), "dss"))
from constant import *
from nls import _
from math import radians
from helper import Dispatcher, event_manager

import threading as td
import time
from dss_log import log

bg_hover_color="#ebf4fd"
bg_normal_color = "#f6f6f6"
border_hover_color="#7da2ce"
border_normal_color = "#d2d2d2"

class GenItems(TreeItem):
    H_PADDING = 10
    V_PADDING = 5
    CHECK_WIDTH = IMG_WIDTH + 20
    JUMP_WIDTH = IMG_WIDTH + 10

    NETWORK_DISCONNECT = 0
    NETWORK_LOADING = 1
    NETWORK_CONNECTED = 2

    def __init__(self, jumpto_cb=None, is_last= False):
        TreeItem.__init__(self)

        self.network_state = 0
        if jumpto_cb:
            self.jumpto_cb = jumpto_cb

        self.loading_pixbuf = app_theme.get_pixbuf("network/loading.png")
        self.check_pixbuf = app_theme.get_pixbuf("network/check_box-2.png")
        self.jumpto_pixbuf = app_theme.get_pixbuf("network/jump_to.png")
        self.check_hover_pixbuf = app_theme.get_pixbuf("network/check_box-4.png")
        self.check_disable = app_theme.get_pixbuf("network/check_box-5.png")

        self.border_color = border_normal_color
        self.bg_color = bg_normal_color
        self.is_last = is_last
        self.is_hover = False
        self.hover_column = -1
        self.can_disable = False
        
    def render_check(self, cr, rect):
        self.render_background(cr,rect)

        if self.is_hover and self.network_state ==self.NETWORK_DISCONNECT:
            draw_pixbuf(cr, self.check_hover_pixbuf.get_pixbuf(), rect.x + self.H_PADDING, rect.y + (rect.height - IMG_WIDTH)/2)
        elif self.is_hover:
            if self.hover_column == 0 and self.can_disable:
                draw_pixbuf(cr, self.check_disable.get_pixbuf(), rect.x + self.H_PADDING, rect.y + (rect.height - IMG_WIDTH)/2)
            else:
                if self.network_state == self.NETWORK_LOADING:
                    self.draw_loading(cr, rect)
                elif self.network_state == self.NETWORK_CONNECTED:
                    draw_pixbuf(cr, self.check_pixbuf.get_pixbuf(), rect.x + self.H_PADDING, rect.y + (rect.height - IMG_WIDTH)/2)
        else:
            if self.network_state == self.NETWORK_LOADING:
                self.draw_loading(cr, rect)
            elif self.network_state == self.NETWORK_CONNECTED:
                draw_pixbuf(cr, self.check_pixbuf.get_pixbuf(), rect.x + self.H_PADDING, rect.y + (rect.height - IMG_WIDTH)/2)

        #draw outline
        with cairo_disable_antialias(cr):
            cr.set_source_rgb(*color_hex_to_cairo(self.border_color))
            cr.set_line_width(1)
            if self.is_last:
                cr.rectangle(rect.x, rect.y + rect.height -1, rect.width, 1)
            cr.rectangle(rect.x, rect.y, rect.width, 1)
            cr.rectangle(rect.x, rect.y, 1, rect.height)
            cr.fill()

    def render_jumpto(self, cr, rect):
        self.render_background(cr, rect)
        draw_pixbuf(cr, self.jumpto_pixbuf.get_pixbuf(), rect.x , rect.y + (rect.height - IMG_WIDTH)/2)
        with cairo_disable_antialias(cr):
            cr.set_source_rgb(*color_hex_to_cairo(self.border_color))
            cr.set_line_width(1)
            if self.is_last:
                cr.rectangle(rect.x, rect.y + rect.height -1, rect.width, 1)
            cr.rectangle(rect.x, rect.y, rect.width, 1)
            cr.rectangle(rect.x + rect.width -1, rect.y, 1, rect.height)
            cr.fill()

    def render_background(self, cr, rect):
        x, y, w, h = rect
        cr.set_source_rgb(*color_hex_to_cairo(self.bg_color))
        cr.rectangle(x, y, w, h)
        cr.fill()

    def render_blank(self, cr, rect):
        self.render_background(cr, rect)
        with cairo_disable_antialias(cr):
            cr.set_source_rgb(*color_hex_to_cairo(self.border_color))
            cr.set_line_width(1)
            if self.is_last:
                cr.rectangle(rect.x, rect.y + rect.height -1, rect.width, 1)
            cr.rectangle(rect.x, rect.y, rect.width, 1)
            cr.fill()

    def hover(self, column, offset_x, offset_y):
        self.is_hover = True
        self.bg_color = bg_hover_color
        self.hover_column = column

        self.redraw()

    def unhover(self, column, offset_x, offset_y):
        self.is_hover = False
        self.hover_column = -1
        self.bg_color = bg_normal_color
        self.redraw()

    def redraw(self):
        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def set_net_state(self, state):
        self.network_state = state
        if state == self.NETWORK_LOADING:
            LoadingThread(self).start()
        else:
            self.redraw()

    def get_net_state(self):
        return self.network_state
    
    def refresh_loading(self, position):
        self.position = position
        self.redraw()

    def draw_loading(self, cr, rect):
        with cairo_state(cr):
            cr.translate(rect.x + 18 , rect.y + 15)
            cr.rotate(radians(self.position))
            cr.translate(-18, -15)
            draw_pixbuf(cr, self.loading_pixbuf.get_pixbuf(), 10 , 7)

    def get_height(self):
        return CONTAINNER_HEIGHT
    
    def single_click(self, column, x, y):
        if self.jumpto_cb:
            columns = len(self.get_column_widths()) - 1
            if column == columns:
                self.jumpto_cb()
            else:
                self.click_cb()
        self.redraw()

    def click_cb(self):
        pass

    def force_stop_loading(self):
        self.network_state = 0


class LoadingThread(td.Thread):
    def __init__(self, widget):
        td.Thread.__init__(self)
        self.setDaemon(True)
        self.widget = widget
    
    def run(self):
        position = 0
        while self.widget.get_net_state() == 1 and time:
            self.widget.refresh_loading(position)
            time.sleep(0.1)
            position += 60

class WiredItem(GenItems):
    def __init__(self, device, font_size=DEFAULT_FONT_SIZE):
        GenItems.__init__(self)
        self.device = device
        self.essid = self.device.get_device_desc()
        self.font_size = font_size
        self.can_disable = True

        self.jumpto_icon = app_theme.get_pixbuf("network/jump_to.png")

    def render_device(self, cr, rect):
        self.render_background(cr, rect)
        (text_width, text_height) = get_content_size(self.essid)
        draw_text(cr, self.essid, rect.x, rect.y, rect.width, rect.height,
                alignment = pango.ALIGN_LEFT)
        with cairo_disable_antialias(cr):
            cr.set_source_rgb(*color_hex_to_cairo(self.border_color))
            cr.set_line_width(1)
            if self.is_last:
                cr.rectangle(rect.x, rect.y + rect.height -1, rect.width, 1)
            cr.rectangle(rect.x, rect.y, rect.width, 1)
            cr.fill()

    def get_column_widths(self):
        return [IMG_WIDTH + 20, -1, IMG_WIDTH + 10]

    def get_column_renders(self):
        return [self.render_check, self.render_device, self.render_jumpto]
    
    def single_click(self, column, x, y):
        if column == 0 and self.network_state > 0:
            log.debug(self.device)
            net_manager.disactive_wired_device([self.device])
            #self.device.nm_device_disconnect()
        if column == 2:
            from lan_config import WiredSetting
            Dispatcher.to_setting_page(WiredSetting(self.device, net_manager.get_primary_wire(self.device)), False)
        else:
            device_ethernet = nm_module.cache.get_spec_object(self.device.object_path)
            device_ethernet.auto_connect()
        self.redraw()

class WirelessItem(GenItems):
    def  __init__(self,
                  ap,
                  device,
                  font_size = DEFAULT_FONT_SIZE):
        GenItems.__init__(self)
        self.ap = ap
        self.device = device
        self.ssid = self.ap.get_ssid()
        self.strength = ap.get_strength()
        self.security = int(ap.get_flags())
        self.font_size = font_size
        self.is_last = False

        '''
        Pixbufs
        '''
        self.lock_pixbuf =  app_theme.get_pixbuf("network/lock.png")
        self.strength_0 = app_theme.get_pixbuf("network/Wifi_0.png")
        self.strength_1 = app_theme.get_pixbuf("network/Wifi_1.png")
        self.strength_2 = app_theme.get_pixbuf("network/Wifi_2.png")
        self.strength_3 = app_theme.get_pixbuf("network/Wifi_3.png")

    def render_ssid(self, cr, rect):
        self.render_background(cr,rect)
        ssid = self.ssid.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        (text_width, text_height) = get_content_size(ssid)
        draw_text(cr, ssid, rect.x, rect.y, rect.width, rect.height,
                alignment = pango.ALIGN_LEFT)

        with cairo_disable_antialias(cr):
            cr.set_source_rgb(*color_hex_to_cairo(self.border_color))
            cr.set_line_width(1)
            if self.is_last:
                cr.rectangle(rect.x, rect.y + rect.height -1, rect.width, 1)
            cr.rectangle(rect.x, rect.y, rect.width, 1)
            cr.fill()

    def render_signal(self, cr, rect):
        self.render_background(cr,rect)

        if self.security:
            lock_icon = self.lock_pixbuf
            draw_pixbuf(cr, lock_icon.get_pixbuf(), rect.x , rect.y + (rect.height - IMG_WIDTH)/2)

        if self.strength > 80:
            signal_icon = self.strength_3
        elif self.strength > 60:
            signal_icon = self.strength_2
        elif self.strength > 30:
            signal_icon = self.strength_1
        else:
            signal_icon = self.strength_0
        
        draw_pixbuf(cr, signal_icon.get_pixbuf(), rect.x + IMG_WIDTH + 5, rect.y + (rect.height - IMG_WIDTH)/2)
        with cairo_disable_antialias(cr):
            cr.set_source_rgb(*color_hex_to_cairo(self.border_color))
            cr.set_line_width(1)
            if self.is_last:
                cr.rectangle(rect.x, rect.y + rect.height -1, rect.width, 1)
            cr.rectangle(rect.x, rect.y, rect.width, 1)
            cr.fill()

    def get_column_widths(self):
        return [IMG_WIDTH + 20, -1, IMG_WIDTH*2 + 5 + 20, IMG_WIDTH + 10]

    def get_column_renders(self):
        return [self.render_check, self.render_ssid, self.render_signal, self.render_jumpto]

    def single_click(self, column, x, y):
        if column ==3:
            from wlan_config import WirelessSetting
            Dispatcher.to_setting_page(WirelessSetting(self.ap, net_manager.get_primary_wireless(self.ap)), False)
        elif column < 2:
            if self.network_state != 2:
                self.connect_by_ssid(self.ssid, self.ap)

    def connect_by_ssid(self, ssid, ap):
        connection =  net_manager.connect_wireless_by_ssid(ssid, self.device)
        #print connection, "DEBUG connect by ssid"
        self.ap = ap
        if connection and not isinstance(connection, NMRemoteConnection):
            security = net_manager.get_sec_ap(self.ap)
            if security:
                print "connect by ssid", security
                self.toggle_dialog(connection, security)
            else:
                connection = nm_module.nm_remote_settings.new_connection_finish(connection.settings_dict, 'lan')
                #ap = filter(lambda ap:ap.get_ssid() == ssid, self.ap_list)
                nm_module.nmclient.activate_connection_async(connection.object_path,
                                          self.device.object_path,
                                           ap.object_path)
        elif connection == None:
            pass

    def toggle_dialog(self, connection, security=None):
        ssid = connection.get_setting("802-11-wireless").ssid
        if ssid != None:
            AskPasswordDialog(connection,
                              ssid,
                              key_mgmt=security,
                              cancel_callback=self.cancel_ask_pwd,
                              confirm_callback=self.pwd_changed).show_all()

    def cancel_ask_pwd(self):
        pass

    def pwd_changed(self, pwd, connection):
        print connection, "in pwd changed"
        if not isinstance(connection, NMRemoteConnection):
            connection = nm_module.nm_remote_settings.new_connection_finish(connection.settings_dict, 'lan')
        
        if hasattr(self, "connection"):
            if self.connection:
                net_manager.save_and_connect(pwd, connection, self.ap)
            else:
                net_manager.save_and_connect(pwd, connection, None)
        else:
            net_manager.save_and_connect(pwd, connection, None)

class InfoItem(GenItems):
    def __init__(self, content, jumpto= None, is_last= False):
        GenItems.__init__(self, jumpto, is_last)
        self.content = content

    def render_content(self, cr, rect):
        self.render_background(cr, rect)
        if self.network_state == self.NETWORK_CONNECTED:
            text_color = "#3da1f7"
        else:
            text_color = "#000000"
        (text_width, text_height) = get_content_size(self.content)
        draw_text(cr, self.content, rect.x, rect.y, rect.width, rect.height,
                alignment = pango.ALIGN_LEFT, text_color = text_color)

        with cairo_disable_antialias(cr):
            cr.set_source_rgb(*color_hex_to_cairo(self.border_color))
            cr.set_line_width(1)
            if self.is_last:
                cr.rectangle(rect.x, rect.y + rect.height -1, rect.width, 1)
            cr.rectangle(rect.x, rect.y, rect.width, 1)
            cr.fill()

    def get_column_renders(self):
        return [self.render_check, self.render_content, self.render_blank
        ,self.render_jumpto]

    def get_column_widths(self):
        return [self.CHECK_WIDTH, -1, 1, self.JUMP_WIDTH]

class HidenItem(GenItems):
    def __init__(self, connection, jumpto=None, font_size=DEFAULT_FONT_SIZE):
        GenItems.__init__(self, jumpto)
        
        self.connection = connection
        self.ap = None
        self.id = self.connection.get_setting("802-11-wireless").ssid
        print self.id

    def render_id(self, cr, rect):
        self.render_background(cr, rect)
        id  = string_markup(self.id)
        (text_width, text_height) = get_content_size(id)
        draw_text(cr, id, rect.x, rect.y, rect.width, rect.height,
                alignment = pango.ALIGN_LEFT)

        with cairo_disable_antialias(cr):
            cr.set_source_rgb(*color_hex_to_cairo(self.border_color))
            cr.set_line_width(1)
            if self.is_last:
                cr.rectangle(rect.x, rect.y + rect.height -1, rect.width, 1)
            cr.rectangle(rect.x, rect.y, rect.width, 1)
            cr.fill()

    def get_column_widths(self):
        return [self.CHECK_WIDTH, -1, 1, self.JUMP_WIDTH]
    
    def get_column_renders(self):
        return [self.render_check, self.render_id, self.render_blank, self.render_jumpto]
    
    def jumpto_cb(self):
        from wlan_config import HiddenSetting
        Dispatcher.to_setting_page(HiddenSetting(self.connection), False)

    def click_cb(self):
        wireless_device = net_manager.device_manager.get_wireless_devices()[0]
        nm_module.nmclient.activate_connection_async(self.connection.object_path,
                                   wireless_device.object_path,
                                   "/")


class HotspotItem(TreeItem):

    def __init__(self, font_size=DEFAULT_FONT_SIZE):
        TreeItem.__init__(self)
        self.entry = None
        self.height = self.get_height()
        self.ssid_buffer = EntryBuffer("")
        self.ssid_buffer.set_property('cursor-visible', False)
        self.password_buffer = EntryBuffer("")
        self.password_buffer.set_property('cursor-visible', False)

        self.ssid_buffer.connect("changed", self.entry_buffer_changed)
        self.ssid_buffer.connect("insert-pos-changed", self.entry_buffer_changed)
        self.ssid_buffer.connect("selection-pos-changed", self.entry_buffer_changed)
        self.password_buffer.connect("changed", self.entry_buffer_changed)
        self.password_buffer.connect("insert-pos-changed", self.entry_buffer_changed)
        self.password_buffer.connect("selection-pos-changed", self.entry_buffer_changed)

        self.ENTRY_COLUMN = [2, 4]
        self.entry_buffer = None
        self.is_active = False
        self.check_pixbuf = app_theme.get_pixbuf("network/check_box-2.png")
        self.jumpto_pixbuf = app_theme.get_pixbuf("network/jump_to.png")
        self.border_color = border_normal_color
        self.bg_color = bg_normal_color

    def entry_buffer_changed(self, bf):
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
    def render_check(self, cr, rect):
        render_background(cr, rect)

        gap = (rect.height - IMG_WIDTH)/2
        
        if self.is_active:
            draw_pixbuf(cr, self.check_pixbuf.get_pixbuf(), rect.x + 10, rect.y + gap)   

    def render_ssid(self, cr ,rect):
        render_background(cr, rect)
        
        draw_text(cr, _("SSID:"), rect.x, rect.y, rect.width, rect.height,
                alignment = pango.ALIGN_LEFT)

    def render_ssid_entry(self, cr, rect):
        render_background(cr, rect)
        with cairo_disable_antialias(cr):
            cr.set_source_rgb(0, 0, 0)
            cr.set_line_width(1)
            cr.rectangle(rect.x, rect.y + 4, rect.width, 22)
            cr.stroke()
        if self.is_select:
            text_color = "#ffffff"
        else:
            text_color = "#000000"
            self.ssid_buffer.move_to_start()

        self.ssid_buffer.set_text_color(text_color)
        height = self.ssid_buffer.get_pixel_size()[1]
        offset = (self.height - height)/2
        if offset < 0 :
            offset = 0
        rect.y += offset  
        if self.entry and self.entry.allocation.width == self.get_column_widths()[1]-4:
            self.entry.calculate()
            rect.x += 2
            rect.width -= 4
            self.ssid_buffer.set_text_color("#000000")
            self.ssid_buffer.render(cr, rect, self.entry.im, self.entry.offset_x)
        else:
            self.ssid_buffer.render(cr, rect)

    def render_pwd(self, cr, rect):
        render_background(cr, rect)

        draw_text(cr, _("Password:"), rect.x, rect.y, rect.width, rect.height,
                alignment = pango.ALIGN_LEFT)

    def render_pwd_entry(self, cr, rect):
        render_background(cr, rect)
        with cairo_disable_antialias(cr):
            cr.set_source_rgb(0, 0, 0)
            cr.set_line_width(1)
            cr.rectangle(rect.x, rect.y + 4, rect.width, 22)
            cr.stroke()
        if self.is_select:
            text_color = "#ffffff"
        else:
            text_color = "#000000"
            self.password_buffer.move_to_start()

        self.password_buffer.set_text_color(text_color)
        height = self.password_buffer.get_pixel_size()[1]
        offset = (self.height - height)/2
        if offset < 0 :
            offset = 0
        rect.y += offset  
        if self.entry and self.entry.allocation.width == self.get_column_widths()[1]-4:
            self.entry.calculate()
            rect.x += 2
            rect.width -= 4
            self.password_buffer.set_text_color("#000000")
            self.password_buffer.render(cr, rect, self.entry.im, self.entry.offset_x)
        else:
            self.password_buffer.render(cr, rect)

    def render_active(self, cr, rect):
        with cairo_disable_antialias(cr):
            cr.set_source_rgb(0, 0, 0)
            cr.set_line_width(1)
            cr.rectangle(rect.x, rect.y + 4, rect.width, 22)
            cr.stroke()

        draw_text(cr, _("active"), rect.x, rect.y, rect.width, rect.height,
                alignment = pango.ALIGN_LEFT)
    
    def render_jump(self, cr, rect):
        render_background(cr, rect)
        gap = (rect.height - IMG_WIDTH)/2
        draw_pixbuf(cr, self.jumpto_pixbuf.get_pixbuf(), rect.x + 10, rect.y + gap)   

    def set_connection_name(self, sdf):
        pass

    def expand(self):
        pass
    
    def unexpand(self):
        pass
    
    def get_buffer(self, column):
        buffers = [0, 0, self.ssid_buffer, 0, self.password_buffer, 0]
        self.entry_buffer = buffers[column]
        return self.entry_buffer
    
    def get_height(self):
        return CONTAINNER_HEIGHT
    
    def get_column_widths(self):
        return [20, 30, 200, 20, 200, 30, 20]

    def get_column_renders(self):
        return [self.render_check, self.render_ssid, self.render_ssid_entry,
                self.render_pwd, self.render_pwd_entry, self.render_active,
                self.render_jump]
    
    def unselect(self):
        pass
    
    def select(self):
        pass
    
    def hover(self, column, offset_x, offset_y):
        self.is_hover = True
        self.border_color = border_hover_color

    def unhover(self, column, offset_x, offset_y):
        #print column, offset_x, offset_y
        self.is_hover = False
        self.border_color = border_normal_color
    
    def motion_notify(self, column, offset_x, offset_y):
        pass
    
    def button_press(self, column, offset_x, offset_y):
        pass        
    
    def button_release(self, column, offset_x, offset_y):
        pass        
    
    def single_click(self, column, offset_x, offset_y):
        pass        

    def double_click(self, column, offset_x, offset_y):
        pass        
    
    def draw_drag_line(self, drag_line, drag_line_at_bottom=False):
        pass

    def highlight(self):
        pass
    
    def unhighlight(self):
        pass
    
    def release_resource(self):
        return False
    
    def redraw(self):
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
         
class DSLItem(GenItems):

    def __init__(self, connection, jumpto=None, font_size=DEFAULT_FONT_SIZE):
        GenItems.__init__(self, jumpto)
        
        self.connection = connection
        self.id = self.connection.get_setting("connection").id

        event_manager.add_callback("update-dsl-id", self.__on_update_id)

    def __on_update_id(self, name, obj, data):
        if obj != self.connection:
            return

        self.id = data
        self.redraw()
    
    def render_id(self, cr, rect):
        self.render_background(cr, rect)
        (text_width, text_height) = get_content_size(self.id)
        draw_text(cr, self.id, rect.x, rect.y, rect.width, rect.height,
                alignment = pango.ALIGN_LEFT)

        with cairo_disable_antialias(cr):
            cr.set_source_rgb(*color_hex_to_cairo(self.border_color))
            cr.set_line_width(1)
            if self.is_last:
                cr.rectangle(rect.x, rect.y + rect.height -1, rect.width, 1)
            cr.rectangle(rect.x, rect.y, rect.width, 1)
            cr.fill()

    def get_column_widths(self):
        return [self.CHECK_WIDTH, -1, self.JUMP_WIDTH]
    
    def get_column_renders(self):
        return [self.render_check, self.render_id, self.render_jumpto]
    
    def jumpto_cb(self):
        from dsl_config import DSLSetting
        Dispatcher.to_setting_page(DSLSetting(self.connection), True)

    def click_cb(self):
        event_manager.emit('dsl-connection-start', self.connection)
        if net_manager.wired_device:
            device_path = net_manager.wired_device.object_path
            nm_module.nmclient.activate_connection_async(self.connection.object_path,
                                               device_path,
                                               "/")

class MobileItem(GenItems):

    def __init__(self, device, jumpto):
        GenItems.__init__(self)
        from mm.mmdevice import MMDevice
        self.device = MMDevice(device)
        manufacturer = self.device.get_manufacturer()
        model = self.device.get_model()
        self.info = model + " " + manufacturer

    def render_info(self, cr ,rect):
        self.render_background(cr, rect)
        (text_width, text_height) = get_content_size(self.info)
        draw_text(cr, self.info, rect.x, rect.y, rect.width, rect.height,
                alignment = pango.ALIGN_LEFT)
        with cairo_disable_antialias(cr):
            cr.set_source_rgb(*color_hex_to_cairo(self.border_color))
            cr.set_line_width(1)
            if self.is_last:
                cr.rectangle(rect.x, rect.y + rect.height -1, rect.width, 1)
            cr.rectangle(rect.x, rect.y, rect.width, 1)
            cr.fill()

    def get_column_widths(self):
        return [IMG_WIDTH + 20, -1, IMG_WIDTH + 10]

    def get_column_renders(self):
        return [self.render_check, self.render_info, self.render_jumpto]

    def jumpto_cb(self):
        from mobile_config import MobileSetting
        Dispatcher.to_setting_page(MobileSetting(), False)

    def click_cb(self):
        self.device.auto_connect()

class VPNItem(GenItems):                                                        
    def __init__(self, connection, jumpto=None, font_size=DEFAULT_FONT_SIZE):   
        GenItems.__init__(self, jumpto)                                         
                                                                                
        self.connection = connection                                            
        self.id = self.connection.get_setting("connection").id
        #self.click_cb()
                                                                                
        event_manager.add_callback("update-vpn-id", self.__on_update_id)            
                                                                                
    def __on_update_id(self, name, obj, data):                                  
        if obj != self.connection:
            return

        self.id = data                                                          
        self.redraw()                                                           
                                                                                
    def render_id(self, cr, rect):                                              
        self.render_background(cr, rect)                                        
        (text_width, text_height) = get_content_size(self.id)                   
        draw_text(cr, self.id, rect.x, rect.y, rect.width, rect.height,         
                alignment = pango.ALIGN_LEFT)                                   
                                                                                
        with cairo_disable_antialias(cr):                                       
            cr.set_source_rgb(*color_hex_to_cairo(self.border_color))           
            cr.set_line_width(1)                                                
            if self.is_last:                                                    
                cr.rectangle(rect.x, rect.y + rect.height -1, rect.width, 1)       
            cr.rectangle(rect.x, rect.y, rect.width, 1)                         
            cr.fill()

    def get_column_widths(self):                                                
        return [self.CHECK_WIDTH, -1, self.JUMP_WIDTH]                          
                                                                                
    def get_column_renders(self):                                               
        return [self.render_check, self.render_id, self.render_jumpto]

    def click_cb(self):
        self.set_net_state(1)
        monitor = Monitor(self.connection,
                          lambda:self.set_net_state(0),
                          lambda:self.set_net_state(2))
        monitor.start()

    def jumpto_cb(self):
        from vpn_config import VPNSetting
        Dispatcher.to_setting_page(VPNSetting(self.connection), True)

    #def vpn_active_cb(self, active):
        #vpn_connection = nm_module.cache.get_spec_object(active.object_path)
        #vpn_connection.connect("vpn-connected", lambda w: self.set_net_state(2))
        #vpn_connection.connect("vpn-disconnected", lambda w:self.set_net_state(0))
        #vpn_connection.connect("vpn-connecting", lambda w:self.set_net_state(1))
        
class Monitor(threading.Thread):
    def __init__(self, connection, stop_callback, active_callback):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.connection = connection
        self.stop_callback = stop_callback
        self.active_callback = active_callback
        from nmlib.nm_remote_settings import ThreadVPNSpec
        self.td = ThreadVPNSpec(connection, self.on_active_conn_create)
        self.td.start()

    def on_active_conn_create(self, active_conn):
        #pass
        net_manager.emit_vpn_start(active_conn)
         
    def run(self):
        while self.td.isAlive():
            time.sleep(1)

        else:
            if self.td.succeed:
                #self.active_callback()
                pass
            else:
                #Dispatcher.emit('vpn-force-stop')
                #self.stop_callback()
                pass
        
        '''
        from nmlib.nm_remote_settings import ThreadVPNSpec
        td = ThreadVPNSpec(self.connection, self.vpn_active_cb)
        td.start()
        if td.active:
            self.vpn_active_cb(self, td_active)
    
        active_connections = nm_module.nmclient.get_active_connections()
        if active_connections:
            device_path = active_connections[0].get_devices()[0].object_path
            specific_path = active_connections[0].object_path
            active_object = nm_module.nmclient.activate_connection(self.connection.object_path,
                                           device_path,
                                           specific_path)
            active_object.connect("vpn-state-changed", self.vpn_state_changed)
        else:
            print "no active connection available"
        '''
class VpnAutoMonitor(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.run_flag = True

    def on_active_conn_create(self, active_conn):
        #pass
        net_manager.emit_vpn_start(active_conn)
         
    def run(self):
        for active_conn in nm_module.nmclient.get_anti_vpn_active_connection():
            if self.run_flag:
                self.thread = active_conn.vpn_auto_connect(self.on_active_conn_create)
                if self.thread == True:
                    self.run_flag = False
                elif self.thread == False:
                    continue
                else:
                    while self.thread and self.thread.isAlive() and self.run_flag:
                        time.sleep(1)
                    else:
                        if self.thread and self.thread.succeed:
                            self.run_flag = False
                        else:
                            continue
    def stop(self):
        self.run_flag = False
        if hasattr(self, "thread"):
            self.thread.stop_run()
    
class GeneralItem(TreeItem):
    CHECK_LEFT_PADDING = 10
    CHECK_RIGHT_PADIING = 10
    JUMPTO_RIGHT_PADDING = 10
    VERTICAL_PADDING = 5
    NETWORK_DISCONNECT = 0
    NETWORK_LOADING = 1
    NETWORK_CONNECTED = 2

    def __init__(self,
                 name,
                 ap_list,
                 setting_page,
                 slide_to_setting_page_cb,
                 send_to_crumb,
                 check_state=2,
                 font_size=DEFAULT_FONT_SIZE):

        TreeItem.__init__(self)

        self.name = name
        self.ap_list = ap_list
        self.setting = setting_page
        self.slide_to_setting = slide_to_setting_page_cb
        self.send_to_crumb = send_to_crumb
        self.font_size = font_size
        self.check_width = self.get_check_width()
        self.essid_width = self.get_essid_width(self.name)
        self.jumpto_width = self.get_jumpto_width()
        self.network_state = check_state

        self.is_last = True
        self.position = 0

        '''
        Pixbufs
        '''
        self.border_color = border_normal_color
        self.bg_color = bg_normal_color
        self.loading_pixbuf = app_theme.get_pixbuf("network/loading.png")
        self.check_pixbuf = app_theme.get_pixbuf("network/check_box-2.png")
        self.jumpto_pixbuf = app_theme.get_pixbuf("network/jump_to.png")

    def render_check(self, cr, rect):
        render_background(cr, rect)

        if self.network_state == self.NETWORK_LOADING:
            self.draw_loading(cr, rect)
        elif self.network_state == self.NETWORK_CONNECTED:
            draw_pixbuf(cr, self.check_pixbuf.get_pixbuf(), rect.x + self.CHECK_LEFT_PADDING, rect.y + (rect.height - IMG_WIDTH)/2)

        #draw outline
        with cairo_disable_antialias(cr):
            cr.set_source_rgb(*color_hex_to_cairo(self.border_color))
            cr.set_line_width(1)
            if self.is_last:
                cr.rectangle(rect.x, rect.y + rect.height -1, rect.width, 1)
            cr.rectangle(rect.x, rect.y, rect.width, 1)
            cr.rectangle(rect.x, rect.y, 1, rect.height)
            cr.fill()
        #if self.network_state == 0:
            #check_icon = None
        #elif self.network_state == 1:
            #check_icon = self.loading_pixbuf
        #else:
            #check_icon = self.check_pixbuf
        
        #if check_icon:
            #draw_pixbuf(cr, check_icon.get_pixbuf(), rect.x + self.CHECK_LEFT_PADDING, rect.y + (rect.height - IMG_WIDTH)/2)
        #with cairo_disable_antialias(cr):
            #cr.set_source_rgb(*BORDER_COLOR)
            #cr.set_line_width(1)
            #if self.is_last:
                #cr.rectangle(rect.x, rect.y + rect.height -1, rect.width, 1)
            #cr.rectangle(rect.x, rect.y, rect.width, 1)
            #cr.rectangle(rect.x , rect.y, 1, rect.height)
            #cr.fill()

    def draw_loading(self, cr, rect):
        with cairo_state(cr):
            cr.translate(rect.x + 18 , rect.y + 15)
            cr.rotate(radians(60*self.position))
            cr.translate(-18, -15)
            draw_pixbuf(cr, self.loading_pixbuf.get_pixbuf(), 10 , 7)

    def render_name(self, cr, rect):
        render_background(cr, rect)
        #(text_width, text_height) = get_content_size(self.name)
        if self.is_select:
            text_color = None
        draw_text(cr, self.name, rect.x, rect.y, rect.width, rect.height,
                alignment = pango.ALIGN_LEFT)
        with cairo_disable_antialias(cr):
            cr.set_source_rgb(*color_hex_to_cairo(self.border_color))
            cr.set_line_width(1)
            if self.is_last:
                cr.rectangle(rect.x, rect.y + rect.height -1, rect.width, 1)
            cr.rectangle(rect.x, rect.y, rect.width, 1)
            cr.fill()

    def render_jumpto(self, cr, rect):

        render_background(cr, rect)
        if self.is_select:
            pass
        jumpto_icon = self.jumpto_pixbuf
        draw_pixbuf(cr, jumpto_icon.get_pixbuf(), rect.x , rect.y + (rect.height - IMG_WIDTH)/2)
        with cairo_disable_antialias(cr):
            cr.set_source_rgb(*color_hex_to_cairo(self.border_color))
            cr.set_line_width(1)
            if self.is_last:
                cr.rectangle(rect.x, rect.y + rect.height -1, rect.width, 1)
            cr.rectangle(rect.x, rect.y, rect.width, 1)
            cr.rectangle(rect.x + rect.width -1, rect.y, 1, rect.height)
            cr.fill()

    def render_blank(self, cr, rect):
        render_background(cr, rect)
        with cairo_disable_antialias(cr):
            cr.set_source_rgb(*color_hex_to_cairo(self.border_color))
            cr.set_line_width(1)
            if self.is_last:
                cr.rectangle(rect.x, rect.y + rect.height -1, rect.width, 1)
            cr.rectangle(rect.x, rect.y, rect.width, 1)
            cr.fill()


    def get_check_width(self):
        return IMG_WIDTH + self.CHECK_LEFT_PADDING + self.CHECK_RIGHT_PADIING
    def get_essid_width(self, essid):
        return get_content_size(essid)[0]
    
    def get_jumpto_width(self):
        return IMG_WIDTH + self.JUMPTO_RIGHT_PADDING

    def get_column_widths(self):
        return [self.check_width, -1,20, self.jumpto_width]

    def get_column_renders(self):
        return [self.render_check,
                self.render_name,
                self.render_blank,
                self.render_jumpto]

    def render_background(self, item, cr, rect):
        draw_vlinear(cr, rect.x ,rect.y, rect.width, rect.height,
                     ui_theme.get_shadow_color("listview_select").get_color_info())


    def get_height(self):
        return CONTAINNER_HEIGHT
        
    def unselect(self):
        self.is_select = False
        
    def hover(self, column, offset_x, offset_y):
        pass

    def unhover(self, column, offset_x, offset_y):
        #print column, offset_x, offset_y
        pass

    def single_click(self, column, x, y):
        if column == 3:
            self.setting.init("", init_connections=true)
            self.slide_to_setting()
            self.send_to_crumb()

        self.redraw()

    def redraw(self):
        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def set_net_state(self, state):
        if self.network_state == state:
            return
        self.network_state = state
        if state == self.NETWORK_LOADING:
            LoadingThread(self).start()

    def get_net_state(self):
        return self.network_state
    
    def refresh_loading(self, position):
        self.position = position
        self.redraw()

class DeviceToggleItem(GenItems):
    
    def  __init__(self,
                  devices,
                  index,
                  font_size = DEFAULT_FONT_SIZE):
        GenItems.__init__(self)
        self.devices = devices
        self.index = index
        self.device_name = devices[self.index].get_device_desc()

        self.wifi = app_theme.get_pixbuf("network/wifi_device.png")
        self.left = app_theme.get_pixbuf("network/left.png")
        self.left_hover = app_theme.get_pixbuf("network/left_hover.png")
        self.right_hover = app_theme.get_pixbuf("network/right_hover.png")
        self.right = app_theme.get_pixbuf("network/right.png")
        self.bg_color = "#ffffff"

        self.is_hover_left = False
        self.is_hover_right = False

    def render_icon(self, cr, rect):
        self.render_background(cr, rect)
        draw_pixbuf(cr, self.wifi.get_pixbuf(), rect.x + self.H_PADDING, rect.y + (rect.height - IMG_WIDTH)/2)
        with cairo_disable_antialias(cr):
            cr.set_source_rgb(*color_hex_to_cairo(self.border_color))
            cr.set_line_width(1)
            if self.is_last:
                cr.rectangle(rect.x, rect.y + rect.height -1, rect.width, 1)
            cr.rectangle(rect.x, rect.y, rect.width, 1)
            cr.rectangle(rect.x, rect.y, 1, rect.height)
            cr.fill()


    def render_left(self, cr, rect):
        self.render_background(cr, rect)
        if self.is_hover_left:
            icon = self.left_hover
        else:
            icon = self.left
        draw_pixbuf(cr, icon.get_pixbuf(), rect.x + IMG_WIDTH + 5, rect.y + (rect.height - IMG_WIDTH)/2)
        with cairo_disable_antialias(cr):
            cr.set_source_rgb(*color_hex_to_cairo(self.border_color))
            cr.set_line_width(1)
            if self.is_last:
                cr.rectangle(rect.x, rect.y + rect.height -1, rect.width, 1)
            cr.rectangle(rect.x, rect.y, rect.width, 1)
            cr.fill()

    def render_right(self, cr, rect):
        self.render_background(cr, rect)
        if self.is_hover_right:
            icon = self.right_hover
        else:
            icon = self.right
        draw_pixbuf(cr, icon.get_pixbuf(), rect.x , rect.y + (rect.height - IMG_WIDTH)/2)
        with cairo_disable_antialias(cr):
            cr.set_source_rgb(*color_hex_to_cairo(self.border_color))
            cr.set_line_width(1)
            if self.is_last:
                cr.rectangle(rect.x, rect.y + rect.height -1, rect.width, 1)
            cr.rectangle(rect.x, rect.y, rect.width, 1)
            cr.rectangle(rect.x + rect.width -1, rect.y, 1, rect.height)
            cr.fill()
    
    def render_device(self, cr, rect):
        self.render_background(cr, rect)
        (text_width, text_height) = get_content_size(self.device_name)
        draw_text(cr, self.device_name, rect.x, rect.y, rect.width, rect.height,
                alignment = pango.ALIGN_LEFT)

        with cairo_disable_antialias(cr):
            cr.set_source_rgb(*color_hex_to_cairo(self.border_color))
            cr.set_line_width(1)
            if self.is_last:
                cr.rectangle(rect.x, rect.y + rect.height -1, rect.width, 1)
            cr.rectangle(rect.x, rect.y, rect.width, 1)
            cr.fill()

    def get_column_widths(self):
        return [IMG_WIDTH + 20, -1, IMG_WIDTH*2 +5 + 20, IMG_WIDTH + 10]
    
    def get_column_renders(self):
        return [self.render_icon, self.render_device, self.render_left, self.render_right]

    def hover(self, column, offset_x, offset_y):
        pass

    def motion_notify(self, column, offset_x, offset_y):
        if column == 3:
            self.is_hover_right = True
            self.is_hover_left = False
        elif column == 2:
            self.is_hover_left = True
            self.is_hover_right = False

        self.redraw()

    def unhover(self, column, offset_x, offset_y):
        #if column == 3:
        self.is_hover_right = False
        self.is_hover_left = False
        self.redraw()

    def single_click(self, column, x, y):
        if column == 3:
            self.round_plus()
        elif column == 2:
            self.round_minus()

        self.device_name = self.devices[self.index - 1].get_device_desc()
        net_manager.emit_wifi_switch(self.index - 1)
        self.redraw()

    def round_plus(self):
        if self.index == len(self.devices):
            self.index = 1
        else:
            self.index += 1

    def round_minus(self):
        self.index -= 1
        if self.index == 0:
            self.index = len(self.devices)

    def set_index(self, device):
        self.device_name = device.get_device_desc()
        self.index = self.devices.index(device) + 1
        self.redraw()

if __name__=="__main__":

    win = gtk.Window(gtk.WINDOW_TOPLEVEL)
    win.set_title("Container")
    win.set_size_request(700,100)
    #win.border_width(2)

    win.connect("destroy", lambda w: gtk.main_quit())
    tree = [WirelessItem("deepinwork"), WirelessItem("myhost")]
    tv = TreeView(tree)
    tv.set_spacing = 0
    vbox = gtk.VBox(False)
    vbox.pack_start(tv)
    win.add(vbox)
    win.show_all()

    gtk.main()
