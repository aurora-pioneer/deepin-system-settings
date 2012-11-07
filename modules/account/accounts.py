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

import dbus
import gobject
import re
import traceback

name_re = re.compile("[0-9a-zA-Z-]*")
accounts_bus = dbus.SystemBus()

def valid_object_path(object_path):
    if not isinstance(object_path, str):
        return False

    if not object_path.startswith("/"):
        return False

    return all(map(lambda x:name_re.match(x), object_path.split(".")))    

class InvalidPropType(Exception):
    
    def __init__(self, prop_name, need_type, real_type = "string"):
        self.prop_name = prop_name
        self.need_type = need_type
        self.real_type = real_type

    def __str__(self):
        return repr("property %s need type %s ,but given type is :%s",
                    (self.prop_name, self.need_type, self.real_type))

class InvalidObjectPath(Exception):
    
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return repr("InvalidObjectPath:" + self.path)


class BusBase(gobject.Gobject):
    
    def __init__(self, path, interface, service = "org.freedesktop.Accounts", bus = accounts_bus):

        if valid_object_path(path):
            self.object_path = path
        else:
            raise InvalidObjectPath(path)

        self.object_interface = interface
        self.service = service
        self.bus = bus

        try:
            self.dbus_proxy = self.bus.get_object(self.service, self.object_path)
            self.dbus_interface = dbus.Interface(self.dbus_proxy, self.object_interface)
        except dbus.exceptions.DBusException:
            traceback.print_exc()

    def init_dbus_properties(self):        
        try:
            self.properties_interface = dbus.Interface(self.dbus_proxy, "org.freedesktop.DBus.Properties" )
        except dbus.exceptions.DBusException:
            traceback.print_exc()

        if self.properties_interface:
            try:
                self.properties = self.properties_interface.GetAll(self.object_interface)
            except:
                print "get properties failed"
                traceback.print_exc()

    def call_sync(self, method_name, *args, **kwargs):
        try:
            return apply(getattr(self.dbus_interface, method_name), args, kwargs)
        except dbus.exceptions.DBusException:
            print "call dbus method failed:%s\n" % method_name
            traceback.print_exc()
    
    def call_async(self, method_name, signature = None, reply = None, error = None, *args, **kwargs):
        try:
            self.bus.call_async(bus_name = self.service, object_path = self.object_path, object_interface = self.object_interface,
                                method = method_name, signature = signature, args = args, reply_handler = reply, 
                                error_handler = error, timeout = -1.0, byte_arrays = False, require_main_loop = True,  **kwargs)

        except dbus.exceptions.DBusException:
            print "call dbus method failed:%s\n" % method_name
            traceback.print_exc()

class Accounts(BusBase):

    __gsignals__  = {
        "user-added":(gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (str,)),
        "user-deleted":(gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (str,))
            }

    def __init__(self):
        BusBase.__init__(self, path = "/org/freedesktop/Accounts", interface = "org.freedesktop.Accounts")

        self.bus.add_signal_receiver(self.user_added_cb, dbus_interface = self.object_interface, 
                                     path = self.object_path, signal_name = "UserAdded")

        self.bus.add_signal_receiver(self.user_deleted_cb, dbus_interface = self.object_interface, 
                                     path = self.object_path, signal_name = "UserDeleted")

        self.init_dbus_properties()

    def get_daemon_version(self):
        return self.properties["DaemonVersion"]

    def create_user(self, name, fullname, account_type):
        return self.call_sync("CreateUser", name, fullname, account_type)

    def delete_user(self, id, remove_files_flag):
        return self.call_async("DeleteUser", id, remove_files_flag)

    def find_user_by_id(self, id):
        return self.call_sync("FindUserById", id)

    def find_user_by_name(self, name):
        return self.call_sync("FindUserByName", name)

    def list_cached_users(self):
        return self.call_sync("ListCachedUsers")

    def user_added_cb(self, userpath):
        self.emit("user-added", userpath)

    def user_deleted_cb(self, userpath):
        self.emit("user-deleted", userpath)


class User(BusBase):

    __gsignals__  = {
        "changed":(gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
            }
    
    def __init__(self, userpath):
        BusBase.__init__(self, path = userpath, interface = "org.freedesktop.Accounts.User")
        
        self.init_dbus_properties()

    ###get properties    
    def get_x_keyboard_layouts(self):
        return self.properties["XKeyboardLayouts"]

    def get_automatic_login(self):
        return self.properties["AutomaticLogin"]

    def get_locked(self):
        return self.properties["Locked"]

    def get_system_account(self):
        return self.properties["SystemAccount"]

    def get_x_has_messages(self):
        return self.properties["XHasMessages"]

    def get_account_type(self):
        return self.properties["AccountType"]

    def get_password_mode(self):
        return self.properties["PasswordMode"]

    def get_background_file(self):
        return self.properties["BackgroundFile"]

    def get_email(self):
        return self.properties["Email"]

    def get_formats_locale(self):
        return self.properties["FormatsLocale"]

    def get_home_directory(self):
        return self.properties["HomeDirectory"]
    
    def get_icon_file(self):
        return self.properties["IconFile"]

    def get_language(self):
        return self.properties["Language"]

    def get_location(self):
        return self.properties["Location"]

    def get_password_hint(self):
        return self.properties["PasswordHint"]

    def get_real_name(self):
        return self.properties["RealName"]

    def get_shell(self):
        return self.properties["Shell"]

    def get_x_session(self):
        return self.properties["XSession"]

    def get_login_frequency(self):
        return self.properties["LoginFrequency"]

    def get_uid(self):
        return self.properties["Uid"]

    ###set methods
    def set_account_type(self, account_type):
        self.call_async("SetAccountType", account_type)

    def set_automatic_login(self, automatic_login):
        self.call_async("SetAutomaticLogin", automatic_login)

    def set_background_file(self, background_file):
        self.call_async("SetBackgroundFile", background_file)

    def set_email(self, email):
        self.call_async("SetEmail", email)

    def set_formats_locale(self, formats_locale):
        self.call_async("SetFormatsLocale", formats_locale)

    def set_home_directory(self, home_directory):
        self.call_async("SetHomeDirectory", home_directory)

    def set_icon_file(self, filename):
        self.call_async("SetIconFile", filename)

    def set_language(self, language):
        self.call_async("SetLanguage", language)

    def set_location(self, location):
        self.call_async("SetLocation", location)

    def set_locked(self, locked):
        self.call_async("SetLocked", locked)

    def set_password(self, password, hint):
        self.call_async("SetPassword", password, hint)

    def set_password_mode(self, password_mode):
        self.call_async("SetPasswordMode", password_mode)

    def set_real_name(self, name):
        self.call_async("SetRealName", name)

    def set_shell(self, shell):
        self.call_async("SetShell", shell)

    def set_user_name(self, username):
        self.call_async("SetUserName", username)

    def set_x_has_messages(self, has_messages):
        self.call_async("SetXHasMessages", has_messages)

    def set_x_keyboard_layouts(self, layouts):
        self.call_async("SetXKeyboardLayouts", layouts)

    def set_x_session(self, x_session):
        self.call_async("SetXSession", x_session)

    ###signals
    def changed_cb(self):
        self.emit("changed")

def test_sync():
    pass

def test_async():
    pass

def test_async_reply():
    pass

if __name__ == "__main__":
    from dbus.mainloop.glib import DBusGMainLoop
    DBusGMainLoop(set_as_default = True)
