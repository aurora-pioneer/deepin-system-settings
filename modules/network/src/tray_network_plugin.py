#!/usr/bin/env python
#-*- coding:utf-8 -*-
# Copyright (C) 2011 ~ 2013 Deepin, Inc.
#               2011 ~ 2013 Zeng Zhi
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

from dtk.ui.utils import container_remove_all
from tray_ui import TrayUI
from shared_methods import NetManager, device_manager
from helper import Dispatcher
from nm_modules import nm_module
from nmlib.nm_remote_connection import NMRemoteConnection
from subprocess import Popen


from widgets import AskPasswordDialog
from vtk.timer import Timer

WAIT_TIME = 15000

class TrayNetworkPlugin(object):

    def __init__(self):
        self.gui = TrayUI(self.toggle_wired, self.toggle_wireless, self.mobile_toggle)
        self.net_manager = NetManager()
        Dispatcher.connect("request_resize", self.request_resize)
        self.gui.button_more.connect("clicked", self.more_setting)

        self.need_auth_flag = False
        self.this_device = None

        self.timer = Timer(WAIT_TIME)
        self.timer.Enabled = False
        self.timer.connect("Tick", self.timer_count_down_finish)

        self.init_wired_signals()
        self.init_wireless_signals()

    def init_values(self, this_list):
        self.this_list = this_list
        self.this = self.this_list[0]
        self.tray_icon = self.this_list[1]
        self.init_widgets()

    def mobile_toggle(self, widget):
        pass
    
    def timer_count_down_finish(self, widget):
        connections = nm_module.nmclient.get_active_connections()
        active_connection = connections[-1]
        
        self.this_connection = active_connection.get_connection()
        self.this_device.nm_device_disconnect()
        self.toggle_dialog(self.this_connection)
        widget.Enabled = False

    def init_widgets(self):
        wired_state = self.net_manager.get_wired_state()
        if wired_state:
            self.gui.wire.set_active(wired_state)
            if wired_state[0] and wired_state[1]:
                self.change_status_icon("cable")
            else:
                self.change_status_icon("cable_disconnect")
            Dispatcher.connect("wired-change", self.set_wired_state)
        else:
            self.gui.remove_net("wired")
        
        wireless_state= self.net_manager.get_wireless_state()
        if wireless_state:
            self.gui.wireless.set_active(wireless_state)
            if wireless_state[0] and wireless_state[1]:
                self.change_status_icon("links")


            Dispatcher.connect("wireless-change", self.set_wireless_state)
            Dispatcher.connect("connect_by_ssid", self.connect_by_ssid)
        else:
            self.gui.remove_net("wireless")


    def toggle_wired(self, widget):
        if widget.get_active():
            self.net_manager.active_wired_device(self.active_wired)
        else:
            self.net_manager.disactive_wired_device(self.disactive_wired)

    def set_wired_state(self, widget, device, new_state, reason):
        '''
        wired-change callback
        '''
        print new_state, reason
        if new_state is 20:
            self.gui.wire.set_active((False, False))
            if self.gui.wireless.get_active():
                self.change_status_icon("links")
            else:
                self.change_status_icon("cable_disconnect")
        elif new_state is 30:
            
            self.gui.wire.set_sensitive(True)
            if self.gui.wireless.get_active():
                self.change_status_icon("links")
            else:
                self.change_status_icon("cable_disconnect")
            if reason is not 0:
                self.gui.wire.set_active((True, False))
        elif new_state is 40:
            print "rotate"
            if not self.gui.wire.get_active():
                self.gui.wire.set_active((True, True))
            self.change_status_icon("loading")
            self.let_rotate(True)
        elif new_state is 100:
            self.active_wired()

    def init_wired_signals(self):
        device_manager.load_wired_listener(self)

    def wired_device_active(self, widget, new_state, old_state, reason):
        self.active_wired()

    def wired_device_deactive(self, widget, new_state, old_state, reason):
        self.gui.wire.set_sensitive(True)
        if self.gui.wireless.get_active():
            self.change_status_icon("links")
        else:
            self.change_status_icon("cable_disconnect")
        if reason is not 0:
            self.gui.wire.set_active((True, False))

    def wired_device_unavailable(self,  widget, new_state, old_state, reason):
        self.gui.wire.set_active((False, False))
        if self.gui.wireless.get_active():
            self.change_status_icon("links")
        else:
            self.change_status_icon("cable_disconnect")

    def wired_device_available(self, widget, new_state, old_state, reason):
            self.gui.wire.set_sensitive(True)
            if self.gui.wireless.get_active():
                self.change_status_icon("links")
            else:
                self.change_status_icon("cable_disconnect")
            if reason is not 0:
                self.gui.wire.set_active((True, False))

    def wired_activate_start(self, widget, new_state, old_state, reason):
            if not self.gui.wire.get_active():
                self.gui.wire.set_active((True, True))
            self.change_status_icon("loading")
            self.let_rotate(True)

    def wired_activate_failed(self, widget, new_state, old_state, reason):
        pass
        #Dispatcher.connect("wired_change", self.wired_changed_cb)

    def connect_by_ssid(self, widget, ssid, ap):
        connection =  self.net_manager.connect_wireless_by_ssid(ssid)
        self.ap = ap
        if connection and not isinstance(connection, NMRemoteConnection):
            security = self.net_manager.get_security_by_ap(self.ap)
            if security:
                print "NMCONNECTION"
                self.toggle_dialog(connection, security)
            else:
                connection = nm_module.nm_remote_settings.new_connection_finish(connection.settings_dict, 'lan')
                #ap = filter(lambda ap:ap.get_ssid() == ssid, self.ap_list)
                nm_module.nmclient.activate_connection_async(connection.object_path,
                                          self.net_manager.wireless_devices[0].object_path,
                                           ap.object_path)
        
    def active_wired(self):
        """
        after active
        """
        self.gui.wire.set_active((True, True))
        self.change_status_icon("cable")
    
    def tray_resize(self, widget, height):
        pass

    def disactive_wired(self):
        """
        after diactive
        """
        if self.net_manager.get_wired_state()[0]:
            self.gui.wire.set_active((True, False))
        if self.gui.wireless.get_active():
            self.change_status_icon("links")
        else:
            self.change_status_icon("cable_disconnect")
    #####=======================Wireless
    def __get_ssid_list(self):
        return self.net_manager.get_ap_list()

    def init_tree(self):
        print "init+tree"
        self.ap_list = self.__get_ssid_list()
        self.gui.set_ap(self.ap_list)

    def toggle_wireless(self, widget):
        if widget.get_active():
            self.init_tree()
            index = self.net_manager.get_active_connection(self.ap_list)
            if index:
                print "Debug", index
                self.gui.set_active_ap(index, True)
            else:
                #if self.this_device and self.this_device.get_state() != 40: 
                self.activate_wireless()
            #Dispatcher.tray_show_more()
            Dispatcher.request_resize()
        else:
            container_remove_all(self.gui.tree_box)
            #self.gui.more_button.set_ap_list([])
            Dispatcher.request_resize()
            
            #Dispatcher.tray_show_more()

            def device_disactive():
                pass

            self.net_manager.disactive_wireless_device(device_disactive)

    def set_wireless_state(self, widget, device, new_state, old_state, reason):
        """
        "wireless-change" signal callback
        """
        self.this_device = device
        print new_state, old_state, reason
        if new_state is 20:
            self.gui.wireless.set_active((False, False))
        elif new_state is 30:
            print "==================="
            #self.notify_send("a", "disconnected", "")
            self.gui.wireless.set_sensitive(True)

            if self.gui.wire.get_active():
                self.change_status_icon("cable")
            else:
                self.change_status_icon("wifi_disconnect")
            if reason == 39:
                self.gui.wireless.set_active((True, False))
                #if self.gui.wireless.get_active():
                    #index = self.gui.get_active_ap()
                    #self.gui.set_active_ap(index, False)
                    #self.need_auth_flag = False
            '''
            if old_state == 120:
                if self.need_auth_flag:
                    self.toggle_dialog(self.this_connection)
                    device.nm_device_disconnect()
               '''     

        elif new_state is 40:
            #self.notify_send("a", "connecting", "")
            self.gui.wireless.set_active((True, True))
            self.change_status_icon("loading")

            self.let_rotate(True)
        elif new_state is 50:
            self.this_device = device
            self.timer.Enabled = True
            self.timer.Interval = WAIT_TIME
                
        #elif new_state is 60 and old_state == 50:
            #active_connection = nm_module.nmclient.get_active_connections()
            #print map(lambda a: a.get_connection(), active_connection)
            #print "need auth"
        elif new_state is 100:
            #self.notify_send("a", "connected", "")
            self.change_status_icon("links")
            self.set_active_ap()
            self.need_auth_flag = False
        '''
        elif new_state is 120 and reason is 7:
            self.need_auth_flag = True
            active_connection = nm_module.nmclient.get_active_connections()[1]
            self.this_connection = active_connection.get_connection()
        '''

    def init_wireless_signals(self):
        device_manager.load_wireless_listener(self)
        self.gui.ap_tree.connect("single-click-item", self.ap_selected)
        self.selected_item = None
        #TODO signals 

    def ap_selected(self, widget, item, column, x, y):
        self.selected_item = item

    def wireless_device_active(self,  widget, new_state, old_state, reason):
        self.change_status_icon("links")
        self.set_active_ap()
        self.need_auth_flag = False

    def wireless_device_deactive(self, widget, new_state, old_state, reason):
        self.gui.wireless.set_sensitive(True)
        if self.gui.wire.get_active():
            self.change_status_icon("cable")
        else:
            self.change_status_icon("wifi_disconnect")
        if reason == 39:
            self.gui.wireless.set_active((True, False))

    def wireless_device_unavailable(self, widget, new_state, old_state, reason):
        self.gui.wireless.set_active((False, False))

    def wireless_activate_start(self, widget, new_state, old_state, reason):
        print "sdfsdf"
        self.gui.wireless.set_active((True, True))
        self.change_status_icon("loading")

        self.let_rotate(True)
        self.this_device = widget
        self.timer.Enabled = True
        self.timer.Interval = WAIT_TIME

    def wireless_activate_failed(self, widget, new_state, old_state, reason):
        connections = nm_module.nmclient.get_active_connections()
        active_connection = connections[-1]
        
        self.this_connection = active_connection.get_connection()
        self.this_device.nm_device_disconnect()
        self.toggle_dialog(self.this_connection)

    def toggle_dialog(self, connection, security=None):
        ssid = connection.get_setting("802-11-wireless").ssid
        if ssid != None:
            AskPasswordDialog(connection,
                              ssid,
                              key_mgmt=security,
                              cancel_callback=self.cancel_ask_pwd,
                              confirm_callback=self.pwd_changed).show_all()


    def cancel_ask_pwd(self):
        self.timer.Enabled = False
        self.timer.Interval = WAIT_TIME

    def pwd_changed(self, pwd, connection):
        if not isinstance(connection, NMRemoteConnection):
            connection = nm_module.nm_remote_settings.new_connection_finish(connection.settings_dict, 'lan')
        
        if hasattr(self, "ap"):
            if self.ap:
                self.net_manager.save_and_connect(pwd, connection, self.ap)
            else:
                self.net_manager.save_and_connect(pwd, connection, None)
        else:
            self.net_manager.save_and_connect(pwd, connection, None)
            
    def set_active_ap(self):
        index = self.net_manager.get_active_connection(self.ap_list)
        print "active index", index
        self.gui.set_active_ap(index, True)

    def activate_wireless(self):
        """
        try to auto active wireless
        """
        def device_actived():
            pass
        self.net_manager.active_wireless_device(device_actived)
    
    def change_status_icon(self, icon_name):
        """
        change status icon state
        """
        self.timer.Enabled = False
        self.timer.Interval = WAIT_TIME
        self.let_rotate(False)
        self.tray_icon.set_icon_theme(icon_name)

    def let_rotate(self, rotate_check, interval=100):
        self.tray_icon.set_rotate(rotate_check, interval)

    def run(self):
        return True

    def insert(self):
        return 3

    def more_setting(self, button):
        try:
            self.this.hide_menu()
            Popen(("deepin-system-settings", "network"))
        except Exception, e:
            print e
            pass
        
    def id(self):
        return "tray-network_plugin"

    def plugin_widget(self):
        return self.gui 
    
    def tray_show_more(self, widget):
        print "tray show more"

    def show_menu(self):
        self.menu_showed = True
        Dispatcher.request_resize()

    def hide_menu(self):
        self.menu_showed = False
        if self.gui.wireless.get_active() and hasattr(self, "ap_list"):
            self.gui.reset_tree()

    def request_resize(self, widget):
        """
        resize this first
        """
        height = self.gui.get_widget_height()
        self.this.resize(1,1)
        self.this.set_size_request(185, height + 46)

def return_plugin():
    return TrayNetworkPlugin
