#!/usr/bin/env python
#-*- coding:utf-8 -*-

from theme import app_theme

from dtk.ui.tab_window import TabBox
from dtk.ui.button import Button,ToggleButton, RadioButton, CheckButton
from dtk.ui.entry import InputEntry, TextEntry
from dtk.ui.label import Label
from dtk.ui.spin import SpinBox
from dtk.ui.utils import container_remove_all
#from dtk.ui.droplist import Droplist
from dtk.ui.combo import ComboBox
from widgets import SettingButton
# NM lib import 
from nmlib.nm_utils import TypeConvert
from nmlib.nmclient import nmclient
wired_device = nmclient.get_wired_devices()[0]
from nmlib.nm_remote_settings import nm_remote_settings
from container import Contain

import gtk

class DSLSetting(gtk.HBox):

    def __init__(self, slide_back_cb = None, change_crumb_cb = None):

        gtk.HBox.__init__(self)
        self.slide_back = slide_back_cb
        self.change_crumb = change_crumb_cb
        
        self.wired = None
        self.ipv4 = None
        self.dsl = None
        self.ppp = None

        self.tab_window = TabBox()
        self.items = [("DSL", NoSetting()),
                      ("Wired", NoSetting()),
                      ("IPv4 Setting", NoSetting()),
                      ("PPP", NoSetting())]
        self.tab_window.add_items(self.items)
        self.sidebar = SideBar( None, self.init, self.check_click)

        # Build ui
        self.pack_start(self.sidebar, False , False)
        vbox = gtk.VBox()
        vbox.connect("expose-event", self.expose_event)
        vbox.pack_start(self.tab_window ,True, True)
        self.pack_start(vbox, True, True)
        hbox = gtk.HBox()
        apply_button = gtk.Button("Apply")
        apply_button.connect("clicked", self.save_changes)
        hbox.pack_start(apply_button, False, False, 0)
        buttons_aligns = gtk.Alignment(0.5 , 1, 0, 0)
        buttons_aligns.add(hbox)
        vbox.pack_start(buttons_aligns, False , False)
        hbox.connect("expose-event", self.expose_event)

    def expose_event(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation
        cr.set_source_rgb( 1, 1, 1) 
        cr.rectangle(rect.x, rect.y, rect.width, rect.height)
        cr.fill()

    def init(self):
        # Get all connections  
        connections = nm_remote_settings.get_pppoe_connections()
        # Check connections
        if connections == []:
            # Create a new connection
            nm_remote_settings.new_pppoe_connection()
            connections = nm_remote_settings.get_pppoe_connections()

        self.wired_setting = [Wired(con) for con in connections]
        self.ipv4_setting = [IPV4Conf(con) for con in connections]
        self.dsl_setting = [DSLConf(con) for con in connections]
        self.ppp_setting = [PPPConf(con) for con in connections]

        self.sidebar.init(connections, self.ipv4_setting)
        index = self.sidebar.get_active()
        self.wired = self.wired_setting[index]
        self.ipv4 = self.ipv4_setting[index]
        self.dsl = self.dsl_setting[index]
        self.ppp = self.ppp_setting[index]
        #self.dsl = NoSetting()
        #self.ppp = NoSetting()

        self.init_tab_box()

    def init_tab_box(self):
        self.tab_window.tab_items[0] = ("DSL", self.dsl)
        self.tab_window.tab_items[1] = ("Wired",self.wired)
        self.tab_window.tab_items[2] = ("IPV4 setting",self.ipv4)
        self.tab_window.tab_items[3] = ("PPP", self.ppp)
        tab_index = self.tab_window.tab_index
        self.tab_window.tab_index = -1
        self.tab_window.switch_content(tab_index)
        self.queue_draw()

    def check_click(self, connection):
        index = self.sidebar.get_active()
        self.wired = self.wired_setting[index]
        self.ipv4 = self.ipv4_setting[index]
        self.dsl = self.dsl_setting[index]
        self.ppp = self.ppp_setting[index]
        ##self.dsl = NoSetting()
        #self.ppp = NoSetting()

        self.init_tab_box()
        
    def save_changes(self, widget):
        print "saving"
        self.dsl.save_setting()
        self.ppp.save_setting()

        connection = self.dsl.connection
        connection.update()
        self.change_crumb()
        self.slide_back() 


class SideBar(gtk.VBox):
    def __init__(self, connections , main_init_cb, check_click_cb):
        gtk.VBox.__init__(self, False, 5)
        self.connections = connections
        self.main_init_cb = main_init_cb
        self.check_click_cb = check_click_cb

        # Build ui
        self.buttonbox = gtk.VBox(False, 6)
        self.pack_start(self.buttonbox, False, False)
        add_button = Button("Add setting")
        add_button.connect("clicked", self.add_new_connection)
        self.pack_start(add_button, False, False, 6)
        self.set_size_request(160, -1)
    
    def init(self, connection_list, ip4setting):
        # check active
        active_connection = wired_device.get_active_connection()
        if active_connection:
            active = active_connection.get_connection()
        else:
            active = None

        self.connections = connection_list
        self.setting = ip4setting
        
        # Add connection buttons
        container_remove_all(self.buttonbox)
        btn = SettingButton(None, 
                            self.connections[0],
                            self.setting[0],
                            self.check_click_cb)
        self.buttonbox.pack_start(btn, False, False, 6)
        for index, connection in enumerate(self.connections[1:]):
            button = SettingButton(btn,
                                   connection,
                                   self.setting[index + 1],
                                   self.check_click_cb)
            self.buttonbox.pack_start(button, False, False, 6)

        try:
            index = self.connections.index(active)
            self.buttonbox.get_children()[index].check.set_active(True)
        except ValueError:
            self.buttonbox.get_children()[0].check.set_active(True)

    def get_active(self):
        checks = self.buttonbox.get_children()
        for index,c in enumerate(checks):
            if c.check.get_active():
                return index
    
    def add_new_connection(self, widget):
        new_connection = nm_remote_settings.new_pppoe_connection()
        self.main_init_cb()


class NoSetting(gtk.VBox):
    def __init__(self):
        gtk.VBox.__init__(self)

        label_align = gtk.Alignment(0.5,0.5,0,0)

        label = Label("No active connection")
        label_align.add(label)
        self.add(label_align)


class Wired(gtk.VBox):
    def __init__(self, connection):
        gtk.VBox.__init__(self)
        
        ethernet_setting = connection.get_setting("802-3-ethernet")

        table = gtk.Table(3, 2, False)
        
        mac_address = Label("Device Mac address:")
        table.attach(mac_address, 0, 1, 0, 1)

        mac_entry = gtk.Entry()
        table.attach(mac_entry, 1, 2, 0, 1)

        clone_addr = Label("Cloned Mac Adrress:")
        table.attach(clone_addr, 0, 1, 1, 2)
        clone_entry = gtk.Entry()
        table.attach(clone_entry, 1,2, 1, 2)

        mtu = Label("MTU:")
        table.attach(mtu, 0,1,2,3)
        mtu_spin = SpinBox(0,0, 1500, 1, 55)
        table.attach(mtu_spin, 1,2,2,3)
        
        align = gtk.Alignment(0.5, 0.5, 0, 0)
        align.add(table)
        self.add(align)

        ## retrieve wired info
        (mac, clone_mac, mtu) = ethernet_setting.mac_address, ethernet_setting.cloned_mac_address, ethernet_setting.mtu
        #print mac, clone_mac, mtu
        if mac != None:
            mac_entry.set_text(mac)
        if clone_mac !=None:
            clone_entry.set_text(clone_mac)
        if mtu != None:
            mtu_spin.set_value(int(mtu))

class IPV4Conf(gtk.VBox):

    def __init__(self, connection = None):
        
        gtk.VBox.__init__(self)
        self.connection = connection 
        table = gtk.Table(9, 2 , False)
        # Ip configuration
        self.auto_ip = gtk.RadioButton(None, "自动获得IP地址")
        table.attach(self.auto_ip, 0,1,0,1,)
        self.manual_ip = gtk.RadioButton(self.auto_ip, "手动添加IP地址")
        table.attach(self.manual_ip, 0,1,1,2)

        addr_label = Label("IP地址:")
        table.attach(addr_label, 0,1,2,3)
        self.addr_entry = gtk.Entry()
        #self.addr_entry.set_size(30, 25)
        self.addr_entry.connect("activate", self.check_ip_valid)
        self.addr_entry.set_sensitive(False)
        table.attach(self.addr_entry, 1,2,2,3)

        mask_label = Label("子网掩码:")
        table.attach(mask_label, 0,1,3,4)
        self.mask_entry = gtk.Entry()
        #self.mask_entry.set_size(30, 25)
        self.mask_entry.connect("activate", self.check_mask_valid)
        table.attach(self.mask_entry, 1,2,3,4)
        
        gate_label = Label("默认网关")
        table.attach(gate_label, 0,1,4,5)
        self.gate_entry = gtk.Entry()
        #self.gate_entry.set_size(30, 25)
        self.gate_entry.connect("activate", self.check_gate_valid)
        table.attach(self.gate_entry, 1,2,4,5)
        
        #DNS configuration
        self.auto_dns = gtk.RadioButton(None, "自动获得DNS服务器地址")
        self.manual_dns = gtk.RadioButton(self.auto_dns,"使用下面的dns服务器:")
        table.attach(self.auto_dns, 0, 1, 5, 6) 
        table.attach(self.manual_dns, 0, 1, 6, 7)

        master_dns = Label("首选DNS服务器地址:")
        slave_dns = Label("使用下面的DNS服务器地址:")
        self.master_entry = gtk.Entry()
        self.slave_entry = gtk.Entry()
        #self.master_entry.set_size(30, 25)
        #self.slave_entry.set_size(30, 25)
        self.master_entry.connect("activate", self.check_dns_valid)
        self.slave_entry.connect("activate", self.check_dns_valid)
        
        table.attach(master_dns, 0, 1, 7, 8)
        table.attach(self.master_entry, 1, 2, 7, 8)
        table.attach(slave_dns, 0, 1, 8, 9)
        table.attach(self.slave_entry, 1, 2, 8, 9)

        align = gtk.Alignment(0.5,0.5,0.5,0.5)
        align.add(table)
        self.add(align)
        
        #aligns = gtk.Alignment(0.5,0.5,0,0)
        #hbox = gtk.HBox()
        #self.apply_button = gtk.Button("Apply")
        self.show_all()
        #self.cancel_button = gtk.Button("Cancel")
        #hbox.pack_start(self.cancel_button, False, False, 0)
        #hbox.pack_start(self.apply_button, False, False, 0)
        #aligns.add(hbox)
        #self.add(aligns)
        
        
        self.cs =None
        self.reset(connection)
        self.manual_ip.connect("toggled", self.manual_ip_entry, self.cs)
        self.auto_ip.connect("toggled", self.auto_get_ip_addr, self.cs)
        self.auto_dns.connect("toggled", self.auto_dns_set, self.cs)
        self.manual_dns.connect("toggled", self.manual_dns_set, self.cs)
        #self.apply_button.connect("clicked", self.save_changes, self.cs)
        #self.cancel_button.connect("clicked", self.cancel_changes)

    def check_ip_valid(self, widget ):
        text = widget.get_text()
        if TypeConvert.is_valid_ip4(text):
            print "valid"
        else:
            print "invalid"

    def check_mask_valid(self, widget):
        text = widget.get_text()
        if TypeConvert.is_valid_netmask(text):
            print "valid"
        else:
            print "invalid"


    def check_gate_valid(self, widget):
        text = widget.get_text()
        if TypeConvert.is_valid_gw(self.addr_entry.get_text(),
                                   self.mask_entry.get_text(),
                                   text):
            print "valid"
        else:
            print "invalid"
        

    def check_dns_valid(self, widget):
        text = widget.get_text()
        if TypeConvert.is_valid_ip4(text):
            print "valid"
        else:
            print "invalid"

    def reset(self, connection):
        self.cs = connection.get_setting("ipv4")       
        self.clear_entry()
        #print self.cs.dns
        #print self.cs.method, connection.get_setting("connection").id
        if self.cs.method == "auto":
            self.auto_ip.set_active(True)
            self.addr_entry.set_sensitive(False)
            self.mask_entry.set_sensitive(False)
            self.gate_entry.set_sensitive(False)
            
        else:
            self.manual_ip.set_active(True)
            self.addr_entry.set_sensitive(True)
            self.mask_entry.set_sensitive(True)
            self.gate_entry.set_sensitive(True)
            if not self.cs.addresses == []:
                self.addr_entry.set_text(self.cs.addresses[0][0])
                self.mask_entry.set_text(self.cs.addresses[0][1])
                self.gate_entry.set_text(self.cs.addresses[0][2])

        if self.cs.dns == []:
            self.auto_dns.set_active(True)
            self.master_entry.set_sensitive(False)
            self.slave_entry.set_sensitive(False)
        else:
            self.manual_dns.set_active(True)
            self.master_entry.set_sensitive(True)
            self.slave_entry.set_sensitive(True)
            if len(self.cs.dns) > 1:
                self.slave_entry.set_text(self.cs.dns[1])
            self.master_entry.set_text(self.cs.dns[0])


    def auto_dns_set(self, widget, connection):
        if widget.get_active():
            connection.clear_dns()
            self.master_entry.set_sensitive(False)
            self.slave_entry.set_sensitive(False)

    def manual_dns_set(self, widget, connection):
        if widget.get_active():
            self.master_entry.set_sensitive(True)
            self.slave_entry.set_sensitive(True)
            if len(connection.dns) == 1:
                self.master_entry.set_text(connection.dns[0])
            elif len(connection.dns) > 1:
                self.slave_entry.set_text(connection.dns[1])

    def clear_entry(self):
        self.addr_entry.set_text("")
        self.mask_entry.set_text("")
        self.gate_entry.set_text("")
        self.master_entry.set_text("")
        self.slave_entry.set_text("")

    def auto_get_ip_addr(self, widget, connection):
        if widget.get_active():
            connection.method = 'auto'
            self.addr_entry.set_sensitive(False)
            self.mask_entry.set_sensitive(False)
            self.gate_entry.set_sensitive(False)
    def manual_ip_entry(self,widget, connection):
        if widget.get_active():
            connection.method = 'manual'
            self.addr_entry.set_sensitive(True)
            self.mask_entry.set_sensitive(True)
            self.gate_entry.set_sensitive(True)
            if not connection.addresses == []:
                self.addr_entry.set_text(connection.addresses[0][0])
                self.mask_entry.set_text(connection.addresses[0][1])
                self.gate_entry.set_text(connection.addresses[0][2])
    
    def save_changes(self):
        connection = self.cs
        if connection.method =="manual": 
            connection.clear_addresses()
            connection.add_address([self.addr_entry.get_text(),
                                     self.mask_entry.get_text(),
                                     self.gate_entry.get_text()])
            connection.clear_dns()
            if not self.master_entry.get_text() == "":
                connection.add_dns(self.master_entry.get_text())
            if not self.slave_entry.get_text() == "":
                connection.add_dns(self.slave_entry.get_text())
        
        connection.adapt_ip4config_commit()
        #self.connection.update()


class DSLConf(gtk.VBox):

    def __init__(self, connection):
        gtk.VBox.__init__(self)
        self.connection = connection
        self.dsl_setting = self.connection.get_setting("pppoe")

        # UI
        dsl_table = gtk.Table(4, 3, False)
        username_label = Label("Username:")
        service_label = Label("Service:")
        password_label = Label("Password:")
        #pack labels
        dsl_table.attach(username_label, 0, 1 , 0, 1)
        dsl_table.attach(service_label, 0, 1, 1, 2)
        dsl_table.attach(password_label, 0, 1, 2, 3)

        # entries
        self.username_entry = InputEntry()
        self.username_entry.set_size(200,20)
        self.service_entry = InputEntry()
        self.service_entry.set_size(200,20 )
        self.password_entry = InputEntry()
        self.password_entry.set_size(200, 20)

        #pack entries
        dsl_table.attach(self.username_entry, 1, 3, 0, 1)
        dsl_table.attach(self.service_entry, 1, 3, 1, 2)
        dsl_table.attach(self.password_entry, 1, 3, 2, 3)

        align = gtk.Alignment(0.5, 0.5, 0, 0)
        align.add(dsl_table)
        self.add(align)
        self.show_all()
        self.refresh()

    def refresh(self):
        # get dsl settings
        username = self.dsl_setting.username
        service = self.dsl_setting.service
        password = self.dsl_setting.password
        
        # check if empty
        if username == None:
            username = ""
        if service == None:
            service = ""
        if password == None:
            password = ""
        # fill entry
        self.username_entry.set_text(username)
        self.service_entry.set_text(service)
        self.password_entry.set_text(password)
        
    def save_setting(self):
        username = self.username_entry.get_text()
        service = self.service_entry.get_text()
        password = self.password_entry.get_text()

        self.dsl_setting.username = username
        self.dsl_setting.service = service
        self.dsl_setting.password = password



class PPPConf(gtk.VBox):

    def __init__(self, connection):
        gtk.VBox.__init__(self)

        self.connection = connection
        self.ppp_setting = self.connection.get_setting("ppp")

        method = Contain(app_theme.get_pixbuf("/Network/misc.png"), "Configure Method", self.toggle_cb)
        # invisable settings
        self.refuse_eap = CheckButton("EAP")
        self.refuse_pap = CheckButton("PAP")
        self.refuse_chap = CheckButton("CHAP")
        self.refuse_mschap = CheckButton("MSCHAP")
        self.refuse_mschapv2 = CheckButton("MSCHAP v2")
        
        self.method_table = gtk.Table(5, 8, False)
        self.method_table.set_no_show_all(True)
        self.method_table.hide()
        self.method_table.attach(self.refuse_eap, 0, 8, 0, 1)
        self.method_table.attach(self.refuse_pap, 0, 8, 1, 2)
        self.method_table.attach(self.refuse_chap, 0, 8, 2, 3)
        self.method_table.attach(self.refuse_mschap, 0, 8, 3, 4)
        self.method_table.attach(self.refuse_mschapv2, 0, 8, 4, 5)

        # visible settings
        table = gtk.Table(9, 8, False)
        compression = Label("Compression")
        table.attach(compression, 0, 5, 0 ,1)

        self.require_mppe = CheckButton("Use point-to-point encryption(mppe)")
        self.require_mppe.connect("toggled", self.mppe_toggled)
        self.require_mppe_128 = CheckButton("Require 128-bit encryption")
        self.mppe_stateful = CheckButton("Use stataful MPPE")
        
        self.nobsdcomp = CheckButton("Allow BSD data Compression")
        self.nodeflate = CheckButton("Allow Deflate date compression")
        self.no_vj_comp = CheckButton("Use TCP header compression")

        echo = Label("Echo")
        self.ppp_echo = CheckButton("Send PPP echo packets")
        #self.mppe.set_size_request(100, 10)
        table.attach(self.require_mppe, 0, 10, 1, 2)
        table.attach(self.require_mppe_128, 1, 10, 2, 3)
        table.attach(self.mppe_stateful, 1, 10, 3, 4)
        table.attach(self.nobsdcomp, 0, 10, 4, 5)
        table.attach(self.nodeflate, 0, 10, 5, 6)
        table.attach(self.no_vj_comp, 0, 10, 6, 7)
        table.attach(echo, 0, 5, 7, 8)
        table.attach(self.ppp_echo, 0, 10, 8, 9)

        vbox = gtk.VBox()
        vbox.pack_start(method, False, False)
        vbox.pack_start(self.method_table, False, False)
        vbox.pack_start(table, False, False)
        align = gtk.Alignment(0.5, 0.5, 0, 0)
        align.add(vbox)
        self.add(align)

        self.require_mppe_128.set_sensitive(False)
        self.mppe_stateful.set_sensitive(False)
        self.refresh()

    def refresh(self):
        #=========================
        # retreieve settings
        refuse_eap = self.ppp_setting.refuse_eap
        refuse_pap = self.ppp_setting.refuse_pap
        refuse_chap = self.ppp_setting.refuse_chap
        refuse_mschap = self.ppp_setting.refuse_mschap
        refuse_mschapv2 = self.ppp_setting.refuse_mschapv2

        require_mppe = self.ppp_setting.require_mppe
        require_mppe_128 = self.ppp_setting.require_mppe_128
        mppe_stateful = self.ppp_setting.mppe_stateful

        nobsdcomp = self.ppp_setting.nobsdcomp
        nodeflate = self.ppp_setting.nodeflate
        no_vj_comp = self.ppp_setting.no_vj_comp

        lcp_echo_failure = self.ppp_setting.lcp_echo_failure
        lcp_echo_interval = self.ppp_setting.lcp_echo_interval

        # entering ui
        #if widget.get_active():
            #self.require_mppe_128.set_sensitive(True)
            #self.mppe_stateful.set_sensitive(True)
        #else:
            #self.require_mppe_128.set_active(False)
            #self.mppe_stateful.set_active(False)
            #self.require_mppe_128.set_sensitive(False)
            #self.mppe_stateful.set_sensitive(False)

        self.refuse_eap.set_active( not refuse_eap)
        self.refuse_pap.set_active(not refuse_pap)
        self.refuse_chap.set_active(not refuse_chap)
        self.refuse_mschap.set_active(not refuse_mschap)
        self.refuse_mschapv2.set_active(not refuse_mschapv2)

        self.require_mppe.set_active(require_mppe)
        self.require_mppe_128.set_active(require_mppe_128)
        # FIXME umcomment it when backend ready
        self.mppe_stateful.set_active(mppe_stateful)
        self.nobsdcomp.set_active(not nobsdcomp)
        self.nodeflate.set_active(not nodeflate)
        self.no_vj_comp.set_active(not no_vj_comp)

        if lcp_echo_failure == None and lcp_echo_interval == None:
            self.ppp_echo.set_active(False)
        else:
            self.ppp_echo.set_active(True)
        #==================================

    def save_setting(self):
        refuse_eap = not self.refuse_eap.get_active()
        refuse_pap = not self.refuse_pap.get_active()
        refuse_chap = not self.refuse_chap.get_active()
        refuse_mschap = not self.refuse_mschap.get_active()
        refuse_mschapv2 = not self.refuse_mschapv2.get_active()

        require_mppe = self.require_mppe.get_active()
        require_mppe_128 = self.require_mppe_128.get_active()
        mppe_stateful = self.mppe_stateful.get_active()

        nobsdcomp = not self.nobsdcomp.get_active()
        nodeflate = not self.nodeflate.get_active()
        no_vj_comp = not  self.no_vj_comp.get_active()

        echo = self.ppp_echo.get_active()

        self.ppp_setting.refuse_eap = refuse_eap
        self.ppp_setting.refuse_pap = refuse_pap
        self.ppp_setting.refuse_chap = refuse_chap
        self.ppp_setting.refuse_mschap = refuse_mschap 
        self.ppp_setting.refuse_mschapv2 = refuse_mschapv2
        self.ppp_setting.require_mppe = require_mppe
        self.ppp_setting.require_mppe_128 = require_mppe_128
        self.ppp_setting.mppe_stateful = mppe_stateful

        self.ppp_setting.nobsdcomp = nobsdcomp
        self.ppp_setting.nodeflate = nodeflate
        self.ppp_setting.no_vj_comp = no_vj_comp

        if echo:
            lcp_echo_failure = 5
            lcp_echo_interval = 30
        else:
            lcp_echo_failure = 0
            lcp_echo_interval = 0

        #print self.ppp_setting.prop_dict

    def mppe_toggled(self, widget):
        #print "toggled"
        if widget.get_active():
            self.require_mppe_128.set_sensitive(True)
            self.mppe_stateful.set_sensitive(True)
        else:
            self.require_mppe_128.set_active(False)
            self.mppe_stateful.set_active(False)
            self.require_mppe_128.set_sensitive(False)
            self.mppe_stateful.set_sensitive(False)

    def toggle_cb(self, widget):
        if widget.get_active():
            self.method_table.set_no_show_all(False)
            self.show_all()
        else:
            self.method_table.set_no_show_all(True)
            self.method_table.hide()




        # Check Buttons