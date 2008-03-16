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
import gobject
import SysFSAccess
from GlobalConfiguration import *
from SysFSAccess import *
from ProcessInterface import *


class BluetoothScanner(threading.Thread):
    def __init__(self, update_callback):
        threading.Thread.__init__(self)
        self.keep_running = True
        self.scan_active = False
        self.update_callback = update_callback
        self.start()


    def run(self):
        while (self.keep_running):
            if self.scan_active:
                self.update_callback(self.update_list())
                time.sleep(BLUETOOTH_UPDATE_INTERVAL)   # scan every x seconds
            else:
                time.sleep(2)   # check again if we are active in a second


    def set_active(self, active):
        self.scan_active = active


    def update_list(self):
        ## exec hcitool scan
        hcitool = ProcessInterface("%s scan hci0" % HCITOOL_CMD)
        while not hcitool.process_finished():
            time.sleep(0.1)   ## wait for command to compute
        hcitool_output = hcitool.read_from_process()

        ## exec pand list
        pand = ProcessInterface("pand -l")
        while not pand.process_finished():
            time.sleep(0.1)   ## wait for command to compute
        pand_output = pand.read_from_process()

        ## filter output for  visible peers
        visible_peers = []
        for line in hcitool_output.split("\n"):
            if line.find(":") >= 1:
                visible_peers.append((line.strip().split("\t")[1],\
                                                line.strip().split("\t")[0]))
        ## filter output for connected peers
        connected_peers = []
        for line in pand_output.split("\n"):
            if len(line.split(" ")) > 1:
                connected_peers.append(line.split(" ")[1])

        return (visible_peers, connected_peers)




class BluetoothPanel(gtk.VBox):
    """
    Settings for the Bluetooth Module of GTA01
    """
    def __init__(self):
        gtk.VBox.__init__(self, False, 0)
        self.address = ""
    
        self.create_notebook_page()

        # asyncronous stuff
        self.update_ui_condition = threading.Condition()
        self.scan_for_bt_peers = True       # to be handled in critical section!
        self.async_updated = False          # to be handled in critical section!
        self.visible_peers_backup = []
        self.connected_peers_backup = []

        # creating backgroundscanner - not active by default
        self.bluetooth_scanner = BluetoothScanner(self.update_from_scanner)

        # start our update timer
        gobject.timeout_add(500, self.update_ui) # every 1/2 second
    
        # settings powerstate as last operation to ensure existence of all 
        # widgets
        if self.get_power_state():
            self.power_state_cbtn.set_active(True)
            self.visible_state_cbtn.set_active(True)
            self.update_btn.set_active(True)
            self.list_store1.append(("Scanning for ", "Peers", False))
            self.pand_state_cbtn.set_active(self.get_pand_state())
            self.update_infos()
        else:
            self.power_state_cbtn.set_active(False)
            self.visible_state_cbtn.set_active(False)



    def create_notebook_page(self):
        self.set_border_width(0)

        ## Power State of Bluetooth Module
        cell_frame = gtk.Frame("Bluetooth State")
        upper_box = gtk.HBox()
        upper_box.set_border_width(10)

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
        info_box.set_border_width(10)

        self.name_label = gtk.Label("Visible Name: %s" % self.get_name())
        self.address_label = gtk.Label("Address: %s" % self.get_address())
        self.ip_address_label = gtk.Label("IP: %s" % self.get_ip_address())
        info_box.add(self.name_label)
        info_box.add(self.address_label)
        info_box.add(self.ip_address_label)
        info_frame.add(info_box)
        self.pack_start(info_frame, False, True, 1)


        scan_frame = gtk.Frame("Devices in range")
        scan_frame_box = gtk.VBox()
        scan_frame_box.set_border_width(10)
        (scroll_win, self.tree_view1, self.list_store1) = \
                            self.make_list_view(3, \
                                            ["Name", "Address", "Link"], \
                                                    ["text", "text", "toggle"])
        scan_frame_box.pack_start(scroll_win, True, True, 0)

        scan_btn_box = gtk.HBox()
        self.update_btn = gtk.ToggleButton("Scan for\nPeers")
        self.update_btn.connect('toggled', self.scan_for_peers_toggled)
        scan_btn_box.add(self.update_btn)
        connect_btn = gtk.Button("Connect\n(PAN)")
        connect_btn.connect('clicked', self.connect_to_peer)
        scan_btn_box.add(connect_btn)
        scan_frame_box.pack_start(scan_btn_box, False, True, 0)
        scan_frame.add(scan_frame_box)

        self.pack_start(scan_frame, True, True, 0)

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
######### update GUI from asynchronous changes (from threads) ##################
################################################################################
    def update_ui(self):
        self.update_ui_condition.acquire()  # <- critical section
        if not self.async_updated:          # to be handled in critical section!
            self.update_ui_condition.release()  # -> critical section
            return True                     # Do nothing, keep going
        else:
            self.async_updated = False

        self.list_store1.clear()
        # access the peer_list (which is written to by the scan thread)
        for entry in self.peer_list:        
            self.list_store1.append(entry)

        if len(self.peer_list) <= 0:
            self.list_store1.append(("Scanning for ", "Peers...", False))

        self.update_ui_condition.release()  # -> critical section
        return True                         # keep going for ever

    ## gets calles from thread context - has no access to GUI!
    def update_from_scanner(self, data):
        (visible_peers, connected_peers) = data

        ## this does not need synchronisation yet - only one thread calling
        ## find out if anything has changed since last update
        if self.visible_peers_backup == visible_peers and \
                self.connected_peers_backup == connected_peers:
            return  ## nothing to be done

        self.visible_peers_backup = visible_peers
        self.connected_peers_backup = connected_peers


        self.update_ui_condition.acquire()  # <- critical section
        self.peer_list = []                 # to be handled in critical section!

        for entry in visible_peers:
            ## see if entry can be found in conneced list
            found = False
            for connected in connected_peers:
                print "."
                if entry[1] == connected:
                    found = True
            ## add to list als (Name, Address, Found)
            self.peer_list.append((entry[0], entry[1], found))

        self.async_updated = True           # to be handled in critical section!
        self.update_ui_condition.release()  # -> critical section

