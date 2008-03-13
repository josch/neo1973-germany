"""
 * ProcessInterface.py - SettingsGUI - 
 *   Interface to interactive userspace processes
 *
 * Based on code from Jens Diemer <- ToDo - License
 *
 * Using libgsm_tool until there is a python bindung available
 *
 * (C) 2007 by Kristian Mueller <kristian-m@kristian-m.de>
 * All Rights Reserved
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program; if not, write to the Free Software Foundation, Inc.,
 * 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

import os 
import subprocess
import threading
import signal
import time

class error_poller(threading.Thread):
    def __init__(self, error_stream):
        self.error_stream = error_stream
        threading.Thread.__init__(self)
        ## init
        self.out_data = []
        self.keep_going = True
        self.start()
        
    def run(self):
        while self.keep_going:
            self.error_stream.flush()
            line = self.error_stream.readline()
            if line == "": break
            self.out_data.append(line)

    def stop(self):
        """
        kills process if still running
        """
        if self.process.poll() != None:
            print " already killed"
            return

        self.killed = True
        os.kill(self.process.pid, signal.SIGQUIT)
        ## gice it a second
        time.sleep(1)
        ## have to kill - as readline is blocking.
        os.kill( self.process.pid, signal.SIGKILL )



class async_process(threading.Thread):
    """
    asynchronous subprocess handler

    used to read the output - access through out_data

    not working with Windows - as there is no os.kill() available
    command - the command to be started
    cwd - directory for execution
    timeout - timeout for stop - 
            0 to execution until self.keep_going is set to False
    """
    def __init__(self, command, options, cwd, timeout):
        self.command    = command
        self.options    = options        
        self.cwd        = cwd
        self.timeout    = timeout
        self.process_created_error = False
        self.process_created = False    ## find out when subprocess() finished
        self.keep_going = True
        
        self.killed = False
        self.out_data = [] # output buffer <- ToDo use a list - for now '\n's
        self.events = []

        threading.Thread.__init__(self)
        
#        print "COMMAND was >>%s<<" % self.command
        self.start()
        
        """
        if timeout > 0:
            self.join( self.timeout )
        else:
            self.keep_going = True
            while self.keep_going == True:
                time.sleep(1)
                
        self.join()
        self.stop()
        
        """
        # provide return code
        #self.returncode = self.process.returncode

    def run(self):
        print "Executes subprocess [%s]" % " ".join([self.command] + self.options)
        try:
            self.process = subprocess.Popen(
                    [self.command] + self.options,
                    cwd = self.cwd,
                    bufsize = 1, # line buffer 
                    shell = False,
    #                shell = True, # resulting in broken pipe on stdout
                    universal_newlines = True, # changes any nl/cr-combination to one nl
                    stdout = subprocess.PIPE,
                    stderr = subprocess.PIPE,
                    stdin = subprocess.PIPE
                )
        except:
            print "Error: subprocess %s could not be started" % self.command
            self.process = 0
            self.process_created_error = True
            
        self.process_created = True
        # save output
        line = ""
        while self.keep_going:
            char = ""
            while char == "":
                char = self.process.stdout.read(1)
                if char == "":
                    ## nonblocking? okay let's take a nap
                    time.sleep(0.5)
                    
            line = line + char
            if line[-1] == "\n":
                self.out_data.append(line)
                
                for event in self.events:
                    if line.find(event[0]) >= 0:
                        event[1](line)
                line = ""
                
        print "Subprocess terminated"

    ## event_name <- string to search for (e.g. EVENT: blah changed...)
    ## function <- function to call
    def register_event_handler(self, event_name, function, args, kwargs):
        self.events.append([event_name, function, args, kwargs])

    def stop( self ):
        """
        kills process if still running
        """
        if self.process.poll() != None:
            print " already killed"
            return

        print "trying to kill"
        self.killed = True
        os.kill( self.process.pid, signal.SIGQUIT )
        ## gice it a second
        time.sleep(1)
        ## have to kill - as readline is blocking.
        os.kill( self.process.pid, signal.SIGKILL )

class ProcessInterface:
    def __init__(self, command):
        self.command = command.split()[0]
        self.options = [command.split()[x] for x in range(1,len(command.split()))]
        self.process = async_process(self.command, self.options, "/", timeout = 0)

        while self.process.process_created == False:
            if self.process.process_created_error:
                return -1
            time.sleep(0.1)
        self.error_poller = error_poller(self.process.process.stderr)

    ## write string to buffer - new line is attached string
    def write_to_process(self, string):
        ## find out if process is still running before wire
        if self.process.process.poll() == None:     # was ==
            self.process.process.stdin.write("%s\n" % string)
            self.process.process.stdin.flush()
            return True
        else:
            return False

    ## read back string with all output lines currently in buffer    
    def read_from_process(self):
        out_string = ""
        for x in self.process.out_data:
            out_string += x
        return out_string
    
    ## read back string with all error lines currently in buffer    
    def read_error_from_process(self):
        out_string = ""
        for x in self.error_poller.out_data:
            out_string += x
        return out_string
        
    ## removes first error in list
    def get_error(self):
        if len(self.error_poller.out_data) > 0:
            out_string = self.error_poller.out_data[0]
            self.error_poller.out_data.remove(out_string)
            out_string = out_string.split("\n")[0]
            return out_string
        else:
            return ""

    ## removes first output in list
    def get_output(self):
        if len(self.process.out_data) > 0:
            out_string = self.process.out_data[0]
            self.process.out_data.remove(out_string)
            out_string = out_string.split("\n")[0]
            return out_string
        else:
            return ""

    def register_event_handler(self, event_name, function, args = [], kwargs = {}):
        self.process.register_event_handler(event_name, function, args, kwargs)

    def close_process(self):
        print "trying to kill process"
        self.process.keep_going = False
        self.process.join(1)
        self.process.stop()
        self.process.join(1)


class test:
    def do_test(self):
        print "Test interface"
        bash = ProcessInterface("/bin/sh")
        print "subprocess created"

        time_running = 0
        while time_running < 5:
            print "\nEntering while loop"
            time_running = time_running + 1
            bash.write_to_process("echo hello")
            bash.write_to_process("echo error > /dev/stderr")
            time.sleep(0.2)
            print "next output<%s>" % bash.get_output()
#            print "===\nstdout: <%s> \n===" % bash.read_from_process()
            print "next error<%s>" % bash.get_error()
#            print "===\nstderr: <%s> \n===" % bash.read_error_from_process()
#            time.sleep(0.2)

        bash.close_process()
        print "halllooo"

        # ToDo remove    
        ##         self.process = subprocess.Popen(self.command, cwd = self.cwd, shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE, stdin = subprocess.PIPE)

#test = test()
#test.do_test()
