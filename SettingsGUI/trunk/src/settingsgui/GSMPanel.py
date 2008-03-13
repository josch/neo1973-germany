"""
 * GSMPanel.py - SettingsGUI - GSM Settings
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

import sys
import os
import threading
import time
import gtk
# import gobject 

from ProcessInterface import *
from SysFSAccess import *
from GlobalConfiguration import * 
#from settingsgui.ProcessInterface import *
#from settingsgui.SysFSAccess import *
#from settingsgui.GlobalConfiguration import * 


MAX_SIGNAL = 30.0
LIBGSM_TOOL = "/usr/bin/libgsmd-tool"
PATH_TO_LIBGSM_TOOL = "/usr/bin/"
GSMD_INIT = "/etc/init.d/gsmd"
SYSFS_ENTRY_GSM_POWER = "/sys/bus/platform/devices/gta01-pm-gsm.0/power_on"

class GSMPanel(gtk.VBox):
    def __init__(self):
        gtk.VBox.__init__(self, False, 0)
        self.create_notebook_page()
        gtk.gdk.threads_init()
        self.gsm_state = 0
        self.start_gsm_tool()


    def __del__(self):
        try: 
            self.gsm_tool_at.write_to_process("\d") ## EOF!
        except:
            print "GSMPanel: Warning: gsmtool seems to be closed already"
        time.sleep(0.3)


    def start_gsm_tool(self):
        if os.path.exists(LIBGSM_TOOL):
            self.gsm_tool_at = ProcessInterface(
                                                "%s -m atcmd" % LIBGSM_TOOL)
            time.sleep(0.2)
            error_out = self.gsm_tool_at.read_error_from_process()
            if len(error_out) > 0:
                error_out = error_out.rstrip('\n').lstrip('\n').rstrip(
                                                            '\r').lstrip('\r')
                self.update_state("error libgsm-tool: %s" % error_out)
                print "error libgsm-tool: %s" % error_out
                self.state_changed("Off")
                return False

            self.gsm_tool_at.register_event_handler("RSTR=",\
                                                        self.at_state_changed)
            time.sleep(0.3)

            ## request regestration state
            self.gsm_tool_at.write_to_process("AT+CREG?")

            self.gsm_tool_at.register_event_handler("EVENT: Signal Quality",\
                                                    self.link_quality_changed)
            self.gsm_tool_at.register_event_handler("EVENT: Netreg registered",\
                                             self.network_registration_changed)
            self.gsm_tool_at.register_event_handler("EVENT: Signal Quality",\
                                                    self.link_quality_changed)
            self.gsm_tool_at.register_event_handler("# Power-On",\
                                                            self.state_changed)
            self.gsm_tool_at.register_event_handler("# Register",\
                                                            self.state_changed)
            self.gsm_tool_at.register_event_handler("", self.update_output)
            self.gsm_tool_at.register_event_handler("Our current operator is",\
                                                         self.operator_changed)
            self.gsm_tool_at.register_event_handler("ERROR reading from gsm_fd",\
                                                         self.gsm_fs_changed)
            self.state_changed("Init")

            return True
        else:
            self.update_state("%s not found, most functions in the GSM panel disabled" % LIBGSM_TOOL)
            self.gsm_tool_at = False
        return False


    def check_pppd_running(self):
        if not os.path.exists("/proc"):
            return False
        for key in os.listdir("/proc"):
            if key.replace("/proc/", ""):
                if key.isdigit():
                    fd = open(os.path.join("/proc/", key, "cmdline"))
                    if fd.read().find("pppd") >= 0:
                        return True
        return False

################################################################################
######### Callbacks from libgsmd-tool subprocess output - as callbacks #########
################################################################################

    def update_gsmd_state(self):
        None

    def update_output(self, string):
        ## remove tailing and starting \n and \r - just in case 
        string =  string.rstrip('\n').lstrip('\n').rstrip('\r').lstrip('\r')
        print "libgsmd-tool: <%s>" % string
        self.update_state(string)
        self.update_gsmd_state()
   
    def gsm_fs_changed(self, string):
        self.state_changed("Off")
   
    ## called from gsmd at answer
    def at_state_changed(self, string):
        if string.find("RSTR=") < 0 or string.find(":") < 0\
                                                        or string.find("`") < 0:
            if string.find("OK") >= 0:
                if self.gsm_state == 1:
                    self.state_changed("Power-On")        
                time.sleep(1)
                self.gsm_tool_at.write_to_process("AT+COPS?") ## request oper. name
                time.sleep(1)
                self.gsm_tool_at.write_to_process("AT+CSQ") ## request sign. qual.
            else:
                return False
            return True

        response = string.split("`")[1].rstrip("'")
        cmd = response.split(":")[0]        
        resp = response.split(":")[1].split(",")
        resp = [x.rstrip("\n").rstrip("'").rstrip("\"").lstrip("\"") for x in resp]

        print "got a response from modem: CMD: %s Response: %s" %(cmd, resp)

        ## set location area code and cellid        
        if string.find("+CREG") >= 0:
            if len(resp) == 3:
                location_area = resp[1]
                cell_id = resp[2]
            if len(resp) >= 4:
                location_area = resp[2]
                cell_id = resp[3]           
            if len(resp) >= 3:
                self.reg_state_cbtn.set_active(1)
                self.connected_state_cbtn.set_active(1)
                self.state_changed("Connected")
            else:
                location_area = ""
                cell_id = ""
                self.state_changed("Init")
                
            print "Got a location: %s/%s" % (location_area, cell_id)
            self.area_code_lbl.set_text("Location Area Code: %s" % location_area) 
            self.cell_id_lbl.set_text("Cell ID: %s" % cell_id)        
            if len(resp) >= 2:  # it should always be
                if resp[0] == 0:
                    self.reg_state_cbtn.set_active(0)
                    self.connected_state_cbtn.set_active(0)
                if resp[1] == 0 or resp[1] == 2 or resp[1] == 3:
                    self.connected_state_cbtn.set_active(0)
                if resp[1] == 5 or resp[1] == 1:
                    self.reg_state_cbtn.set_active(1)
                    self.connected_state_cbtn.set_active(1)


        if string.find("+COPS") >= 0:
            if len(resp) >= 3:
                self.operator_lbl.set_text("Operator: %s" % resp[2])
            """
            else:
                if len(resp) == 1:
                    time.sleep(3)
                    ## request oper. name
                    self.gsm_tool_at.write_to_process("AT+COPS?")
                    time.sleep(1)
                    ## request sign. qual.
                    self.gsm_tool_at.write_to_process("AT+CSQ") 
            """
                

        if string.find("+CSQ") >= 0:
            if len(resp) >= 2:
                self.link_quality_changed("%s %s %s %s" % \
                            (resp[0], resp[0], resp[0], resp[0], ))


        ## set opername - ToDo                        
                        
    ## called from gsmd event
    def link_quality_changed(self, line):
        ## ToDo - strange - maybe filter the '#'???
        try: 
            quality = int(line.split(" ")[4])
        except:
            quality = int(line.split(" ")[3])  
        if quality != 99:          
            self.scale_adj.value = int((quality / MAX_SIGNAL) * 100)
            self.sig_stength_scale.set_text("%3.4s %%" % ((quality / MAX_SIGNAL) * 100))

    ## called from gsmd event
    ## ToDo - remove strange string-list-join-thing
    def operator_changed(self, line):
        line_list = line.split(" ")
        operator = " ".join([line_list[x+4] for x in range(len(line_list)-4)])
        self.operator_lbl.set_text("Operator: %s" % operator.rstrip('\n'))

    ## called from gsmd event
    ## requesting name of operator
    def network_registration_changed(self, line):
        if len(line.split()) >= 11:
            location_area = line.split()[7]
            cell_id = line.split()[10]
        else:
            location_area = ""
            cell_id = ""
        
        self.area_code_lbl.set_text("Location Area Code: %s"%location_area) 
        self.cell_id_lbl.set_text("Cell ID: %s" % cell_id)        
        if cell_id != "?":
            print "setting connected - cell_id=%s" % cell_id
            self.state_changed("Connected")
            self.operator_lbl.set_text("Operator: ")

        
    ## called from gsmd event
    def state_changed(self, line):
        self.gsm_state = 0
        if line.find("Init") >= 0:
            self.gsm_state = 1
        if line.find("Power-On") >= 0:
            self.gsm_state = 2
        if line.find("Register") >= 0:
            self.gsm_state = 3
        if line.find("Connected") >= 0:            
            self.gsm_tool_at.write_to_process("AT+COPS?") ## request oper. name
            time.sleep(1)
            self.gsm_tool_at.write_to_process("AT+CSQ") ## request sign. qual.
            self.gsm_state = 4

        ## may flicker
        self.lib_state_cbtn.set_active(0)

        self.power_state_cbtn.set_active(0)
        self.power_state_cbtn.set_sensitive(0)
        self.power_state_cbtn.set_inconsistent(0)

        self.reg_state_cbtn.set_active(0)
        self.reg_state_cbtn.set_sensitive(0)
        self.reg_state_cbtn.set_inconsistent(0)

        self.connected_state_cbtn.set_active(0)

        self.sig_stength_scale.set_text("Invalid")

        ## nothing
        if self.gsm_state == 0:
            self.start_gsmd_btn.set_sensitive(1)
            self.start_gsmd_btn.set_sensitive(1)
            self.stop_gsmd_btn.set_sensitive(0)

        ## init lib
        if self.gsm_state > 0:
            self.lib_state_cbtn.set_active(1)
            self.power_state_cbtn.set_sensitive(1)
            self.start_gsmd_btn.set_sensitive(0)
            self.stop_gsmd_btn.set_sensitive(1)
            
        ## power
        if self.gsm_state > 1:
            self.power_state_cbtn.set_active(1)
            self.reg_state_cbtn.set_sensitive(1)
        
        ## register
        if self.gsm_state > 2:
            self.reg_state_cbtn.set_active(1)
        
        ## connected
        if self.gsm_state > 3:
            self.connected_state_cbtn.set_active(1)



################################################################################
############################## Callbacks from UI ###############################
################################################################################
    
    def power_cb_changed(self, widget):
        widget.set_inconsistent(1)
        if widget.get_active():
            ## power on modem
            print "sending power-on request to modem"        
            self.gsm_tool_at.write_to_process("AT+CFUN=1") 

    def register_cb_changed(self, widget):
        widget.set_inconsistent(1)
        if widget.get_active():
            print "sending register request to modem"
            self.gsm_tool_at.write_to_process("AT+COPS=0")

    def stop_gsmd(self, widget):
        os.popen("start-stop-daemon --stop -x /usr/sbin/gsmd")
        time.sleep(2)   ## libgsmd-tool will flush some outdated data
        self.start_gsmd_btn.set_sensitive(1)
        self.stop_gsmd_btn.set_sensitive(0)
        self.state_changed("Off")


    def start_gsmd(self, widget):
        # restart not working yet - using stop and start
        if self.check_pppd_running():
            mbox = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, gtk.BUTTONS_YES_NO, 
                        "There seems to be a GPRS connection runnung.\nDo you want to close it?")
            response = mbox.run()
            mbox.hide()
            mbox.destroy()   
            if response == gtk.RESPONSE_YES:
                print "will terminate pppd"
                os.system("start-stop-daemon --stop -x %s" % (PPP_INIT))

        os.system("%s stop" %(GSMD_INIT))
        print "executing: %s start" %(GSMD_INIT)
        os.system("%s start" %(GSMD_INIT))
        time.sleep(0.5)
        self.link_quality_changed("0 0 0 0 0")
        self.network_registration_changed("? ? ? ? ? ? ? ? ? ? ?")
        self.start_gsmd_btn.set_sensitive(0)
        self.stop_gsmd_btn.set_sensitive(1)
        time.sleep(1)   ## give the gsmd some time to init... :-/
        self.reinit_libgsmd_tool(None)

    def reinit_libgsmd_tool(self, widget):
        if not self.start_gsm_tool():
            print "error starting gsm-tool - abort reinit"
            return
        self.link_quality_changed("0 0 0 0 0")
        self.network_registration_changed("? ? ? ? ? ? ? ? ? ? ?")
        self.state_changed("Init")
        self.operator_changed("? ? ? ? ?")

    def get_cur_sig_strength(self):
        # ToDo - parse everything!
        return 0   #ToDo

    
    ## change output on "state bar"
    def update_state(self, string):
        self.state_entry.set_text(string)


    def create_notebook_page(self):
        self.set_border_width(0)

        top_btn_box = gtk.HBox(False, 0)
        self.start_gsmd_btn = gtk.Button("Start\ngsmd")
        self.start_gsmd_btn.connect("clicked", self.start_gsmd)
        top_btn_box.add(self.start_gsmd_btn)

        self.stop_gsmd_btn = gtk.Button("Stop\ngsmd")
        self.stop_gsmd_btn.connect("clicked", self.stop_gsmd)
        top_btn_box.add(self.stop_gsmd_btn)

        self.pack_start(top_btn_box, False, False, 0)

        # signal Quality
        frame = gtk.Frame("Signal Stength")
        box = gtk.VBox()
        box.set_border_width(15)

        self.scale_adj = gtk.Adjustment(self.get_cur_sig_strength(), 0.0, 
                                                           100, 1.0, 1.0, 0.0)
        self.sig_stength_scale = gtk.ProgressBar(self.scale_adj)
        self.sig_stength_scale.set_text("0.0 %")
        box.add(self.sig_stength_scale)
        frame.add(box)
        self.pack_start(frame, False, False, 1)

        # cell info
        cell_frame = gtk.Frame("Cell Information")
        cell_box = gtk.VBox()
        cell_box.set_border_width(15)

        self.area_code_lbl = gtk.Label("Location Area Code: ?")
        cell_box.add(self.area_code_lbl)

        self.cell_id_lbl = gtk.Label("Cell ID: ?")
        cell_box.add(self.cell_id_lbl)

        self.operator_lbl = gtk.Label("Operator: ?")
        cell_box.add(self.operator_lbl)

        cell_frame.add(cell_box)
        self.pack_start(cell_frame, False, False, 0)

        # state
        state_frame = gtk.Frame("GSM State")
        state_box = gtk.HBox()
        state_box1 = gtk.VBox()
        state_box2 = gtk.VBox()
        state_box.set_border_width(15)

        self.lib_state_cbtn = gtk.CheckButton("Init")
        self.lib_state_cbtn.set_sensitive(1)
        self.lib_state_cbtn.connect("released", self.reinit_libgsmd_tool)
        state_box1.add(self.lib_state_cbtn)
        self.power_state_cbtn = gtk.CheckButton("Power")
        self.power_state_cbtn.set_sensitive(1)
        self.power_state_cbtn.connect("released", self.power_cb_changed)
        state_box1.add(self.power_state_cbtn)
        self.reg_state_cbtn = gtk.CheckButton("Register")
        self.reg_state_cbtn.set_sensitive(1)
        self.reg_state_cbtn.connect("released", self.register_cb_changed)
        state_box2.add(self.reg_state_cbtn)
        self.connected_state_cbtn = gtk.CheckButton("Connected")
        self.connected_state_cbtn.set_sensitive(0)
        state_box2.add(self.connected_state_cbtn)

        state_box.add(state_box1)
        state_box.add(state_box2)
        state_frame.add(state_box)
        self.pack_start(state_frame, False, False, 0)
        
        
        state_bar_box = gtk.VBox()
        self.state_entry = gtk.Entry()
        self.state_entry.set_text("")
        self.state_entry.set_sensitive(0)
        state_bar_box.add(self.state_entry)
        self.pack_start(state_bar_box, False, False, 0)
        
        self.show_all()        
