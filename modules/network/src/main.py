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
import dss
from proxy_config import ProxyConfig
import sys
import os
from dss import app_theme
from dtk.ui.theme import ui_theme
from dtk.ui.new_treeview import TreeView
from dtk.ui.draw import  draw_line
from dtk.ui.utils import color_hex_to_cairo, container_remove_all, get_content_size
from deepin_utils.file import  get_parent_dir
from deepin_utils.ipc import is_dbus_name_exists
from dtk.ui.label import Label
from dtk.ui.scrolled_window import ScrolledWindow
import gtk

from container import Contain, ToggleThread
from lists import (WiredItem, WirelessItem, GeneralItem,
                  HidenItem, InfoItem, DSLItem, MobileItem,
                  VPNItem)
from widgets import AskPasswordDialog
from nmlib.nm_remote_connection import NMRemoteConnection


from dsl_config import DSLSetting
from vpn_config import VPNSetting
from mobile_config import MobileSetting
from regions import Region
from settings_widget import HotspotBox

from nmlib.nmcache import cache
from nm_modules import nm_module
from helper import Dispatcher
from device_manager import device_manager

sys.path.append(os.path.join(get_parent_dir(__file__, 4), "dss"))
from module_frame import ModuleFrame 
from nmlib.servicemanager import servicemanager

from nls import _
from constants import *

slider = nm_module.slider
PADDING = 32
from dtk.ui.theme import DynamicColor
LABEL_COLOR = DynamicColor("#666666")

def pack_start(parent, child_list, expand=False, fill=False):
    for child in child_list:
        parent.pack_start(child, expand, fill)

class Section(gtk.VBox):

    def __init__(self):
        gtk.VBox.__init__(self)

    def load(self, toggle, content):
        self.content_box = gtk.VBox(spacing=15)
        self.pack_start(toggle, False, False)
        toggle.switch.connect("toggled", self.toggle_callback)
        
        for c in content:
            self.content_box.pack_start(c, False, False)

        self.align = self._set_align()
        self.pack_start(self.align, False, False)
        self.show_all()

    def _set_align(self):
        align = gtk.Alignment(0,0,1,0)
        align.set_padding(0,0,PADDING,11 + 11)
        #align.add(self.content_box)
        return align

    def toggle_callback(self, widget):
        is_active = widget.get_active()
        print is_active
        if is_active:
            self.toggle_on()
            if self.content_box not in self.align.get_children():
                self.align.add(self.content_box)
            self.show_all()
            self.toggle_on_after()
        
        else:
            self.align.remove(self.content_box)
            self.toggle_off()

    def toggle_on(self):
        '''
        method cb when toggle on
        '''
        print "on"
        pass

    def toggle_on_after(self):
        pass

    def toggle_off(self):
        print "off"
        pass

class TestSection(Section):

    def __init__(self):
        Section.__init__(self)
        self.wire = Contain(app_theme.get_pixbuf("network/cable.png"), _("Wired"), lambda w: w)
        self.button = gtk.Button("Test")
        self.label = Label("this is a test")
        self.load(self.wire, (self.button, self.label))

class WiredDevice(object):

    def __init__(self):
        pass

    def _init_signals(self):
        device_manager.load_wired_listener(self)

    def wired_device_active(self, widget, new_state, old_state, reason):
        index = self.wired_devices.index(widget)
        self.wire.set_active(True)
        if self.tree.visible_items != []:
            self.tree.visible_items[index].set_net_state(2)
            self.tree.queue_draw()

    def wired_device_deactive(self, widget, new_state, old_state, reason):
        index = self.wired_devices.index(widget)
        if not reason == 0:
            if self.tree.visible_items != []:
                self.tree.visible_items[index].set_net_state(0)
                self.tree.queue_draw()

    def wired_device_unavailable(self,  widget, new_state, old_state, reason):
        pass

    def wired_activate_start(self, widget, new_state, old_state, reason):
        index = self.wired_devices.index(widget)
        if self.tree.visible_items != []:
            self.tree.visible_items[index].set_net_state(1)
            self.tree.queue_draw()

    def wired_activate_failed(self, widget, new_state, old_state, reason):
        pass

class WiredSection(Section, WiredDevice):

    def __init__(self):
        Section.__init__(self)
        WiredDevice.__init__(self)
        self.wired_devices = device_manager.get_wired_devices()
        self.init_state()

        self.init_signals()

    def init_state(self):
        if self.wired_devices:
            self.wire = Contain(app_theme.get_pixbuf("network/cable.png"), _("Wired"), lambda w:w)
            self.tree = TreeView([])
            self.tree.set_expand_column(1)
            self.load(self.wire, [self.tree])
            if self.get_state(self.wired_devices):
                self.wire.set_active(True)
        else:
            pass

    def init_signals(self):
        Dispatcher.connect("wired-device-add", self.device_added)
        self._init_signals()
    
    def get_state(self, devices):
        for d in devices:
            if d.get_state() == 100:
                return True
        return False
    
    def device_added(self, widget, device):
        print "device_added"
        self.wired_devices = device_manager.get_wired_devices()
        self.wire.set_active(True, emit=True)

    def get_list(self):
        return map(lambda d: WiredItem(d), self.wired_devices)

    def toggle_on(self):
        self.tree.delete_all_items()
        item_list = self.get_list()
        item_list[-1].is_last = True

        self.tree.add_items(item_list, 0, True)
        self.tree.set_size_request(-1, len(self.tree.visible_items)*30)

    def toggle_on_after(self):
        for i,d in enumerate(self.wired_devices):
            if d.get_state() == 100:
                self.tree.visible_items[i].set_net_state(2)
            else:
                device_ethernet = cache.get_spec_object(d.object_path)
                device_ethernet.auto_connect()

    def toggle_off(self):
        for wired_device in self.wired_devices:
            wired_device.nm_device_disconnect()

