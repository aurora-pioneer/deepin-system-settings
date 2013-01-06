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
import time
import threading
from logger import Logger
from report import ProgressBar, parse_bytes
from state import ConnectionState
from fetch import HTTPFetch
from events import EventManager

import common

class UpdateObject(object):
    speed = 0
    progress = 0
    remaining = 0

class StopExcetion(Exception):
    pass

class PauseException(Exception):
    pass

class ResumeException(Exception):
    pass

class TaskObject(Logger):
    
    def __init__(self, url, output_file=None, num_connections=4, max_speed=None, verbose=False):
        self.url = url
        self.output_file = self.get_output_file(output_file)
        self.num_connections = num_connections
        self.max_speed = max_speed
        self.conn_state = None
        self.fetch_threads = []
        self.__stop = True
        self.__pause = False
        self.__finish = False
        self.verbose = verbose
        self.signal = EventManager()
        
        self.update_object = UpdateObject()
        
        self.task_thread = None
        
    def get_output_file(self, output_file):    
        if output_file is not None:
            return output_file
        
        return self.url.rsplit("/", 1)[1]
    
    def emit_update(self):
        dl_len = 0
        for rec in self.conn_state.progress:
            dl_len += rec
            
            
        self.update_object.speed = avg_speed = dl_len / self.conn_state.elapsed_time
        self.update_object.progress = dl_len * 100 / self.conn_state.filesize
        self.update_object.remaining = (self.conn_state.filesize - dl_len) / avg_speed if avg_speed > 0 else 0
        
        self.signal.emit("update", self.update_object)
        
    def is_actived(self):    
        for task in self.fetch_threads:
            if task.isAlive():
                return True
        return False    
    
    def stop_all_task(self):
        for task in self.fetch_threads:
            task.need_to_quit = True
            
    def stop(self):        
        self.__stop = True
        self.task_thread = None
        
    def pause(self):    
        self.__pause = True
        
    def resume(self):
        if self.task_thread is None:
            self.signal.emit("resume", None)
            self.start()
        
    def isfinish(self):    
        return self.__finish
    
    def start(self):
        self.task_thread = threading.Thread(target=self.run)
        self.task_thread.setDaemon(True)
        self.task_thread.start()
            
    def run(self):    
        try:
            if not self.output_file:
                self.logerror("Invalid URL")
                self.signal.emit("error", "Invalid URL")
                return
            
            self.__stop = False
            self.__pause = False
            
            file_size = HTTPFetch.get_file_size(self.url)
            if file_size == 0:
                self.logerror("UEL: %s, Unable to get the file size", self.url)
                self.signal.emit("error", "Unable to get the file size")
                return
            
            part_output_file = "%s.part" % self.output_file            
            
            # Checking if we have a partial download available and resume
            self.conn_state = ConnectionState(self.num_connections, file_size)    
            state_file = common.get_state_file(self.url)
            self.conn_state.resume_state(state_file, part_output_file)
            
            # load ProgressBar.
            if file_size < 1024:
                num_connections = 1
            else:    
                num_connections = self.num_connections
            
            self.report_bar = ProgressBar(self.num_connections, self.conn_state)
            
            self.loginfo("File: %s, need to fetch %s", self.output_file, 
                         parse_bytes(self.conn_state.filesize - sum(self.conn_state.progress)))
            
            #create output file with a .part extension to indicate partial download

            os.open(part_output_file, os.O_CREAT | os.O_WRONLY)
            
            start_offset = 0
            start_time = time.time()
            
            
            for i in range(num_connections):
                current_thread = HTTPFetch(i, self.url, self.output_file, state_file, 
                                           start_offset + self.conn_state.progress[i],
                                           self.conn_state)
                self.fetch_threads.append(current_thread)
                current_thread.start()
                start_offset += self.conn_state.chunks[i]
                
            while self.is_actived():
                if self.__stop:
                    raise StopExcetion
                
                if self.__pause:
                    raise PauseException
                
                end_time = time.time()
                self.conn_state.update_time_taken(end_time-start_time)
                start_time = end_time
                
                download_sofar = self.conn_state.download_sofar()
                
                if self.max_speed != None and \
                        (download_sofar / self.conn_state.elapsed_time) > (self.max_speed * 1204):
                    for task in self.fetch_threads:
                        task.need_to_sleep = True
                        task.sleep_timer = download_sofar / (self.max_speed * 1024 - self.conn_state.elapsed_time)
                        
                # update progress        
                if self.verbose:        
                    self.report_bar.display_progress()        
                self.emit_update()
                time.sleep(1)        
                
            if self.verbose:    
                self.report_bar.display_progress()    
                
            os.remove(state_file)    
            os.rename(part_output_file, self.output_file)
            self.__finish = True
            self.emit_update()            
            self.signal.emit("finish", None)
            if self.verbose:    
                self.report_bar.display_progress()    
            
        except StopExcetion:    
            self.stop_all_task()
            
            try:
                os.unlink(part_output_file)
            except: pass    
            
            try:
                os.unlink(state_file)
            except: pass
            
            self.signal.emit("stop", None)
            
        except PauseException:    
            self.stop_all_task()
            self.signal.emit("pause", None)
            
        except KeyboardInterrupt, e:    
            self.stop_all_task()
            
        except Exception, e:    
            print e
            self.logdebug("File: %s at dowloading error %s", self.output_file, e)
            self.stop_all_task()
