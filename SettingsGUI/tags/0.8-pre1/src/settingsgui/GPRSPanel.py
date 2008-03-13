"""
 * GPRSPanel.py - SettingsGUI - GPRS Settings
 *
 * GPRS Connection  Settings - using pppd until the LDISC interface is 
 * finished
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

import sys
import os
import shutil    # to create a backup of pppd config files
import threading
import time
import gtk
import gobject 

from ProcessInterface import * 
from SysFSAccess import * 
from GSMPanel import * 
from GlobalConfiguration import * 
from pppdConfigParser import *

#from settingsgui.ProcessInterface import * 
#from settingsgui.SysFSAccess import * 
#from settingsgui.GSMPanel import * 
#from settingsgui.GlobalConfiguration import * 
#from settingsgui.pppdConfigParser import *

## ToDo
## from GSMPanel import GSMPanel   ## to reach the operator name 
## (name peer like operator)


################################################################################
# lots of methods - will devide them into block with big comments between them #
################################################################################
class GPRSPanel(gtk.VBox):
    def __init__(self, GSM_Panel):
        self.GSM_Panel = GSM_Panel
        gtk.VBox.__init__(self, False, 0)
        self.peer_entries = {}
        self.entry_dict = {}
        self.local_ip = ""
        self.remote_ip = "" 
        self.nameserver_ip = ""

        self.peer_entries.update(self.find_peers())
        self.create_notebook_page()
        self.peer_changed_callback(self.peer_combo)
        self.set_state("disconnected")
        
################################################################################
############ search system for ppp peers (pppd config files) ###################
################################################################################
    def find_peers(self):
        new_dict = {}

        if not os.path.exists(os.path.expanduser(PPP_PATH_TO_USER_PEERS)):
            os.makedirs(os.path.expanduser(PPP_PATH_TO_USER_PEERS))
            print "created %s" % os.path.expanduser(PPP_PATH_TO_USER_PEERS)
        else:
            try:
                for key in os.listdir(
                                    os.path.expanduser(PPP_PATH_TO_USER_PEERS)):
                                    
                    if (key[-1] != '~') \
                    and (key.find("-chat") < 0) \
                    and (key.find("latest_") < 0):
                        path_to_file = os.path.join(
                                os.path.expanduser(PPP_PATH_TO_USER_PEERS), key)
                        new_dict[key] = pppdConfigParser(path_to_file)
#                        print "Added and parsed <%s> (global)" % path_to_file
            except: ## maybe we have no permissions for os.listdir
                None    # nothing we can do about it - 
                        # ToDo: maybe throw a message box

        ## read in system wide peers
        if os.path.exists(PPP_PATH_TO_GLOBAL_PEERS):    
            try:
                for key in os.listdir(PPP_PATH_TO_GLOBAL_PEERS):
                    if ((key[-1] != '~') \
                    and (key.find("-chat") < 0) \
                    and (key.find("latest_") < 0) \
                    and (key.find(PPP_PATH_TO_USER_PEERS) < 0)):
                                    
                        path_to_file = os.path.join(
                                                PPP_PATH_TO_GLOBAL_PEERS, key)
                                                
                        new_dict[key] = pppdConfigParser(path_to_file)
            except: ## maybe we have no permissions for os.listdir
                print "could no access %s" % PPP_PATH_TO_GLOBAL_PEERS

        print "found %d peers" % len(new_dict)
        
        
        ## no peer found, creating default peer
        if len(new_dict) <= 0:
            ## ToDo use users directory
            print "Will create a default peer in /etc/ppp/peers"
            if not os.path.exists(PPP_PATH_TO_GLOBAL_PEERS):
                try:
                    os.makedirs(PPP_PATH_TO_GLOBAL_PEERS)
                except:
                    print "Could not make %s dir" % PPP_PATH_TO_GLOBAL_PEERS
            try:
                filename = os.path.join(PPP_PATH_TO_GLOBAL_PEERS, 
                                                        PPP_DEFAULT_CONFIG_NAME)
                peer_fd = open(filename, 'w')
                print "Creating default peer in %s " % filename
                for line in PPP_DEFAULT_CONFIG.split('\n'):
                    peer_fd.write("%s\n" %line)
                peer_fd.close()

                ## connect chat script                
                filename = os.path.join(PPP_PATH_TO_GLOBAL_PEERS, 
                                "%s-connect-chat" % PPP_DEFAULT_CONFIG_NAME)
                print "Creating default chat file in %s " % filename
                peer_fd = open(filename, 'w')                
                for line in PPP_DEFAULT_CONNECT_SCRIPT.split('\n'):
                    peer_fd.write("%s\n" %line)
                peer_fd.close()

                ## disconnect chat script                
                filename = os.path.join(PPP_PATH_TO_GLOBAL_PEERS, 
                                "%s-disconnect-chat" % PPP_DEFAULT_CONFIG_NAME)
                print "Creating default chat file in %s " % filename
                peer_fd = open(filename, 'w')                
                for line in PPP_DEFAULT_DISCONNECT_SCRIPT.split('\n'):
                    peer_fd.write("%s\n" %line)
                peer_fd.close()
                
                filename = os.path.join(PPP_PATH_TO_GLOBAL_PEERS, 
                                                        PPP_DEFAULT_CONFIG_NAME)
                new_dict[PPP_DEFAULT_CONFIG_NAME] = pppdConfigParser(filename)                                                        
            except:
                print "Could not create peer <%s>" % os.path.join(
                            PPP_PATH_TO_GLOBAL_PEERS, PPP_DEFAULT_CONFIG_NAME)
        return new_dict
        
################################################################################
############# interfacing the pppd subprocess, regestering callbacks ###########
################################################################################
        
    ## starting subprocess
    ## ToDo: use -b and parse a logfile 
    ##   to keep it running when SettingsGUI is quit
    ##   => find out if pppd is running on start up
    def start_pppd(self, config_file):
        parameters = "debug call %s" % config_file
        pppd = ProcessInterface(
            "start-stop-daemon --start -x %s -- %s" % (PPP_INIT, parameters))
        pppd.register_event_handler("ERROR", self.connection_error)
        pppd.register_event_handler("", self.update_output)
        pppd.register_event_handler("local  IP address", self.update_local_ip)
        pppd.register_event_handler("remote IP address", self.update_remote_ip)

    ## ToDo see start_pppd
    def stop_pppd(self):
        pppd = ProcessInterface("start-stop-daemon --stop -x %s" % (PPP_INIT))
        pppd.register_event_handler("", self.update_output)
        self.set_state("disconnected")



################################################################################
############## Callbacks from pppd subprocess output - as callbacks ############
################################################################################
    ## called from pppd parser subprocess
    def update_local_ip(self, string):
        if len(string.split()) >= 3:
            self.local_ip = string.split()[3]
        else:
            self.local_ip = ""
        self.IP_text_buffer.set_text("Local IP: %s\nRemote IP: %s\nNameserver: %s" %(
                self.local_ip, self.remote_ip, self.nameserver_ip))


    ## called from pppd parser subprocess
    def update_remote_ip(self, string):
        if len(string.split()) >= 3:
            self.remote_ip = string.split()[3]
            self.set_state("connected")
        else:
            self.remote_ip = ""
        self.IP_text_buffer.set_text("Local IP: %s\nRemote IP: %s\nNameserver: %s" %(
                self.local_ip, self.remote_ip, self.nameserver_ip))
        

    ## called from pppd parser subprocess
    def connection_error(self, dummy):
        self.set_state("disconnected")


    ## called indirectly from pppd parser subprocess (from set state)
    def update_nameserver(self):
        self.nameserver_ip = ""
        if self.state_string == "connected" and os.path.exists("/etc/resolv.conf"):
            fd = open("/etc/resolv.conf", 'r')
            for line in fd.readlines():
                if line.find("nameserver") >= 0:
                    self.nameserver_ip = line.split()[1]
                    break
            fd.close()

        if not os.path.exists("/etc"):
            try:
                os.makedirs("/etc")
            except:
                print "could not make /etc directory"

        if  len(self.nameserver_ip) <= 0:
            try:
                fd = open("/etc/resolv.conf", 'w')
                fd.write("nameserver %s\n" % DEFAULT_NAMESERVER)
            except:
                print "could not edit /etc/resolv.conf to add a default Nameserver"
            
        self.IP_text_buffer.set_text("Local IP: %s\nRemote IP: %s\nNameserver: %s" %(
                self.local_ip, self.remote_ip, self.nameserver_ip))


    ## called on init and from pppd parser subprocess 
    def set_state(self, state_string):
        self.state_string = state_string
        
        if state_string == "connected":
            self.disconnect_btn.set_sensitive(1)
            self.connect_btn.set_sensitive(0)
            self.update_nameserver()
        
        if state_string == "disconnected":
            self.connect_btn.set_sensitive(1)
            self.disconnect_btn.set_sensitive(0)
            self.update_local_ip("")
            self.update_remote_ip("")
            self.update_nameserver()

    def update_output(self, string):
        ## remove tailing and starting \n and \r - just in case 
        string =  string.rstrip('\n').lstrip('\n').rstrip('\r').lstrip('\r')
        print "pppd: <%s>" % string
        self.update_state(string)



################################################################################
############################## Callbacks from UI ###############################
################################################################################

    ## called when drop down box selection changed
    def peer_changed_callback(self, widget):        
        print "peers changed, filling in entries..."
        entry = widget.get_active_text()
        if not self.peer_entries.has_key(entry):
            self.update_state("Could not open a peer file")
            return False 
            
        self.current_peer_entry = self.peer_entries[entry]
        if self.peer_entries.has_key(entry):
            self.entry_dict["APN"].set_text(self.current_peer_entry.get_APN())
            self.entry_dict["User"].set_text(self.current_peer_entry.get_user())
            self.entry_dict["Password"].set_text(self.current_peer_entry.get_password())
            self.entry_dict["Number"].set_text(self.current_peer_entry.get_number())
        self.current_peer_entry.config_name = entry
        return True
    ## user edited the settings
    def settings_changed(self, widget):
        self.entry_dict[widget.get_name()].set_text(widget.get_text())
        self.add_peer_btn.set_sensitive(1)

    ## ToDo
    def save_peer(self, widget):
        file_path = os.path.join(os.path.expanduser(PPP_PATH_TO_USER_PEERS), \
                                        self.current_peer_entry.config_name)
        if not os.path.exists("%s-backup" % file_path):
            print "will backup peer %s - %s" % (file_path, self.current_peer_entry.config_name)
            try:
                shutil.copyfile(file_path, "%s-backup" % file_path)
                
                if os.path.exists("%s-connect-chat" % file_path) and \
                    not os.path.exists("%s-connect-chat-backup" % file_path):
                    shutil.copyfile("%s-connect-chat" % file_path, \
                                        "%s-connect-chat-backup" % file_path)
                                        
                if os.path.exists("%s-disconnect-chat" % file_path) and \
                    not os.path.exists("%s-disconnect-chat-backup" % file_path):
                    shutil.copyfile("%s-disconnect-chat" % file_path, \
                                        "%s-disconnect-chat-backup" % file_path)
            except:
                self.update_state("Backup of old entry failed - aborting!")
                return False
        
        
        if self.current_peer_entry.generate_configuration(
                os.path.expanduser(PPP_PATH_TO_USER_PEERS), \
                self.current_peer_entry.config_name, \
                self.entry_dict["APN"].get_text(), \
                self.entry_dict["User"].get_text(), \
                self.entry_dict["Password"].get_text(), \
                self.entry_dict["Number"].get_text()):
            self.update_state("%s saved to %s" % (\
                        self.current_peer_entry.config_name, \
                        os.path.expanduser(PPP_PATH_TO_USER_PEERS)))
                       
        return True

    def connect_clicked(self, widget):
        if self.GSM_Panel.stop_gsmd_btn.get_property("sensitive"):
            mbox = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, 
                        gtk.BUTTONS_YES_NO, "Do you want to terminate gsmd first?")
            response = mbox.run()
            mbox.hide()
            mbox.destroy()   
            if response == gtk.RESPONSE_YES:
                print "will terminate gsmd"
                self.GSM_Panel.stop_gsmd(None)
            
        if self.current_peer_entry.generate_configuration(
                os.path.expanduser(PPP_PATH_TO_USER_PEERS), PPP_GENCONFIG_NAME, \
                self.entry_dict["APN"].get_text(), \
                self.entry_dict["User"].get_text(), \
                self.entry_dict["Password"].get_text(), \
                self.entry_dict["Number"].get_text()):
            self.start_pppd(PPP_GENCONFIG_NAME)
        
    def disconnect_clicked(self, widget):
        self.stop_pppd()
        



################################################################################
############################## UI Helper fkts ##################################
################################################################################

    ## change output on "state bar"
    def update_state(self, string):
        self.state_entry.set_text(string)


    ## creating a label + entry box
    def add_entry_with_name(self, name, default_text, password_mode, callback):
        entry_box = gtk.HBox()
        
        label = gtk.Label(name)
        label.set_width_chars(8)
        entry_box.set_spacing(15)
        entry_box.pack_start(label, False, False, 0)
        
        entry = gtk.Entry()
        entry.set_text(default_text)
        entry.set_visibility(password_mode)
        entry.connect("changed", callback)
        entry.set_name(name)
        entry_box.add(entry)
        
        self.entry_dict[name] = entry   ## to access the text entry
        
        entry_box.show()
        return entry_box
        
################################################################################
################################# create UI ####################################
################################################################################
    def create_notebook_page(self):
#        start_time = time.time()
        self.set_border_width(0)

        peer_box = gtk.HBox()
#        self.peer_combo = gtk.combo_box_new_text()
        self.peer_combo = gtk.combo_box_entry_new_text()
        if len(self.peer_entries) <= 0:
            self.peer_combo.append_text("ERROR /etc/ppp/ access?")   ## <- there was no peer and access to /etc/ppp was not possible
        for entry in self.peer_entries:
            self.peer_combo.append_text(entry)
                
        self.peer_combo.set_focus_on_click(False)
#        self.peer_combo.set_property("allow_empty", 0)
        self.peer_combo.set_active(0)

#        self.peer_combo.set_sensitive(0)
        self.peer_combo.connect('changed', self.peer_changed_callback)             

        self.add_peer_btn = gtk.Button()
        image = gtk.Image()
        image.set_from_icon_name("gtk-save", gtk.ICON_SIZE_MENU)
        self.add_peer_btn.add(image)
        self.add_peer_btn.connect('clicked', self.save_peer)
        peer_box.pack_start(self.add_peer_btn, False, False, 0)
        peer_box.add (self.peer_combo)
        if len(self.peer_entries) <= 0:
            self.add_peer_btn.set_sensitive(1)
        else:
            self.add_peer_btn.set_sensitive(0)
            
        self.pack_start(peer_box, False, False, 0)


        # GPRS Settings
        gprs_frame = gtk.Frame("GPRS Login Settings")
        gprs_box = gtk.VBox()
        gprs_box.set_border_width(10)

        gprs_box.add(self.add_entry_with_name("APN", "internet.eplus.de", True, self.settings_changed))
        gprs_box.add(self.add_entry_with_name("User", "gprs", True, self.settings_changed))
        gprs_box.add(self.add_entry_with_name("Password", "gprs", False, self.settings_changed))
        gprs_box.add(self.add_entry_with_name("Number", "*99***1#", True, self.settings_changed))
        gprs_frame.add(gprs_box)
        self.pack_start(gprs_frame, False, False, 0)
        
        # buttons
        btn_box = gtk.HBox()
    
        self.connect_btn = gtk.Button("Connect\nto GPRS")
        self.connect_btn.connect("clicked", self.connect_clicked)
        btn_box.add(self.connect_btn)
        ## to prevent keyboard from beeing activated on startup
        self.set_focus_child(self.connect_btn)       

        self.disconnect_btn = gtk.Button("Disconnect\nfrom GPRS")
        self.disconnect_btn.connect("clicked", self.disconnect_clicked)
        self.disconnect_btn.set_sensitive(0)
        btn_box.add(self.disconnect_btn)
        
        self.pack_start(btn_box, False, False, 0)

        state_frame = gtk.Frame("GPRS State")

        # IP infos
        state_box = gtk.VBox()
        
        self.IP_box = gtk.VBox()
        self.IP_box.set_border_width(10)
        self.IP_text_view = gtk.TextView()
        self.IP_text_buffer = self.IP_text_view.get_buffer()
        self.IP_text_buffer.set_text("Local IP: %s\nRemote IP: %s\nNameserver: %s" %(
                self.local_ip, self.remote_ip, self.nameserver_ip))
        self.IP_text_view.set_editable(0)                
        self.IP_box.add(self.IP_text_view)
        state_box.add(self.IP_box)       
                 
        self.state_entry = gtk.Entry()
        self.state_entry.set_text("")
        self.state_entry.set_sensitive(0)
        state_box.add(self.state_entry)
        state_frame.add(state_box)
        self.pack_start(state_frame, False, False, 0)

        ## override the focus chain as OM will fire the keyboard 
        ## if a textentry is active
        focusable_widgets = [self.connect_btn, 
            gprs_box] + [self.entry_dict[x] for x in self.entry_dict] + [self.peer_combo] 

        self.show_all()
#        print "time needed to init GPRS Panel = %s" % (time.time() - start_time)
