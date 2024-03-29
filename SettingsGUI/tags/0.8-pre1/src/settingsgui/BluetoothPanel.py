"""
 * BluetoothPanel.py - SettingsGUI - Bluetooth Settings
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
import time
import gtk
import SysFSAccess
from GlobalConfiguration import *
from SysFSAccess import *
from ProcessInterface import *
#from settingsgui.GlobalConfiguration import *
#from settingsgui.SysFSAccess import *
#from settingsgui.ProcessInterface import *

class BluetoothPanel(gtk.VBox):
    """
    Settings for the Bluetooth Module of GTA01
    """
    def __init__(self):
        gtk.VBox.__init__(self, False, 0)
        self.address = ""
        self.scan_for_bt_peers = True
        self.create_notebook_page()
    
    def create_notebook_page(self):
        self.set_border_width(0)

        ## Power State of Bluetooth Module
        cell_frame = gtk.Frame("Bluetooth State")
        upper_box = gtk.HBox()
        upper_box.set_border_width(15)

        # power 
        self.power_state_cbtn = gtk.CheckButton("Powered")
        self.power_state_cbtn.set_sensitive(1)
        self.power_state_cbtn.connect('pressed', \
                        lambda *w: self.power_state_cbtn.set_inconsistent(1))
        self.power_state_cbtn.connect('released', self.toggle_power)
        upper_box.pack_start(self.power_state_cbtn, True, True, 0)

        # discoverability
        self.visible_state_cbtn = gtk.CheckButton("Visible")
        self.visible_state_cbtn.set_sensitive(1)
        #self.visible_state_cbtn.connect('pressed', \
        #                lambda *w: self.visible_state_cbtn.set_inconsistent(1))
        self.visible_state_cbtn.connect('released', \
                            lambda *w: self.visible_state_cbtn.set_active(1))
        upper_box.pack_start(self.visible_state_cbtn, True, True, 0)

        # pand
        self.pand_state_cbtn = gtk.CheckButton("Allow PAN")
        self.pand_state_cbtn.set_sensitive(1)
        self.pand_state_cbtn.connect('pressed', \
                        lambda *w: self.pand_state_cbtn.set_inconsistent(1))
        self.pand_state_cbtn.connect('released', self.toggle_listen_pand)
        upper_box.pack_start(self.pand_state_cbtn, True, True, 0)

        cell_frame.add(upper_box)
        self.pack_start(cell_frame, False, False, 0)

        ## Info on BT state
        info_frame = gtk.Frame("Bluetooth Informations")
        info_box = gtk.VBox()
        info_box.set_border_width(15)
        self.address_label = gtk.Label("Bluetooth Address: %s" % self.get_address())
        self.ip_address_label = gtk.Label("IP Address: %s" % self.get_ip_address())
        info_box.add(self.address_label)
        info_box.add(self.ip_address_label)
        info_frame.add(info_box)
        self.pack_start(info_frame, False, True, 1)


        scan_frame = gtk.Frame("Devices in range")
        scan_frame_box = gtk.VBox()
        scan_frame_box.set_border_width(15)
        (scroll_win, self.tree_view1, self.list_store1) = \
                            self.make_list_view(3, \
                                            ["Name", "Address", "PAN Link"], \
                                                    ["text", "text", "toggle"])
        scan_frame_box.pack_start(scroll_win, True, True, 0)

        # self.add_scan_list_entry
        self.list_store1.append(("Scanning for Peers", "", False))
        self.update_infos()
        self.update_list(None)


        scan_btn_box = gtk.HBox()
        update_btn = gtk.Button("Update\nList")
        update_btn.connect('clicked', self.update_list)
        scan_btn_box.add(update_btn)
        connect_btn = gtk.Button("Connect\n(PAN)")
        connect_btn.connect('clicked', self.connect_to_peer)
        scan_btn_box.add(connect_btn)
        scan_frame_box.pack_start(scan_btn_box, False, True, 0)
        scan_frame.add(scan_frame_box)

        self.pack_start(scan_frame, True, True, 0)

        # settings powerstate as last operation to ensure existence of all 
        # widgets
        if self.get_power_state():
            self.power_state_cbtn.set_active(True)
            self.visible_state_cbtn.set_active(True)
            self.toggle_power(None)
        else:
            self.power_state_cbtn.set_active(False)
            self.visible_state_cbtn.set_active(False)

        ## finish notebook page creation
        self.show_all()

################################################################################
######################### build GUI helper #####################################
################################################################################
    ## we allow one toggle -for fixed (text, text, toggle)
    def make_list_view(self, number, names, type = ["text", "text", "text"]):
        scroll_win = gtk.ScrolledWindow()
        scroll_win.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        #try:
        if type.index("toggle") >= 0:
            list_store = gtk.ListStore(str, str, 'gboolean')#gobject.TYPE_BOOLEAN)
        #except:
            # list_store = gtk.ListStore(*(str,) * number)

        tree_view = gtk.TreeView(list_store)
        cell = gtk.CellRendererText()
        cell.set_property('editable', False)
        cell_toggle = gtk.CellRendererToggle()
        cell_toggle.set_property('activatable', True)

        tvcolumn = []
        for i in range(number):
            if type[i] == "text":
                tvcolumn.append(gtk.TreeViewColumn(names[i], cell, markup=i))
            if type[i] == "toggle":
                toggle_column = gtk.TreeViewColumn(names[i], cell_toggle)
                tvcolumn.append(toggle_column)
                toggle_column.add_attribute(cell_toggle, attribute = "active", \
                                                                    column = 2)
            tree_view.append_column(tvcolumn[i])
            tvcolumn[i].set_sort_column_id(i)
            tvcolumn[i].set_resizable(True)
        
        scroll_win.add(tree_view)
        return (scroll_win, tree_view, list_store)

################################################################################
####################### Callbacks from GUI #####################################
################################################################################
    def toggle_power(self, event):
        print "Toggleing Power state!"
        if not self.get_power_state():
            set_sysfs_value(SYSFS_ENTRY_BLUETOOTH_POWER, 1)
            self.list_store1.append(("Scanning for Peers", "", False))
        else:
            set_sysfs_value(SYSFS_ENTRY_BLUETOOTH_POWER, 0)
        
        if self.power_state_cbtn.get_active() != self.get_power_state():
            self.power_state_cbtn.get_active()

        ## have to wait for async init :-( - TODO - make updates async.
        time.sleep(2)
        self.update_infos()
        self.update_list(None)

        ## for now we are alyways visible when power is on
        self.visible_state_cbtn.set_active(self.get_power_state())

        self.power_state_cbtn.set_inconsistent(0)
 
    def toggle_listen_pand(self, event):
        if self.pand_state_cbtn.get_active():
            print "Starting pand [pand -s]"
            os.system("pand -s")
        else:
            print "pand already listening for connections"
            self.pand_state_cbtn.set_active(1)
        self.pand_state_cbtn.set_inconsistent(0)

    def get_power_state(self):
        state = get_sysfs_value(SYSFS_ENTRY_BLUETOOTH_POWER)[0]
        print "Powerstate is [%s]" %state
        if state.isdigit():
            return int(state)
        else:
            return 0

    def connect_to_peer(self, event):
        
        def call_cmd(string):
            print("calling command [%s]" % string)
            os.system(string)

        ## get selected entry
        if len(self.address) <= 0:
            return
        (model, model_iter) = self.tree_view1.get_selection().get_selected()
        if model_iter >= 1:
            name = model.get_value(model_iter, 0)  # column is first (name)
            addr = model.get_value(model_iter, 1)  # column is second (adr)
            call_cmd("pand -c %s" % addr)
            ## convert last number of addr to decimal and user as last ip number
            call_cmd("ip a add 10.0.0.%s/24 dev bnep0" % \
                                    int(self.address.split(":")[-1], 16))
            ## set main ip of bnep0 (in case a different ip was set)
            call_cmd("ifconfig bnep0 10.0.0.%s" % \
                                    int(self.address.split(":")[-1], 16))
            ## set 10.0.0.1 to default GW - won't work if GW is set already
            call_cmd("ip r add default via 10.0.0.1")
            time.sleep(1)
            self.update_infos()


    def update_list(self, event):
        self.hcitool = ProcessInterface("%s scan" % HCITOOL_CMD)
        self.list_store1.clear()
        self.hcitool.register_event_handler(":", self.add_scan_list_entry)

        pand_list_tool = ProcessInterface("pand -l")
        time.sleep(1)   ## wait for command to compute
        output = pand_list_tool.read_from_process()
        
        self.connected_peers = []
        for line in output.split("\n"):
            if len(line.split(" ")) > 1:
                self.connected_peers.append(line.split(" ")[1])

################################################################################
#################### subprocess callbacks (outputs) ############################
################################################################################

    def add_scan_list_entry(self, string):
        if string.find(":") >= 0:
            print ("new")
            try: 
                self.connected_peers.index(string.strip().split("\t")[0])
                found = True ## we've had no exception
            except:
                found = False
            print ("append: [%s,%s,%s]" % (string.strip().split("\t")[1], \
                                        string.strip().split("\t")[0], found))
            self.list_store1.append((string.strip().split("\t")[1], \
                                        string.strip().split("\t")[0], found))

    def ip_address_changed(self, string):
        # print "output of get_ip_address: [%s]" % string
        if len(string.split("inet addr:")) > 1:
            self.address_label.set_text("Bluetooth Address: %s" % \
                            string.split("inet addr:")[1].split(" ")[0].strip())


    def bt_address_changed(self, string):
        # print "output of get_address: [%s]" % string
        if string.find("BD Address: "):
            if len(string.split("BD Address: ")) > 1 and \
                    len(string.split("BD Address: ")[1].split(" ")) > 1:
                self.address = string.split("BD Address: ")[1].split(" ")[0]
                self.ip_address_label.set_text("Address: %s" % \
                                string.split("BD Address: ")[1].split(" ")[0])
            else:
                self.ip_address_label.set_text("Address: offline")
        self.ip_address_label.set_text("Address: unknown")



################################################################################
####################### Interface to bluez tools ###############################
################################################################################
    def update_infos(self):
        self.address_label.set_text("Bluetooth Address: %s" % self.get_address())
        self.ip_address_label = gtk.Label("IP Address: %s" % self.get_ip_address())

    def get_ip_address(self):
        if len(self.address) <= 0:
            return "none"
        else:    ## todo mind more than one device
            ifconfig = ProcessInterface("ifconfig bnep0")
            time.sleep(1)   ## wait for command to compute
            output = ifconfig.read_from_process()
            # print "output of get_ip_address: [%s]" % output
            if len(output.split("inet addr:")) > 1:
                return output.split("inet addr:")[1].split(" ")[0].strip()

    def get_address(self):
        hciconfig = ProcessInterface("%s %s" % (HCICONFIG_CMD, BLUETOOTH_DEVICE))
        time.sleep(1)   ## wait for command to compute
        output = hciconfig.read_from_process()

        # print "output of get_address: [%s]" % output
        # hciconfig.close_process() ## has no effect anyway :-( TODO - fix
        if output.find("BD Address: "):
            if len(output.split("BD Address: ")) > 1 and \
                    len(output.split("BD Address: ")[1].split(" ")) > 1:
                self.address = output.split("BD Address: ")[1].split(" ")[0]
                return output.split("BD Address: ")[1].split(" ")[0]
            else:
                return "offline"
        return "unknown"

    def get_features(self):
        """using the hciconfig tool to get the list of supported features"""
        