class WirelessDevice(object):

    def __init__(self):
        self.pwd_failed = False

    def _init_signals(self):
        device_manager.load_wireless_listener(self)

    def wireless_device_active(self,  widget, new_state, old_state, reason):
        self.pwd_failed = False

        if self.selected_item:
            self.selected_item.set_net_state(2)
            return

        index = self.get_actives(self.ap_list)
        if index:
            map(lambda i: self.tree.visible_items[i].set_net_state(2), index)

    def wireless_device_deactive(self, widget, new_state, old_state, reason):
        if reason == 39:
            # toggle off
            #self.toggle_lock = True
            self.wireless.set_sensitive(True)
            self.wireless.set_active(False)

        if self._get_active_item():
            for item in self._get_active_item():
                item.set_net_state(0)

    def wireless_device_unavailable(self, widget, new_state, old_state, reason):
        pass

    def wireless_activate_start(self, widget, new_state, old_state, reason):
        self.wireless.set_active(True)

        if self._get_active_item():
            for item in self._get_active_item():
                item.set_net_state(0)
        if self.pwd_failed:
            widget.nm_device_disconnect()
            self.toggle_dialog(self.this_connection)

        if self.selected_item:
            self.selected_item.set_net_state(1)
        else:
            index = self.get_actives(self.ap_list)
            if index:
                for i in index:
                    self.tree.visible_items[i].set_net_state(1)
            #self.try_to_connect(ssid)
        connections = nm_module.nmclient.get_active_connections()
        if connections:
            active_connection = connections[-1]
            self.this_connection = active_connection.get_connection()
        else:
            self.this_connection = None

    def wireless_activate_failed(self, widget, new_state, old_state, reason):
        if reason == 7:
            self.pwd_failed = True
        #widget.nm_device_disconnect()
        #if self.this_connection:
            #self.toggle_dialog(self.this_connection)

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
        item = self._get_active_item()
        print item
        index = self.get_actives(self.ap_list)
        print index,"sdf"
        if item:
            map(lambda i: i.pwd_changed(pwd, connection), item)
        else:
            print "no active items found"
    ######

class WirelessSection(Section, WirelessDevice):

    def __init__(self, crumb):
        Section.__init__(self)
        WirelessDevice.__init__(self)
        self.wireless_devices = device_manager.get_wireless_devices()

        self.selected_item = None

        self.init_state()
        self.init_signals()

    def init_state(self):
        if self.wireless_devices:
            self.wireless = Contain(app_theme.get_pixbuf("network/wifi.png"), _("Wireless"), lambda w:w)
            self.tree = TreeView([], enable_multiple_select=False)
            self.tree.set_expand_column(1)
            self.tree.connect("single-click-item", self.set_selected_item)
            self.hotspot = HotSpot(None)
            self.vbox = gtk.VBox(False)
            self.label =  Label(_("Creat Hidden network"), 
                              LABEL_COLOR,
                              underline=True,
                              enable_select=False,
                              enable_double_click=False)
            self.space = gtk.VBox()
            self.space.set_size_request(-1, 15)
            self.load(self.wireless, [self.tree, self.label])
            self.vbox.pack_start(self.space, False, False)
            self.vbox.pack_start(self.hotspot, False, False)
            self.pack_start(self.vbox, False, False)

            ## check state
            if self.get_state(self.wireless_devices):
                self.wireless.set_active(True)
        else:
            pass

    def init_signals(self):
        self._init_signals()
        Dispatcher.connect("ap-added", self.ap_added_callback)
        Dispatcher.connect("ap-removed", self.ap_removed_callback)
        self.label.connect("button-release-event", self.create_a_hidden_network)

    def create_a_hidden_network(self, widget, c):
        from wlan_config import HiddenSetting
        Dispatcher.to_setting_page(HiddenSetting(None))

    def ap_added_callback(self, widget):
        print "ap added"
        if self.wireless.get_active:
            self.wireless.set_active(True, emit=True)

    def ap_removed_callback(self, widget):
        print "ap removed"
        if self.wireless.get_active:
            self.wireless.set_active(True, emit=True)

    def set_selected_item(self, widget, item, column, x, y):
        self.selected_item = item

    def toggle_on(self):
        self.tree.delete_all_items()
        self.td = ToggleThread(self.get_list, self.tree, self.after)
        self.td.start()
        #item_list = self.get_list()
        #if self.ap_list:
            #self.tree.add_items(item_list)
        #self.tree.visible_items[-1].is_last = True

    def get_actives(self, ap_list):
        if not ap_list:
            return []
        index = []
        for wireless_device in self.wireless_devices:
            active_connection = wireless_device.get_active_connection()
            if active_connection:
                try:
                    index.append([ap.object_path for ap in ap_list].index(active_connection.get_specific_object()))
                except ValueError:
                    print "not found in ap list"
        return index

    def _get_active_item(self):
        return filter(lambda i: i.get_net_state() > 0, self.tree.visible_items)

    def toggle_on_after(self):
        pass
        #while self.td.isAlive():
            #continue
    def after(self):
        indexs = self.get_actives(self.ap_list)
        if indexs:
            map(lambda i: self.tree.visible_items[i].set_net_state(2), indexs)
        else:
            for d in self.wireless_devices:
                wifi = cache.get_spec_object(d.object_path)
                wifi.auto_connect()

    def toggle_off(self):
        self.ap_list = []
        self.td.stop_run()
        self.selected_item = None
        for wireless_device in self.wireless_devices:
            wireless_device.nm_device_disconnect()
        #self.toggle_lock = True
        self.wireless.set_sensitive(False)

    def get_list(self):
        self.ap_list = list()
        for wireless_device in self.wireless_devices:
            device_wifi = cache.get_spec_object(wireless_device.object_path)
            self.ap_list += device_wifi.order_ap_list()
        aps = map(lambda i:WirelessItem(i), self.ap_list)
        

        hidden_list = self.get_hidden_connection(self.ap_list)
        hiddens = map(lambda c: HidenItem(c), hidden_list)

        return aps + hiddens
        #return self.ap_list

    def get_hidden_connection(self, ap_list):
        from shared_methods import net_manager


        #ssids = map(lambda a: a.get_ssid(), ap_list)
        #hiddens = filter(lambda c: c.get_setting("802-11-wireless").ssid not in ssids, 
                         #nm_module.nm_remote_settings.get_wireless_connections())
        return net_manager.get_hiddens()

        ## need to filter all aps
    def get_state(self, devices):
        for d in devices:
            if d.get_state() == 100:
                return True
        return False
    
