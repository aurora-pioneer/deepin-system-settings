#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Hou Shaohui
# 
# Author:     Hou Shaohui <houshao55@gmail.com>
# Maintainer: Hou Shaohui <houshao55@gmail.com>
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

import os
import glib
import shutil

PROGRAM_NAME = "deepin-individuation"

homedir = os.path.expanduser("~")
lastdir = homedir

data_home = glib.get_user_data_dir()
data_home = os.path.join(data_home, PROGRAM_NAME)

config_home = glib.get_user_config_dir()
config_home = os.path.join(config_home, PROGRAM_NAME)

cache_home = glib.get_user_cache_dir()
cache_home = os.path.join(cache_home, PROGRAM_NAME)

data_dirs = os.getenv("XDG_DATA_DIRS")
if data_dirs == None:
    data_dirs = "/usr/local/share/:/usr/share/"
    
data_dirs = [os.path.join(d, PROGRAM_NAME) for d in data_dirs.split(":")]

config_dirs = os.getenv("XDG_CONFIG_DIRS")
if config_dirs == None:
    config_dirs = "/etc/xdg"
config_dirs = [os.path.join(d, PROGRAM_NAME) for d in config_dirs.split(":")]

program_dir = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]

data_dir = os.path.join(program_dir, 'data')
data_dirs.insert(0, data_dir)
data_dirs.insert(0, data_home)

# insert the config dir
config_dir = os.path.join(program_dir, 'data', 'config')
config_dirs.insert(0, config_dir)


def get_config_dir():
    return config_home

def get_config_dirs():
    return config_dirs[:]

def get_data_dir():
    return data_home

def get_data_dirs():
    return data_dirs[:]

def get_cache_dir():
    return cache_home

def _get_path(basedirs, *subpath_elements, **kwargs):
    check_exists = kwargs.get("check_exists", True)
    subpath = os.path.join(*subpath_elements)
    for d in basedirs:
        path = os.path.join(d, subpath)
        if not check_exists or os.path.exists(path):
            return path
    return None

def get_data_path(*subpath_elements, **kwargs):
    return _get_path(data_dirs, *subpath_elements, **kwargs)

def get_config_path(*subpath_elements, **kwargs):
    return _get_path(config_dirs, *subpath_elements, **kwargs)

def get_data_home_path(*subpath_elements, **kwargs):
    return _get_path([data_home], *subpath_elements, **kwargs)

def get_last_dir():
    return lastdir

def get_plugin_data_dir():
    path = os.path.join(get_data_dirs()[0], 'plugin_data')
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def get_user_theme_dir():
    user_theme_dir = os.path.join(get_config_dir(), "theme")
    if not os.path.exists(user_theme_dir):
        os.makedirs(user_theme_dir)
    return user_theme_dir    

def get_system_theme_dir():
    program_theme_dir = os.path.join(program_dir, "theme")

    system_theme_dir = os.path.join(get_config_dir(), "system-theme")
    if os.path.exists(system_theme_dir):
        try:
            shutil.rmtree(system_theme_dir)
        except: pass    
    os.makedirs(system_theme_dir)
    for theme_file in os.listdir(program_theme_dir):
        shutil.copy("%s/%s" % (program_theme_dir, theme_file), "%s/%s" % (system_theme_dir , theme_file))
        
    return system_theme_dir

def get_image_path(name):
    return os.path.join(program_dir, "data", "images", name)

def get_system_wallpaper_dirs():
    return ["/usr/share/backgrounds", os.path.join(program_dir, "backgrounds")]

def get_download_wallpaper_dir():
    wallpaper_dir = os.path.join(get_images_dir(), "deepin-wallpapers")
    if not os.path.exists(wallpaper_dir):
        os.makedirs(wallpaper_dir)
    return wallpaper_dir    

def get_images_dir():
    return glib.get_user_special_dir(glib.USER_DIRECTORY_PICTURES)

def get_specify_cache_dir(*subpath):
    path = os.path.join(get_cache_dir(), *subpath)
    if not os.path.exists(path):
        os.makedirs(path)
    return path    

def _make_missing_dirs():
    if not os.path.exists(data_home):
        os.makedirs(data_home)
    if not os.path.exists(config_home):
        os.makedirs(config_home)
    if not os.path.exists(cache_home):
        os.makedirs(cache_home)
        
