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
from dtk.ui.new_treeview import TreeItem, TreeView
from dtk.ui.draw import draw_vlinear, draw_pixbuf, draw_text, draw_line
from dtk.ui.utils import get_content_size, cairo_disable_antialias, color_hex_to_cairo, cairo_state
from deepin_utils.file import get_parent_dir
from dtk.ui.constant import DEFAULT_FONT_SIZE
from dtk.ui.new_entry import EntryBuffer, Entry
#from nm_modules import cache
from shared_methods import NetManager
from widgets import AskPasswordDialog
from nmlib.nm_remote_connection import NMRemoteConnection

from nm_modules import cache

#from lan_config import WiredSetting, NoSetting
#from wlan_config import WirelessSetting
#from wired import *
import gtk
import pango

import sys,os
from dtk.ui.label import Label
sys.path.append(os.path.join(get_parent_dir(__file__, 4), "dss"))
from constant import *
from nls import _
from math import radians
from helper import Dispatcher

#from settings_widget import LoadingThread
import threading as td
import time

bg_hover_color="#ebf4fd"
bg_normal_color = "#f6f6f6"
#bg_normal_color = "#ffffff"
border_hover_color="#7da2ce"
border_normal_color = "#d2d2d2"
#border_normal_color = "#ffffff"
net_manager = NetManager()

class GenItems(TreeItem):
    H_PADDING = 10
    V_PADDING = 5
    CHECK_WIDTH = IMG_WIDTH + 20
    JUMP_WIDTH = IMG_WIDTH + 10

    NETWORK_DISCONNECT = 0
    NETWORK_LOADING = 1
    NETWORK_CONNECTED = 2

    def __init__(self):
        TreeItem.__init__(self)

        self.network_state = 0
        self.loading_pixbuf = app_theme.get_pixbuf("network/loading.png")
        self.check_pixbuf = app_theme.get_pixbuf("network/check_box-2.png")
        self.check_out_pixbuf = app_theme.get_pixbuf("network/check_box_out.png")
        self.jumpto_pixbuf = app_theme.get_pixbuf("network/jump_to.png")

        self.border_color = border_normal_color
        self.bg_color = bg_normal_color

    def render_check(self, cr, rect):
        self.render_background(cr,rect)

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
        #self.is_hover = True
        self.bg_color = bg_hover_color
        #self.border_color = border_hover_color
        self.redraw()

    def unhover(self, column, offset_x, offset_y):
        #self.is_hover = False
        self.bg_color = bg_normal_color
        #self.border_color = border_normal_color
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

class LoadingThread(td.Thread):
    def __init__(self, widget):
        td.Thread.__init__(self)
        self.setDaemon(True)
        self.widget = widget
    
    def run(self):
        position = 0
        try:
            while self.widget.get_net_state() == 1:
                self.widget.refresh_loading(position)
                time.sleep(0.1)
                position += 60
        except Exception, e:
            print "class LoadingThread got error %s" % e
##################
class WiredItem(GenItems):
    def __init__(self, device, setting, font_size=DEFAULT_FONT_SIZE):
        GenItems.__init__(self)
        self.device = device
        self.essid = self.device.get_device_desc()
        self.font_size = font_size

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
        if column == 2:
            from lan_config import WiredSetting
            Dispatcher.to_setting_page(WiredSetting(self.device))
        else:
            device_ethernet = cache.get_spec_object(self.device.object_path)
            device_ethernet.auto_connect()
        self.redraw()