#class WirelesSection(gtk.VBox):
    #def __init__(self, send_to_crumb_cb):
        #gtk.VBox.__init__(self)
        #self.wireless_devices = device_manager.get_wireless_devices()
        #if not nm_module.nmclient.wireless_get_enabled():
            #nm_module.nmclient.wireless_set_enabled(True)
        #if self.wireless_devices:
            ## FIXME will support multi devices
            #self.wireless = Contain(app_theme.get_pixbuf("network/wifi.png"), _("Wireless"), self.toggle_cb)
            #self.send_to_crumb_cb = send_to_crumb_cb

            #self.pack_start(self.wireless, False, False)
            #self.tree = TreeView([], enable_multiple_select=False)
            #self.tree.connect("single-click-item", self.set_selected_item)
            #self.settings = None
            #self.hotspot = HotSpot(send_to_crumb_cb)
            #self.vbox = gtk.VBox(False, spacing=15)
            #self.vbox.set_no_show_all(True)
            #self.vbox.hide()
            #self.align = gtk.Alignment()
            #self.align.show()
            #self.align.set(0,0,1,1)
            #self.align.set_padding(0,0,PADDING,11 + 11)
            #self.align.add(self.tree)
            #self.vbox.pack_start(self.align, False, False)
            #self.vbox.pack_start(self.hotspot, False, False)


            #self.pack_start(self.vbox, False, False, 0)
            #self.__init_signals()

            ##Dispatcher.connect("wireless-change", self.state_changed_callback)

            #self.__init_state()
            
            #self.selected_item = None
            ##self.pack_start(self.hotspot, False, False, 0)

            ## Add signals
            ##for device in self.wireless_devices:
                ##device.connect("state-changed", self.state_changed_callback)

    #def set_selected_item(self, widget, item, column, x, y):
        #self.selected_item = item
        #print "item-selected", item

    #def __init_signals(self):
        #device_manager.load_wireless_listener(self)
    
        ##TODO signals 

    #def _get_active_item(self):
        #return filter(lambda i: i.get_net_state() > 0, self.tree.visible_items)
        
    #def _get_active_ssid(self, device):
        #active_conn = device.get_real_active_connection()
        #if active_conn:
            #return active_conn.get_setting("802-11-wireless").ssid
        #else:
            #return False

    #def state_changed_callback(self, widget, device, new_state, old_state, reason):
        #print "main::wireless",new_state, reason
        #if new_state == 10:
            #return 
        #if new_state is 20:
            #self.wireless.set_active(False)
        #elif new_state is 30:
            ##self.device_is_deactive(reason)
            #if reason == 39:
                #pass

            #if old_state == 120:
                #connections = nm_module.nmclient.get_active_connections()
                #active_connection = connections[-1]
                #self.this_connection = active_connection.get_connection()
                #self.this_device.nm_device_disconnect()
                #self.toggle_dialog(self.this_connection)

        #elif new_state is 40:
            #ssid = self._get_active_ssid(device)
            #if ssid:
                #self.try_to_connect(ssid)
        #elif new_state is 60 and old_state == 50:
            #print "need auth"
        #elif new_state is 100:
            #self.device_is_active(device)
        
    #def ap_added(self):
        #self.tree.set_items(self.retrieve_list())
        #self.show_all()
        #return self.ap_list
    
    #def __init_state(self):
        #if self.wireless_devices:
            ##self.hotspot.add_setting_page(page)
            #for wireless_device in self.wireless_devices:
                #if wireless_device.is_active():
                    #self.wireless.set_active(True)
                #else:
                    #self.wireless.set_active(False)
    
    #def __show_aps(self):
        #item_list = self.retrieve_list()
        #if item_list:
            #self.tree.add_items(item_list,0,True)
            #self.tree.visible_items[-1].is_last = True
            #self.vbox.set_no_show_all(False)
            #self.tree.set_size_request(-1,len(self.tree.visible_items) * self.tree.visible_items[0].get_height())
        #else:
            #self.tree.delete_all_items()
        #self.queue_draw()
        #self.show_all()
            
    #def show_ap_list(self):
        #self.__show_aps()
        #index = self.get_actives(self.ap_list)
        #if index:
            #if index == [-1]:
                #pass
            #elif index[0] == -2:
                ## add hiden network
                #pass
                ##self.tree.add_items([HidenItem(index[1],
                                     ##check_state=2)
                                     ##])
            #else:
                #for i in index:
                    #self.tree.visible_items[i].set_net_state(2)
        #else:
            #if self.wireless_devices[0].get_state() !=30:
                #return
            #for wireless_device in self.wireless_devices:
                #device_wifi = cache.get_spec_object(wireless_device.object_path)
                #print "auto"
                #device_wifi.auto_connect()
        #self.index = index

    #def toggle_cb(self, widget):
        #active = widget.get_active()
        #print "toggled", active
    
        #if active: 
            #self.show_ap_list()
        #else:
            #self.selected_item = None
            #self.tree.delete_all_items()
            #self.vbox.set_no_show_all(True)
            #self.vbox.hide()
            #for wireless_device in self.wireless_devices:
                #wireless_device.nm_device_disconnect()

    #def retrieve_list(self):
        #"""
        #retrieve network lists, will use thread
        #"""
        #self.ap_list = []
        #for wireless_device in self.wireless_devices:
            #device_wifi = cache.get_spec_object(wireless_device.object_path)
            #self.ap_list += device_wifi.order_ap_list()

        #items = [WirelessItem(i) for i in self.ap_list]
        ## Comment for modify
        #items.append(InfoItem(_("connect to hidden network")))
        ##items.append(GeneralItem(_("connect to hidden network"),
                                 ##self.ap_list,
                                 ##self.settings,
                                 ##lambda :slider.slide_to_page(self.settings, "right"),
                                 ##self.send_to_crumb_cb,
                                 ##check_state=0))
        #return items

    #def get_hiden_list(self):
        #ssid_list = []
        #if self.ap_list:
            #for wireless_device in self.wireless_devices:
                #for con in wireless_device.get_wireless_connections():

                    #pass

    #def get_actives(self, ap_list):
        #if not ap_list:
            #return []
        ### TODO 遇到的问题是device已经deactive了， 这个地方还是显示100
        #index = []
        #for wireless_device in self.wireless_devices:
            #active_connection = wireless_device.get_active_connection()
            #if active_connection:
                #try:
                    #index.append([ap.object_path for ap in ap_list].index(active_connection.get_specific_object()))
                #except ValueError:
                    #pass
                    ##if self.check_connection_mode(active_connection.get_connection()):
                        ##return [-1]
                        ##return [-2, active_connection.get_connection()]
        #return index

    #def check_connection_mode(self, connection):
        #mode = connection.get_setting("802-11-wireless").mode
        #if mode == "adhoc":
            #return True
        #else:
            #return False

    #def try_to_connect(self, ssid):
        #print "try_to_connect"
        #self.wireless.set_active(True)
        #if hasattr(self, "ap_list"):
            #ap_list  = [ap.get_ssid() for ap in self.ap_list]
            #try:
                #self.index = ap_list.index(ssid)
                #self.tree.visible_items[self.index].set_net_state(1)
            #except:
                #self.hotspot.set_net_state(1)
    
    #def device_is_active(self, device):
        #print "wireless active"
        #active = device.get_active_connection()
        ## FIXME little wierd
        #for item in self.tree.visible_items:
            #item.set_net_state(0)
        #if active: 
            #try:
                #index = [ap.object_path for ap in self.ap_list].index(active.get_specific_object())
                #self.index = index
                #self.tree.visible_items[index].set_net_state(2)
                #self.tree.visible_items[index].redraw()
            #except ValueError:
                #pass
                ##if self.check_connection_mode(active.get_connection()):
                    ##self.hotspot.set_net_state(2)


    #def device_is_deactive(self, reason):
        #print "wireless deactive", self.index
        #if not self.wireless.get_active():
            #return 
        #if reason == 39:
            #self.wireless.set_active(False)
        #else:
            #try:
                #if self.tree.visible_items != []:
                    #self.tree.visible_items[self.index].set_net_state(0)
                    #self.tree.visible_items[self.index].redraw()
            #except:
                #if self.hotspot.get_net_state() == 1:
                    #self.hotspot.set_net_state(0)