################################################################################
####################### Callbacks from GUI #####################################
################################################################################
    def scan_for_peers_toggled(self, event):
        '''
        activate/deactivate background scanner
        '''
        self.bluetooth_scanner.set_active(self.update_btn.get_active())


    def toggle_power(self, event):
        print "Toggleing Power state!"
        if not self.get_power_state():
            set_sysfs_value(SYSFS_ENTRY_BLUETOOTH_POWER, 1)
            self.list_store1.clear()
            self.list_store1.append(("Scanning for ", "Peers...", False))
            self.update_btn.set_active(True)
        else:
            set_sysfs_value(SYSFS_ENTRY_BLUETOOTH_POWER, 0)
        
        self.power_state_cbtn.set_active(self.get_power_state())

        ## have to wait for async init :-( - TODO - make updates async.
        time.sleep(2)
        self.update_infos()

        ## for now we are alyways visible when power is on
        self.visible_state_cbtn.set_active(self.get_power_state())

        self.power_state_cbtn.set_inconsistent(0)
 
    def toggle_listen_pand(self, event):
        if self.pand_state_cbtn.get_active():

#            IP_address = "%s.%s" % (BLUETOOTH_IP_MASK, \
#                                        int(self.address.split(":")[-1], 16))
#            print "setting IP address to [%s]" % IP_address
            


            print "Starting pand [pand -s]"
            os.system("pand -s")
        else:
            print "pand already listening for connections"
            self.pand_state_cbtn.set_active(1)
        self.pand_state_cbtn.set_inconsistent(0)


    def get_power_state(self):
        power_value = get_sysfs_value(SYSFS_ENTRY_BLUETOOTH_POWER)
        
        ## value will be empty if sysfs entry does not exist
        if len(power_value) > 0:
            state = power_value[0]
        else:
            state = "0"

        if state.isdigit():
            if int(state) > 0:
                return True
        return False


    def get_pand_state(self):
        if process_running("pand\0-s") or process_running("pand\0--listen"):
            return True
        else:
            return False


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
            time.sleep(1)   ## time needed to create bnap device
            ## convert last number of addr to decimal and user as last ip number
            call_cmd("ifconfig bnep0 %s%s" % (BLUETOOTH_IP_MASK, \
                                        int(self.address.split(":")[-1], 16)))
            time.sleep(1)   ## time needed to set ip
            self.update_infos()


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

            self.list_store1.append((string.strip().split("\t")[1], \
                                        string.strip().split("\t")[0], found))


################################################################################
####################### Interface to bluez tools ###############################
################################################################################
    def update_infos(self):
        self.name_label.set_text("Visible Name: %s" % self.get_name())
        self.address_label.set_text("Address: %s" % self.get_address())
        self.ip_address_label.set_text("IP: %s" % self.get_ip_address())

    def get_name(self):
        hciconfig = ProcessInterface("hciconfig hci0 name")
        while not hciconfig.process_finished():
            time.sleep(0.1)   ## wait for command to compute
        output = hciconfig.read_from_process()
        if output.find("Name:") >= 0:
            return output.split("Name:")[1].split("'")[1]
        return "down"


    def get_address(self):
        hciconfig = ProcessInterface("%s %s" % (HCICONFIG_CMD, BLUETOOTH_DEVICE))
        while not hciconfig.process_finished():
            time.sleep(0.1)   ## wait for command to compute
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


    def get_ip_address(self):
        if len(self.address) <= 0:
            return "none"
        else:    ## todo mind more than one device
            ifconfig = ProcessInterface("ifconfig bnep0")
            while not ifconfig.process_finished():
                time.sleep(0.1)   ## wait for command to compute
            output = ifconfig.read_from_process()
            # print "output of get_ip_address: [%s]" % output
            if len(output.split("inet addr:")) > 1:
                return output.split("inet addr:")[1].split(" ")[0].strip()

    def get_features(self):
        """using the hciconfig tool to get the list of supported features"""
        