class WirelessItem(GenItems):
    def  __init__(self,
                  ap,
                  font_size = DEFAULT_FONT_SIZE):
        GenItems.__init__(self)
        self.ap = ap
        self.ssid = self.ap.get_ssid()
        self.strength = ap.get_strength()
        self.security = int(ap.get_flags())
        self.font_size = font_size
        self.is_last = False

        '''
        Pixbufs
        '''
        self.lock_pixbuf =  app_theme.get_pixbuf("lock/lock.png")
        self.strength_0 = app_theme.get_pixbuf("network/Wifi_0.png")
        self.strength_1 = app_theme.get_pixbuf("network/Wifi_1.png")
        self.strength_2 = app_theme.get_pixbuf("network/Wifi_2.png")
        self.strength_3 = app_theme.get_pixbuf("network/Wifi_3.png")

    def render_ssid(self, cr, rect):
        self.render_background(cr,rect)
        (text_width, text_height) = get_content_size(self.ssid)
        draw_text(cr, self.ssid, rect.x, rect.y, rect.width, rect.height,
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
            Dispatcher.to_setting_page(WirelessSetting(self.ap))
        elif column < 2:
            self.connect_by_ssid(self.ssid, self.ap)

    def connect_by_ssid(self, ssid, ap):
        connection =  net_manager.connect_wireless_by_ssid(ssid)
        self.ap = ap
        if connection and not isinstance(connection, NMRemoteConnection):
            security = net_manager.get_security_by_ap(self.ap)
            if security:
                print "connect by ssid"
                self.toggle_dialog(connection, security)
            else:
                connection = nm_module.nm_remote_settings.new_connection_finish(connection.settings_dict, 'lan')
                #ap = filter(lambda ap:ap.get_ssid() == ssid, self.ap_list)
                nm_module.nmclient.activate_connection_async(connection.object_path,
                                          net_manager.wireless_devices[0].object_path,
                                           ap.object_path)

    def toggle_dialog(self, connection, security=None):
            AskPasswordDialog(connection,
                              key_mgmt=security,
                              cancel_callback=self.cancel_ask_pwd,
                              confirm_callback=self.pwd_changed).show_all()

    def cancel_ask_pwd(self):
        pass

    def pwd_changed(self, pwd, connection):
        if not isinstance(connection, NMRemoteConnection):
            connection = nm_module.nm_remote_settings.new_connection_finish(connection.settings_dict, 'lan')
        
        if hasattr(self, "connection"):
            if self.connection:
                net_manager.save_and_connect(pwd, connection, self.connection)
            else:
                net_manager.save_and_connect(pwd, connection, None)
        else:
            net_manager.save_and_connect(pwd, connection, None)

class InfoItem(GenItems):
    def __init__(self, content):
        GenItems.__init__(self)
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
        return [self.CHECK_WIDTH, -1, -1, self.JUMP_WIDTH]

class HidenItem(GenItems):

    def __init__(self,
                 connection,
                 font_size = DEFAULT_FONT_SIZE):

        TreeItem.__init__(self)
        self.setting_object = setting_object
        self.connection = connection
        self.slide_to_setting = slide_to_setting_cb
        self.essid = connection.get_setting("802-11-wireless").ssid

        self.font_size = font_size
        self.is_last = False
        self.check_width = self.get_check_width()
        self.essid_width = self.get_essid_width(self.essid)
        self.signal_width = self.get_signal_width()
        self.jumpto_width = self.get_jumpto_width()
        
        self.network_state = self.NETWORK_DISCONNECT
        self.position = 0

        '''
        Pixbufs
        '''
        self.border_color = border_normal_color
        self.bg_color = bg_normal_color
        self.loading_pixbuf = app_theme.get_pixbuf("network/loading.png")
        self.check_pixbuf = app_theme.get_pixbuf("network/check_box-2.png")
        self.check_out_pixbuf = app_theme.get_pixbuf("network/check_box_out.png")

        self.lock_pixbuf =  app_theme.get_pixbuf("lock/lock.png")
        self.strength_0 = app_theme.get_pixbuf("network/Wifi_0.png")
        self.strength_1 = app_theme.get_pixbuf("network/Wifi_1.png")
        self.strength_2 = app_theme.get_pixbuf("network/Wifi_2.png")
        self.strength_3 = app_theme.get_pixbuf("network/Wifi_3.png")

        self.jumpto_pixbuf = app_theme.get_pixbuf("network/jump_to.png")

    def render_check(self, cr, rect):
        render_background(cr,rect)
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

    def draw_loading(self, cr, rect):
        with cairo_state(cr):
            cr.translate(rect.x + 18 , rect.y + 15)
            cr.rotate(radians(60*self.position))
            cr.translate(-18, -15)
            draw_pixbuf(cr, self.loading_pixbuf.get_pixbuf(), 10 , 7)

    def render_essid(self, cr, rect):
        render_background(cr,rect)
        (text_width, text_height) = get_content_size(self.essid)
        if self.is_select:
            text_color = None
        draw_text(cr, self.essid, rect.x, rect.y, rect.width, rect.height,
                alignment = pango.ALIGN_LEFT)

        with cairo_disable_antialias(cr):
            cr.set_source_rgb(*color_hex_to_cairo(self.border_color))
            cr.set_line_width(1)
            if self.is_last:
                cr.rectangle(rect.x, rect.y + rect.height -1, rect.width, 1)
            cr.rectangle(rect.x, rect.y, rect.width, 1)
            cr.fill()

    def render_signal(self, cr, rect):
        render_background(cr,rect)
        with cairo_disable_antialias(cr):
            cr.set_source_rgb(*color_hex_to_cairo(self.border_color))
            cr.set_line_width(1)
            if self.is_last:
                cr.rectangle(rect.x, rect.y + rect.height -1, rect.width, 1)
            cr.rectangle(rect.x, rect.y, rect.width, 1)
            cr.fill()
    
    def render_jumpto(self, cr, rect):
        render_background(cr,rect)
        if self.is_select:
            pass
        jumpto_icon = self.jumpto_pixbuf
        draw_pixbuf(cr, jumpto_icon.get_pixbuf(), rect.x , rect.y + (rect.height-IMG_WIDTH)/2)
        with cairo_disable_antialias(cr):
            cr.set_source_rgb(*color_hex_to_cairo(self.border_color))
            cr.set_line_width(1)
            if self.is_last:
                cr.rectangle(rect.x, rect.y + rect.height -1, rect.width, 1)
            cr.rectangle(rect.x, rect.y, rect.width, 1)
            cr.rectangle(rect.x + rect.width -1, rect.y, 1, rect.height)
            cr.fill()

    def get_check_width(self):
        return IMG_WIDTH + self.CHECK_LEFT_PADDING + self.CHECK_RIGHT_PADIING

    def get_essid_width(self, essid):
        return get_content_size(essid)[0]
    
    def get_signal_width(self):
        return IMG_WIDTH*2 + self.SECURITY_RIGHT_PADDING + self.SIGNAL_RIGHT_PADDING

    def get_jumpto_width(self):
        return IMG_WIDTH + self.JUMPTO_RIGHT_PADDING

    def get_column_widths(self):
        return [self.check_width, -1, self.signal_width, self.jumpto_width]

    def get_column_renders(self):
        return [self.render_check, self.render_essid, self.render_signal, self.render_jumpto]

    def get_height(self):
        return CONTAINNER_HEIGHT
        
    def select(self):
        self.is_select = True
        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def set_active(self, b):
        if b:
            self.select()
        else:
            self.unselect()

    def get_active(self):
        return self.is_select

    def unselect(self):
        #print "unselect"
        self.is_select = False
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
    def redraw(self):
        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def hover(self, column, offset_x, offset_y):
        self.border_color = border_hover_color
        self.redraw()

    def unhover(self, column, offset_x, offset_y):
        #print column, offset_x, offset_y
        self.border_color = border_normal_color
        self.redraw()

    def single_click(self, column, x, y):
        if column == 3:
            self.setting_object.init(self.essid, init_connections=True)
            self.send_to_crumb()
            self.slide_to_setting()

    def set_net_state(self, state):
        self.network_state = state
        if state == self.NETWORK_LOADING:
            LoadingThread(self).start()
    
    def get_net_state(self):
        return self.network_state
    
    def refresh_loading(self, position):
        self.position = position
        self.redraw()

def render_background( cr, rect, color=bg_normal_color):
    background_color = [(0,[color, 1.0]),
                        (1,[color, 1.0])]
    (cr, rect.x ,rect.y, rect.width, rect.height, background_color)


'''
class WiredItem(TreeItem):
    CHECK_LEFT_PADDING = 10
    CHECK_RIGHT_PADIING = 10
    JUMPTO_RIGHT_PADDING = 10
    VERTICAL_PADDING = 5

    NETWORK_DISCONNECT = 0
    NETWORK_LOADING = 1
    NETWORK_CONNECTED = 2

    def __init__(self, device, setting,font_size = DEFAULT_FONT_SIZE):
        
        TreeItem.__init__(self)
        self.device = device
        self.essid = self.device.get_device_desc()
        self.items = None
        self.setting = setting
        self.is_last = False
        self.font_size = font_size
        self.check_width = self.get_check_width()
        self.essid_width = self.get_essid_width(self.essid)
        self.jumpto_width = self.get_jumpto_width()
        self.network_state = 0
        self.position = 0
        self.is_double_click = False

        self.border_color = border_normal_color
        self.bg_color = bg_normal_color
        self.loading_pixbuf = app_theme.get_pixbuf("network/loading.png")
        self.check_pixbuf = app_theme.get_pixbuf("network/check_box-2.png")
        self.check_out_pixbuf = app_theme.get_pixbuf("network/check_box_out.png")

    def render_check(self, cr, rect):
        render_background(cr, rect)

        if self.network_state == 1:
            self.draw_loading(cr, rect)
        elif self.network_state == 2:
            draw_pixbuf(cr, self.check_pixbuf.get_pixbuf(), rect.x + self.CHECK_LEFT_PADDING, rect.y + 7)

        with cairo_disable_antialias(cr):
            cr.set_source_rgb(*color_hex_to_cairo(self.border_color))
            cr.set_line_width(1)
            if self.is_last:
                cr.rectangle(rect.x, rect.y + rect.height -1, rect.width, 1)
            cr.rectangle(rect.x, rect.y, rect.width, 1)
            cr.rectangle(rect.x , rect.y, 1, rect.height)
            cr.fill()

    def draw_loading(self, cr, rect):
        with cairo_state(cr):
            cr.translate(rect.x + 18 , rect.y + 15)
            cr.rotate(radians(60*self.position))
            cr.translate(-18, -15)
            draw_pixbuf(cr, self.loading_pixbuf.get_pixbuf(), 10 , 7)

    def render_essid(self, cr, rect):
        render_background(cr, rect)
        (text_width, text_height) = get_content_size(self.essid)
        if self.is_select:
            text_color = None
        draw_text(cr, self.essid, rect.x, rect.y, rect.width, rect.height,
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
        jumpto_icon = app_theme.get_pixbuf("network/jump_to.png").get_pixbuf()
        draw_pixbuf(cr, jumpto_icon, rect.x , rect.y + self.VERTICAL_PADDING)
        with cairo_disable_antialias(cr):
            cr.set_source_rgb(*color_hex_to_cairo(self.border_color))
            cr.set_line_width(1)
            if self.is_last:
                cr.rectangle(rect.x, rect.y + rect.height -1, rect.width, 1)
            cr.rectangle(rect.x, rect.y, rect.width, 1)
            cr.rectangle(rect.x + rect.width -1, rect.y, 1, rect.height)
            cr.fill()

    def get_check_width(self):
        check_icon = app_theme.get_pixbuf("network/check_box.png").get_pixbuf()
        return check_icon.get_width() + self.CHECK_LEFT_PADDING + self.CHECK_RIGHT_PADIING
    def get_essid_width(self, essid):
        return get_content_size(essid)[0]
    
    def get_jumpto_width(self):
        return app_theme.get_pixbuf("network/jump_to.png").get_pixbuf().get_width() + self.JUMPTO_RIGHT_PADDING

    def get_column_widths(self):
        return [self.check_width, -1,self.jumpto_width]

    def get_column_renders(self):
        return [self.render_check, self.render_essid, self.render_jumpto]

    def get_height(self):
        return CONTAINNER_HEIGHT
        
    def unselect(self):
        self.is_select = False
        
    def hover(self, column, offset_x, offset_y):
        self.is_hover = True
        self.border_color = border_hover_color

    def unhover(self, column, offset_x, offset_y):
        #print column, offset_x, offset_y
        self.is_hover = False
        self.border_color = border_normal_color

    def double_click(self, column, x, y):
        self.is_double_click = True

    def single_click(self, column, x, y):
        if column == 2:
            from lan_config import WiredSetting
            Dispatcher.to_setting_page(WiredSetting(self.device))
        #else:
            #if self.is_double_click:
                #print "sadfds"
                #device_ethernet = cache.get_spec_object(self.device.object_path)
                #device_ethernet.auto_connect()

        self.is_double_click = False

        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def redraw(self):
        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def set_net_state(self, state):
        self.network_state = state
        if state == self.NETWORK_LOADING:
            LoadingThread(self).start()
    
    def get_net_state(self):
        return self.network_state
    
    def refresh_loading(self, position):
        self.position = position
        self.redraw()
'''        
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

        draw_text(cr, _("password:"), rect.x, rect.y, rect.width, rect.height,
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
         

class DSLItem(TreeItem):
    CHECK_LEFT_PADDING = 10
    CHECK_RIGHT_PADIING = 10
    JUMPTO_RIGHT_PADDING = 10
    VERTICAL_PADDING = 5

    def __init__(self, essid, setting, slide_to_setting_cb = None,send_to_crumb= False, font_size = DEFAULT_FONT_SIZE):
        
        TreeItem.__init__(self)
        self.slide_to_setting = slide_to_setting_cb
        self.essid = essid
        self.items = None
        self.setting = setting
        self.is_last = False
        self.send_to_crumb = send_to_crumb
        self.font_size = font_size
        self.check_width = self.get_check_width()
        self.essid_width = self.get_essid_width(essid)
        self.jumpto_width = self.get_jumpto_width()
        self.border_color = border_normal_color
        self.bg_color = bg_normal_color

    def render_check(self, cr, rect):
        render_background(cr, rect)

        if self.is_select:
            check_icon = app_theme.get_pixbuf("network/check_box.png").get_pixbuf()
        else:
            check_icon = app_theme.get_pixbuf("network/check_box_out.png").get_pixbuf()

        draw_pixbuf(cr, check_icon, rect.x + self.CHECK_LEFT_PADDING, rect.y + self.VERTICAL_PADDING)
        with cairo_disable_antialias(cr):
            cr.set_source_rgb(*color_hex_to_cairo(self.border_color))
            cr.set_line_width(1)
            if self.is_last:
                cr.rectangle(rect.x, rect.y + rect.height -1, rect.width, 1)
            cr.rectangle(rect.x, rect.y, rect.width, 1)
            cr.rectangle(rect.x , rect.y, 1, rect.height)
            cr.fill()


    def render_essid(self, cr, rect):
        render_background(cr, rect)
        (text_width, text_height) = get_content_size(self.essid)
        if self.is_select:
            text_color = None
        draw_text(cr, self.essid, rect.x, rect.y, rect.width, rect.height,
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
        jumpto_icon = app_theme.get_pixbuf("network/jump_to.png").get_pixbuf()
        draw_pixbuf(cr, jumpto_icon, rect.x , rect.y + self.VERTICAL_PADDING)
        with cairo_disable_antialias(cr):
            cr.set_source_rgb(*color_hex_to_cairo(self.border_color))
            cr.set_line_width(1)
            if self.is_last:
                cr.rectangle(rect.x, rect.y + rect.height -1, rect.width, 1)
            cr.rectangle(rect.x, rect.y, rect.width, 1)
            cr.rectangle(rect.x + rect.width -1, rect.y, 1, rect.height)
            cr.fill()

    def get_check_width(self):
        check_icon = app_theme.get_pixbuf("network/check_box.png").get_pixbuf()
        return check_icon.get_width() + self.CHECK_LEFT_PADDING + self.CHECK_RIGHT_PADIING
    def get_essid_width(self, essid):
        return get_content_size(essid)[0]
    
    def get_jumpto_width(self):
        return app_theme.get_pixbuf("network/jump_to.png").get_pixbuf().get_width() + self.JUMPTO_RIGHT_PADDING

    def get_column_widths(self):
        return [self.check_width, -1,self.jumpto_width]

    def get_column_renders(self):
        return [self.render_check, self.render_essid, self.render_jumpto]

    def get_height(self):
        return  app_theme.get_pixbuf("network/check_box.png").get_pixbuf().get_height() + self.VERTICAL_PADDING *2 
        
    def unselect(self):
        self.is_select = False
        
    def hover(self, column, offset_x, offset_y):
        self.is_hover = True
        self.border_color = border_hover_color

    def unhover(self, column, offset_x, offset_y):
        #print column, offset_x, offset_y
        self.is_hover = False
        self.border_color = border_normal_color

    def redraw(self):
        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def single_click(self, column, x, y):
        #if column == 0 and x in range(self.CHECK_LEFT_PADDING, self.check_width-self.CHECK_RIGHT_PADIING):
            #self.is_select = not self.is_select
        if column == 2:
            if not isinstance(self.setting.ipv4, NoSetting):
                self.setting.ipv4.reset(self.setting.ipv4.connection)
            self.slide_to_setting()
            self.send_to_crumb()

        if self.redraw_request_callback:
            self.redraw_request_callback(self)

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
        #if column == 2:
            #self.setting.init()
            #self.slide_to_setting()
            #self.send_to_crumb()
        if column == 3:
            self.setting.init("", init_connections=True)
            self.slide_to_setting()
            self.send_to_crumb()

        self.redraw()


    def redraw(self):
        if self.redraw_request_callback:
            self.redraw_request_callback(self)


    def set_net_state(self, state):
        self.network_state = state
        if state == self.NETWORK_LOADING:
            LoadingThread(self).start()

    def get_net_state(self):
        return self.network_state
    
    def refresh_loading(self, position):
        self.position = position
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