class HotSpot(gtk.VBox):

    def __init__(self, send_to_crumb_cb):
        gtk.VBox.__init__(self, 0)
        cont = Contain(app_theme.get_pixbuf("network/wifi.png"), _("Hotspot"), self.toggle_cb)
        self.pack_start(cont, False, False)
        self.settings = None
        self.send_to_crumb_cb = send_to_crumb_cb
        self.align = gtk.Alignment(0, 0, 1, 1)
        self.align.set_padding(0, 0, PADDING, 22)
        self.hotspot_box = HotspotBox(self.active_connection)
        self.align.add(self.hotspot_box)

        if self.is_adhoc_active():
            cont.set_active(True)
            self.hotspot_box.set_net_state(2)

        self.__init_state()


    def set_net_state(self, state):
        self.hotspot_box.set_net_state(state)

    def get_net_state(self):
        self.hotspot_box.get_net_state()

    def toggle_cb(self, widget):
        active = widget.get_active()
        if active:
            self.add(self.align)
            self.show_all()

            # Handle data
            self.fill_entries()
            if self.hotspot_box.get_net_state() == 2:
                self.hotspot_box.set_active(False)
            else:
                self.hotspot_box.set_active(True)
        else:
            from nmlib.nm_remote_connection import NMRemoteConnection
            if isinstance(self.connection, NMRemoteConnection):
                self.connection.delete()
            self.hotspot_box.set_net_state(0)
            self.hotspot_box.set_active(False)
            self.remove(self.align)

    def fill_entries(self):
        self.connection = self.get_adhoc_connection()
        security_setting = self.connection.get_setting("802-11-wireless-security")
        security_setting.wep_key_type = 2
        if self.connection:
            (ssid, pwd) = self.get_settings(self.connection)
            self.hotspot_box.set_ssid(ssid)
            self.hotspot_box.set_pwd(pwd)

    def get_settings(self, connection):
        ssid = connection.get_setting("802-11-wireless").ssid
        pwd = self.__get_pwd(connection)
        return (ssid, pwd)

    def __get_pwd(self, connection):
        try:
            (setting_name, method) = connection.guess_secret_info() 
            secret = nm_module.secret_agent.agent_get_secrets(connection.object_path,
                                                    setting_name,
                                                    method)
        except:
            secret = ""

        return secret
            

    def get_adhoc_connection(self):
        connections = filter(lambda c: c.get_setting("802-11-wireless").mode == "adhoc",
                             nm_module.nm_remote_settings.get_wireless_connections())
        if connections:
            return connections[0]
        else:
           return nm_module.nm_remote_settings.new_adhoc_connection("")

    def is_adhoc_active(self):
        # TODO just for one device
        wireless_device = nm_module.nmclient.get_wireless_devices()[0]
        active = wireless_device.get_active_connection()
        if active:
            if active.get_connection().get_setting("802-11-wireless").mode == "adhoc":
                return True
            else:
                return False
        else:
            return False
    def is_valid(self):
        security_setting = self.connection.get_setting("802-11-wireless-security")
        active = security_setting.wep_tx_keyidx 
        return security_setting.verify_wep_key(self.hotspot_box.get_ssid(), 2)
        
    def active_connection(self):
        ssid = self.hotspot_box.get_ssid()
        pwd = self.hotspot_box.get_pwd()
        if self.is_valid():
            from nmlib.nm_remote_connection import NMRemoteConnection
            self.connection.get_setting("802-11-wireless").ssid = ssid
            self.connection.get_setting("802-11-wireless-security").set_wep_key(0, pwd)
            
            if not isinstance(self.connection, NMRemoteConnection):
                self.connection = nm_module.nm_remote_settings.new_connection_finish(self.connection.settings_dict, 'lan')

            if isinstance(self.connection, NMRemoteConnection):
                wireless_device = nm_module.nmclient.get_wireless_devices()[0]
                wireless_device.nm_device_disconnect()

                nm_module.nmclient.activate_connection_async(self.connection.object_path,
                                               wireless_device.object_path,
                                               "/")
            return True
        else:
            print "pwd not valid"
            return False

        

    def slide_to_event(self, widget, event):
        self.settings.init("",init_connections=True, all_adhoc=True)
        self.send_to_crumb_cb()
        slider.slide_to_page(self.settings, "right")

    def __init_state(self):
        pass

    def expose_event(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.child.allocation
        width, height = get_content_size(self.label_name)
        cr.set_source_rgb(*color_hex_to_cairo(ui_theme.get_color("link_text").get_color()))
        draw_line(cr, rect.x, rect.y + rect.height, rect.x + width, rect.y + rect.height)

class DSLSection(Section):
    def __init__(self):
        Section.__init__(self)
        self.dsl = Contain(app_theme.get_pixbuf("network/dsl.png"), _("DSL"), lambda w: w)
        self.tree = TreeView([])
        self.tree.set_expand_column(1)
        self.label =  Label(_("DSL Configuration"), 
                          LABEL_COLOR,
                          underline=True,
                          enable_select=False,
                          enable_double_click=False)
        
        self.load(self.dsl, [self.tree, self.label])

        self.__init_signals()

    def __init_signals(self):
        self.label.connect("button-release-event", lambda w,x: self.jumpto_setting())

    def toggle_on(self):
        item_list = self.get_list()
        item_list[-1].is_last = True
        self.tree.delete_all_items()
        self.tree.add_items(item_list)

    def toggle_on_after(self):
        pass
    
    def toggle_off(self):
        pass


    def get_list(self):
        self.connections =  nm_module.nm_remote_settings.get_pppoe_connections()
        return map(lambda c: DSLItem(c, None), self.connections)

    def jumpto_setting(self):
        Dispatcher.to_setting_page(DSLSetting())

class DSLzSection(gtk.VBox):
    def __init__(self, slide_to_setting_cb):
        gtk.VBox.__init__(self)
        self.slide_to_setting = slide_to_setting_cb
        self.setting_page = None
        self.dsl = Contain(app_theme.get_pixbuf("network/dsl.png"), _("DSL"), self.toggle_cb)
        self.pack_start(self.dsl, False, False)

    def toggle_cb(self, widget):
        active = widget.get_active()
        if active:
            self.align = gtk.Alignment(0,0,0,0)
            self.align.set_padding(0,0,PADDING,11)
            label = Label(_("DSL Configuration"), 
                          LABEL_COLOR,
                          underline=True,
                          enable_select=False,
                          enable_double_click=False)
            label.connect("button-release-event", self.slide_to_event)

            self.align.add(label)
            self.add(self.align)
            self.show_all()
        else:
            self.align.destroy()

    def add_setting_page(self, setting_page):
        self.setting_page = setting_page

    def slide_to_event(self, widget, event):
        #from dsl_config import DSLSetting
        Dispatcher.to_setting_page(DSLSetting())
        #self.setting_page.init(init_connections=True)
        #self.slide_to_setting()
        #slider.slide_to_page(self.setting_page, "right")

class VpnSection(Section):
    def __init__(self):
        Section.__init__(self)

        #init
        self.vpn = Contain(app_theme.get_pixbuf("network/vpn.png"), _("VPN Network"), lambda w:w)
        self.tree = TreeView([])
        self.tree.set_expand_column(1)
        self.label = Label(_("VPN Setting"), 
                           LABEL_COLOR,
                           underline=True,
                           enable_select=False,
                           enable_double_click=False)

        self.load(self.vpn, [self.tree, self.label])
        self.init_state()
        
        self.__init_signals()
    
    def init_state(self):
        vpn_active = nm_module.nmclient.get_vpn_active_connection()
        if vpn_active:
            self.vpn.set_active(True)

    def __init_signals(self):
        self.label.connect("button-release-event", lambda w,p: self.jumpto_cb())
        Dispatcher.connect("vpn-redraw", lambda w:self.vpn.set_active(True, emit=True))

    def connect_vpn_signals(self, active_vpn, connection_name):
        active_vpn.connect("vpn-connected", self.vpn_connected, connection_name)
        active_vpn.connect("vpn-connecting", self.vpn_connecting, connection_name)
        active_vpn.connect("vpn-disconnected", self.vpn_disconnected)

    def toggle_on(self):
        item_list = self.get_list()
        #item_list=[]
        if item_list:
            item_list[-1].is_last = True
            self.tree.delete_all_items()
            self.tree.add_items(item_list)

    def toggle_on_after(self):
        vpn_active = nm_module.nmclient.get_vpn_active_connection()
        if vpn_active:
            # TODO fix for mutiple
            connection = vpn_active[0].get_connection()

            try:
                index = self.connection.index(connection)
                self.tree.visible_items[index].set_net_state(2)
                return
            except Exception, e:
                print e
        else:
            pass

    def toggle_off(self):
        vpn_active = nm_module.nmclient.get_vpn_active_connection()
        if vpn_active:
            nm_module.nmclient.deactive_connection_async(vpn_active[0].object_path)
    
    def get_list(self):
        self.connection = nm_module.nm_remote_settings.get_vpn_connections()
        return map(lambda c: VPNItem(c, None), self.connection)
    
    def jumpto_cb(self):
        Dispatcher.to_setting_page(VPNSetting())

class VnSection(gtk.VBox):
    def __init__(self, slide_to_subcrumb_cb):
        gtk.VBox.__init__(self)
        self.slide_to_subcrumb = slide_to_subcrumb_cb
        self.vpn = Contain(app_theme.get_pixbuf("network/vpn.png"), _("VPN Network"), self.toggle_cb)
        self.connection_tree = TreeView([])
        self.label = Label(_("VPN Setting"), 
                           LABEL_COLOR,
                           underline=True,
                           enable_select=False,
                           enable_double_click=False)
        self.label.connect("button-release-event", self.slide_to_event)

        self.vbox = gtk.VBox(False, spacing=15)
        self.align = gtk.Alignment()
        self.align.show()
        self.align.set(0,0,1,0)
        self.align.set_padding(0,0,PADDING,11 + 11)
        self.align.add(self.vbox)
        self.pack_start(self.vpn, False, False)
        self.pack_start(self.align, False, False)

        self.__init_state()

    def toggle_cb(self, widget):
        active = widget.get_active()
        if active:
            vpn_active = nm_module.nmclient.get_vpn_active_connection()
            if vpn_active:
                connection = vpn_active[0].get_connection()
                connection_name = connection.get_setting("connection").id
                #self.vbox.pack_start(self.connection_tree, False, False)
                self.add_item(connection_name, state=2)
                #self.vbox.pack_end(self.label, False, False)
            else:
                self.vbox.pack_end(self.label, False, False)

            self.show_all()
        else:
            container_remove_all(self.vbox)
            vpn_active = nm_module.nmclient.get_vpn_active_connection()
            if vpn_active:
                nm_module.nmclient.deactive_connection_async(vpn_active[0].object_path)

    def add_item(self, connection_name , state):
        #self.vbox.remove(self.connection_tree) 
        container_remove_all(self.vbox)
        self.connection_tree.delete_all_items()
        self.item = GeneralItem(connection_name,
                            None,
                            self.setting,
                            lambda :slider.slide_to_page(self.setting, "right"),
                            self.slide_to_subcrumb,
                            check_state=state)
        self.connection_tree.add_items([self.item]) 
        #self.connection_tree.set_size_request(, -1)
        self.vbox.pack_start(self.connection_tree, False, False)
        

    #def vpn_state_changed(self, widget, state, reason):
        #print "changed",state

    def vpn_connected(self, widget, connection_name):
        print "vpn connected"
        self.item.set_net_state(2)
        #self.sidebar.set_active()

    def vpn_connecting(self, widget, connection_name):
        self.add_item(connection_name, state=1)
        self.item.set_net_state(1)

        #self.vbox.pack_start(self.connection_tree, False, False)
        print "vpn connecting"

    def vpn_disconnected(self, widget):
        print "vpn disconnected"
        container_remove_all(self.vbox)
        if self.vpn.switch.get_active():
            self.vbox.pack_start(self.label, False, False)
        cache.del_spec_object(widget.object_path)

    def slide_to_event(self, widget, event):
        Dispatcher.to_setting_page(VPNSetting())

    def __init_state(self):
        vpn_active = nm_module.nmclient.get_vpn_active_connection()
        if vpn_active:
            self.vpn.switch.set_active(True)

class MobileSection(Section):

    def __init__(self):
        Section.__init__(self)

        # init values
        if self.get_list():
            self.mobile = Contain(app_theme.get_pixbuf("network/3g.png"), _("Mobile Network"), lambda w:w)
            self.tree = TreeView([])
            self.tree.set_expand_column(1)
            self.label = Label(_("Mobile Configuration"),
                          LABEL_COLOR,
                          underline=True,
                          enable_select=False,
                          enable_double_click=False)

            self.load(self.mobile, [self.tree, self.label])
        else:
            pass

    def __init_signals(self):
        nm_module.mmclient.connect("device-added", lambda w,p: mobile.set_active(True))
        self.label.connect("button-release-event", lambda w,p: self.jumpto_cb())

    def toggle_on(self):
        item_list = self.get_list()
        item_list[-1].is_last = True

        self.tree.delete_all_items()
        self.tree.add_items(item_list)

    def toggle_on_after(self):
        pass

    def toggle_off(self):
        pass

    def get_list(self):
        self.cdma = nm_module.mmclient.get_cdma_device()
        self.gsm = nm_module.mmclient.get_gsm_device()

        #self.cdma = nm_module.nm_remote_settings.get_cdma_connections()
        #self.gsm = nm_module.nm_remote_settings.get_gsm_connections()
        
        self.devices = self.cdma + self.gsm
        return map(lambda c: MobileItem(c, None), self.devices)
    
    def jumpto_cb(self):
        Dispatcher.to_setting_page(MobileSetting())


class Mobile(gtk.VBox):
    def __init__(self,
                 send_to_crumb_cb):
        gtk.VBox.__init__(self)
        self.send_to_crumb_cb = send_to_crumb_cb
        mobile = Contain(app_theme.get_pixbuf("network/3g.png"), _("Mobile Network"), self.toggle_cb)
        self.add(mobile)
        self.settings = None
        nm_module.mmclient.connect("device-added", lambda w,p: mobile.set_active(True))

    def toggle_cb(self, widget):
        active = widget.get_active()
        if active:
            self.align = gtk.Alignment(0,0,0,0)
            self.align.set_padding(0,0,PADDING,11 + 11)
            self.add(self.align)
        # Check if there's any mobile device
            mobile_device = nm_module.mmclient.get_cdma_device()
            if mobile_device:
                self.show_device(mobile_device[0])
            else:
                self.show_link()
            self.show_all()
        else:
            self.align.destroy()

    def show_link(self):
        container_remove_all(self.align)
        label = Label(_("Mobile Configuration"),
                      LABEL_COLOR,
                      underline=True,
                      enable_select=False,
                      enable_double_click=False)
        label.connect("button-release-event", self.slide_to_event)
        self.align.add(label)

    def show_device(self, device_path):
        from mm.mmdevice import MMDevice
        container_remove_all(self.align)
        device = MMDevice(device_path)
        manufacturer = device.get_manufacturer()
        model = device.get_model()
        info = model + " " + manufacturer
        item = InfoItem(info, self.jumpto_cb,is_last=True)
        #item = GeneralItem(info,
                           #None,
                           #self.settings,
                           #lambda :slider.slide_to_page(self.settings, "right"),
                           #self.send_to_crumb_cb)
        self.tree = TreeView([item])
        self.tree.set_size_request(758, len(self.tree.visible_items) * self.tree.visible_items[0].get_height())
        self.tree.show_all()
        self.align.add(self.tree)

    def jumpto_cb(self):
        Dispatcher.to_setting_page(MobileSetting(None))

    def device_is_active(self, widget, a):
        print a, "active"

    def device_is_deactive(self, widget, a):
        '''docstring for device_is_deactive'''
        print a, "deactive"

    def slide_to_event(self, widget, event):
        Dispatcher.to_setting_page(MobileSetting(None))

    def add_setting_page(self, setting_page):
        self.settings = setting_page

class Proxy(gtk.VBox):
    def __init__(self, slide_to_setting_cb):
        gtk.VBox.__init__(self)
        self.slide_to_setting = slide_to_setting_cb
        proxy = Contain(app_theme.get_pixbuf("network/proxy.png"), _("Proxy"), self.toggle_cb)
        self.settings = None
        self.add(proxy)

    def toggle_cb(self, widget):
        active = widget.get_active()
        if active:
            self.align = gtk.Alignment(0,0,0,0)
            self.align.set_padding(0,0,PADDING,11)
            label = Label(_("Proxy Configuration"),
                          LABEL_COLOR,
                          underline=True,
                          enable_select=False,
                          enable_double_click=False)
            label.connect("button-release-event", self.slide_to_event)

            self.align.add(label)
            self.add(self.align)
            self.show_all()
        else:
            self.align.destroy()

    def slide_to_event(self, widget, event):
        self.settings.init(True)
        self.slide_to_setting()
        slider.slide_to_page(self.settings, "right")

    def add_setting_page(self, setting_page):
        self.settings = setting_page

class Network(object):
    def __init__(self):        
        self.init_sections()
        self.__init_ui()

        slider._append_page(self.eventbox, "main")
        #slider._append_page(self.wired_setting_page, "wired")
        #slider._append_page(self.dsl_setting_page, "dsl")
        #slider._append_page(self.wireless_setting_page, "wireless")
        #slider._append_page(self.proxy_setting_page, "proxy")
        #slider._append_page(self.vpn_setting_page, "vpn")
        from setting_page_ui import SettingUI
        self.setting_page_ui = SettingUI(None, None)
        slider._append_page(self.setting_page_ui, "setting")
        slider._append_page(Region(), "region")
        #slider._append_page(self.mobile_setting_page, "mobile")
        #pdb.set_trace()
        slider.show_all()
        slider._set_to_page("main")
        Dispatcher.connect("to-setting-page", self.slide_to_setting_page)

    def __init_ui(self):
        vbox = gtk.VBox(False, BETWEEN_SPACING)
        if hasattr(self.wired, "wire"):
            vbox.pack_start(self.wired, False, True,0)
        if hasattr(self.wireless, "wireless"):
            vbox.pack_start(self.wireless, False, True, 0)
        vbox.pack_start(self.dsl, False, True, 0)
        if hasattr(self.mobile, "mobile"):
            vbox.pack_start(self.mobile, False, True, 0)
        vbox.pack_start(self.vpn, False, True, 0)
        vbox.pack_start(self.proxy, False, True, 0)
        vbox.set_size_request(WINDOW_WIDTH - 2 * TEXT_WINDOW_LEFT_PADDING, -1)
        
        scroll_win = ScrolledWindow(right_space=0, top_bottom_space=0)
        scroll_win.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)

        # FIXME UI a align to adjust ui
        ui_align = gtk.Alignment(0, 0, 0, 0)
        ui_align.set_padding(TEXT_WINDOW_TOP_PADDING,
                                    TEXT_WINDOW_TOP_PADDING,
                                    TEXT_WINDOW_LEFT_PADDING,
                                    TEXT_WINDOW_LEFT_PADDING)

        ui_align.add(vbox)
        scroll_win.add_with_viewport(ui_align)

        self.eventbox = gtk.EventBox()
        self.eventbox.set_above_child(False)
        self.eventbox.add(scroll_win)
        vbox.connect("expose-event", self.expose_callback)
        ui_align.connect("expose-event", self.expose_callback)
    
    def __pack_start(self, parent, child_list, expand=False, fill=False):
        for child in child_list:
            parent.pack_start(child, expand, fill)

    def expose_callback(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation
        cr.set_source_rgb( 1, 1, 1) 
        cr.rectangle(rect.x, rect.y, rect.width, rect.height)
        cr.fill()

    def slide_to_setting_page(self, widget, setting_module):
        self.setting_page_ui.load_module(setting_module)

    def activate_succeed(self, widget, connection_path):
        print "active_succeed with", connection_path
        print connection_path

    def activate_failed(self, widget, connection_path):
        print "active failed"

    def device_added(self, widget, connection_path):
        print "device add:", connection_path
        self.wired.refresh_device()

    def device_removed(self, widget, connection_path):
        print "device remove:", connection_path
        self.wired.refresh_device()

    def init_sections(self):
        #slider._set_to_page("main")
        self.wired = WiredSection()
        self.wireless = WirelessSection(lambda : module_frame.send_submodule_crumb(2, _("Wireless Setting")))
        self.dsl = DSLSection()
        self.proxy = Proxy(lambda : module_frame.send_submodule_crumb(2, _("Proxy")))
        self.vpn = VpnSection()

        self.proxy_setting_page = ProxyConfig( lambda  :slider.slide_to_page(self.eventbox, "left"),
                                          lambda  : module_frame.send_message("change_crumb", 1))
        self.proxy.add_setting_page(self.proxy_setting_page)

        self.mobile = MobileSection()
        #self.mobile_setting_page = MobileSetting( lambda  :slider.slide_to_page(self.eventbox, "left"),
                                          #lambda  : module_frame.send_message("change_crumb", 1))
        #self.mobile.add_setting_page(self.mobile_setting_page)

    def refresh(self):
        nm_module.init_objects()
        self.init_sections()
        self.eventbox.set_above_child(False)
        self.eventbox.queue_draw()

    def stop(self):
        self.eventbox.set_above_child(True)
        self.wired_setting_page = None
        self.wireless_setting_page = None
        self.dsl_setting_page = None
        
    def get_main_page(self):
        return self.eventbox

if __name__ == '__main__':
    if is_dbus_name_exists("org.freedesktop.NetworkManager", False):
        module_frame = ModuleFrame(os.path.join(get_parent_dir(__file__, 2), "config.ini"))
        Dispatcher.load_module_frame(module_frame)
        Dispatcher.load_slider(slider)
        network = Network()

        def service_stop_cb(widget, s):
            network.stop()
            global cache
            cache.clearcache()
            cache.clear_spec_cache()

        def service_start_cb(widget, s):
            print "#service start#"
            network.refresh()

        servicemanager.connect("service-start", service_start_cb)
        servicemanager.connect("service-stop", service_stop_cb)
        main_align = network.get_main_page()
        module_frame.add(slider)
        
        def message_handler(*message):
            (message_type, message_content) = message
            if message_type == "show_again":
                slider._set_to_page("main")
                module_frame.send_module_info()
            elif message_type == "click_crumb":
                print "click_crumb"
                (crumb_index, crumb_label) = message_content
                if crumb_index == 1:
                    slider._slide_to_page("main", "left")
                if crumb_label == _("VPN"):
                    slider._slide_to_page("vpn", "left")
        module_frame.module_message_handler = message_handler
        module_frame.run()
