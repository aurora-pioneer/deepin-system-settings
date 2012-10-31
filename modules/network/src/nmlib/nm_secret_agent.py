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

import gobject
import keyring
import getpass
import traceback
import dbus
import dbus.service
import dbus.mainloop.glib
from nmobject import NMObject
from nmcache import cache
from nm_utils import TypeConvert

class NMAgentManager(NMObject):
    '''NMAgentManager'''
        
    def __init__(self):
        NMObject.__init__(self, "/org/freedesktop/NetworkManager/AgentManager", "org.freedesktop.NetworkManager.AgentManager")

    def register(self, identifier):
        try:
            if self.validate_identifier(identifier):
                self.dbus_method("Register", identifier, reply_handler = self.register_finish, error_handler = self.register_error)
        except:
            traceback.print_exc()

    def register_finish(self, *reply):
        pass

    def register_error(self, *error):
        pass

    def unregister(self):
        try:
            self.dbus_method("UnRegister", reply_handler = self.unregister_finish, error_handler = self.unregister_error)
        except:
            traceback.print_exc()

    def unregister_finish(self, *reply):
        pass

    def unregister_error(self, *error):
        pass

    def validate_identifier(self, identifier):
        if len(identifier) < 3 or len(identifier) > 255:
            return False
        if identifier.startswith('.') or identifier.endswith('.'):
            return False
        li = list(identifier)
        for i in range(len(li)):
            if li[i] == '.' and li[i+1] == '.':
                return False
            if not li[i].isalnum() and li[i] not in ["_","-","."]:
                return False
        return True    


agent_manager = NMAgentManager()

class NMSecretAgent(NMObject):
    '''NMSecretAgent'''
    # __gsignals__  = {
<<<<<<< HEAD
    #         "registration-result":(gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_NONE,))
=======
    #         "registration-result":(gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_NONE,)),
>>>>>>> origin/master
    #         }
    
    def __init__(self):
        self.auto_register = ""
        self.identifier = "org.freedesktop.NetworkManager.SecretAgent"
        self.registered = ""
        
        agent_manager.register(self.identifier)

    def generate_service_name(self, uuid, setting_name, method):
        return "nm_" + uuid +"_" + setting_name + "_" + method

    def agent_get_secrets(self, conn_path, setting_name, method):
        service = self.generate_service_name(cache.getobject(conn_path).settings_dict["connection"]["uuid"], setting_name)
        username = getpass.getuser()
        return keyring.get_password(service, username)

    def agent_cancel_secrets(self, connection, setting_name):
        pass

    def agent_save_secrets(self, conn_path, setting_name, method):
        service = self.generate_service_name(cache.getobject(conn_path).settings_dict["connection"]["uuid"], 
                                             setting_name, method)
        username = getpass.getuser()
        # password = TypeConvert.dbus2py(cache.getobject(conn_path).settings_dict[setting_name])
        password = cache.getobject(conn_path).get_secrets(setting_name)[setting_name][method]
        print service
        print username
        print password
        keyring.set_password(service, username, password)

    def agent_delete_secrets(self, conn_path, setting_name):
        service = self.generate_service_name(cache.getobject(conn_path).settings_dict["connection"]["uuid"], setting_name)
        username = getpass.get_user()
        if keyring.get_password(service, username):
            keyring.set_password(service, username, "")

# secret_agent = NMSecretAgent()

if __name__ == "__main__":
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)  
    agent = NMSecretAgent()
    mainloop = gobject.MainLoop()
    mainloop.run()
    
