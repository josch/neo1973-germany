"""
 * MofiPanel.py - SettingsGUI - Wireless AP Connection Settings
 *
 * Added and programmed by John Beaven <johnbeaven@users.sourceforge.net>
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
import gtk

from settingsgui.pythonwifi.iwlibs import Wireless, getNICnames
from ConfigParser import *
import os
import subprocess

class MofiPanel(gtk.VBox):
    def __init__(self):
        
        gtk.VBox.__init__(self, False, 0)
        
        self.config = ConfigParser()
        self.config.read(os.path.join(os.environ['HOME'], '.mofi.conf'))
        
        self.ap_ui = {}
        
        self.create_notebook_page()
        
    def get_aps(self):
        
        found_aps = {}
        
        # search for accesspoints the interfaces can access..
        # and show list of connections to user..
        for ifname in getNICnames():
            
            wifi = Wireless(ifname)
            essid = wifi.getEssid()
            
            try:
                wifi.scan()
            except(RuntimeError):
                print "could not scan for WiFi networks, may need root permission"
                return []

            for results in wifi.scan():
                
                enc_type = "unknown"
                
                # seems encryption [0x0,0x0,0x0,0x8] is WPA, [0x0,0x0,0x0,0x80] is open
                enc = map(lambda x: hex(ord(x)), results.encode)
                    
                if enc[3] == '0x80':
                    enc_type = "open"
                elif  enc[3] == '0x8':
                    enc_type = "WPA"
                    
                # see if we have a config setting for this essid..
                password = ''
                if self.config.has_option(results.essid, 'password'):
                    password = str(self.config.get(results.essid, 'password'))
                    
                #print "ESSID:", results.essid
                #print "PASSWORD:", password
                #print "Access point:", results.bssid
                #print "Mode:", results.mode
                #if len(results.rate) > 0:
                #    print "Highest Bitrate:", results.rate[len(results.rate)-1]
                #print "Quality: Quality ", results.quality.quality, "Signal ", results.quality.getSignallevel(), " Noise ", results.quality.getNoiselevel()
                    
                found_aps[results.essid] = {'essid':results.essid, 'enc':enc_type, 'password':password, 'connected': (essid == results.essid)}
                    
            return found_aps
                
    def generate_wpa_supplicant(self, pref = []):
        
        found_aps = self.get_aps()
            
        print 'generating wpa_supplicant configuration'
        
        prefered_order = pref
        
        if self.config.has_option('DEFAULT', 'prefered_order'):
            prefered_order += str(self.config.get('DEFAULT', 'prefered_order')).split(',')
            
        # generate wpa_supplicant.conf from retrieved data..
        # if we have no pass, just assume open network..
        wpa_conf = """#NOTE: this file is overwritten by mofi - do not edit!
ctrl_interface=/var/run/wpa_supplicant
eapol_version=1
ap_scan=1
"""

        # prioritise aps in prefered_order from conf..
        for aps in prefered_order:
            
            if aps in found_aps:
                
                wpa_conf += """
network={
       ssid="%s"
       scan_ssid=1
       key_mgmt=WPA-PSK
       pairwise=CCMP TKIP
       group=TKIP CCMP
       psk="%s"
       priority=10
}""" %(aps, found_aps[aps]['password'])
                
                del found_aps[aps]

        # finally gen open connections for remaining aps..
        for aps in found_aps:
            
            wpa_conf += """
network={
       ssid="%s"
       key_mgmt=NONE
       priority=5
}""" %(aps)
                

        # save config to file
        FILE = open(os.path.join(os.environ['HOME'], 'mofi_wpa_supplicant.conf'),"w")
        FILE.write(wpa_conf)
        FILE.close()


    def create_notebook_page(self):
    	
    	# nasty nasty gui - sorry, I'm in a hurry!
        
        for child in self.get_children():
            self.remove(child)
        
        aps = self.get_aps()
        self.last_aps = aps
        
        button_scan = gtk.Button("Scan (update)")
        
        def scan_update(caller):
            self.create_notebook_page()
            
        button_scan.connect("clicked", scan_update)
        
        grpAps = None
        
        for essid in aps:

            # handle hidden Network names
            if '\x00' in essid:
                hidden_essid = essid.replace("\x00", "*")
                radio = gtk.RadioButton(grpAps, "%s (%s)" \
                                            %(hidden_essid,aps[essid]['enc']))                
            else:
                radio = gtk.RadioButton(grpAps, "%s (%s)"%(essid,aps[essid]['enc']))

            radio.set_active(aps[essid]['connected']);
            grpAps = radio
                
            connected_str = ''
            if aps[essid]['connected']:
                connected_str = 'connected, '
                
            self.ap_ui[essid] = radio
            
        self.passbox = gtk.HBox()
        self.passbox.add(gtk.Label('Password:'))
        self.password = gtk.Entry()
        self.passbox.add(self.password)
        button_save = gtk.Button("save")
        def on_save(caller):
            if not self.config.has_section(self.connecting_to):
                self.config.add_section(self.connecting_to)
            self.config.set(self.connecting_to, 'password', self.password.get_text())
            FILE = open(os.path.join(os.environ['HOME'], '.mofi.conf'),"w")
            self.config.write(FILE)
            FILE.close()
            self.last_aps[self.connecting_to]['password'] = self.password.get_text()
            self.button_connect.show()
            self.passbox.hide()
            connect_selected(caller)
                
        button_save.connect("clicked", on_save)
        self.passbox.add(button_save)
            
        
        def connect_selected(caller):
            for essid in self.ap_ui:
                if self.ap_ui[essid].get_active():
                    
                    self.connecting_to = essid
                    
                    l.set_text('')
                    
                    #make sure we have a password for the AP..
                    if self.last_aps[essid]['enc'] == 'WPA' and self.last_aps[essid]['password'] == '':
                        
                        print 'get the password..'
                        self.password.set_text(self.last_aps[essid]['password'])
                        self.button_connect.hide()
                        self.passbox.show()
                        return
                    
                    self.generate_wpa_supplicant([essid])
                    
                    # call our connection shell script and capture the output..
                    proc = subprocess.Popen([r"sh", "./connect.sh"], stdout=subprocess.PIPE)
                    proc.wait()
                    output = proc.stdout.read()
                    
                    print "out: "+output
                    l.set_text(output)
                    
                    return
        
        self.button_connect = gtk.Button("Connect to selected")
        self.button_connect.connect("clicked", connect_selected)
    
        l = gtk.Label('')
        l.set_line_wrap(True)
            
            
        self.pack_start(button_scan, False, False, 2)
        for essid in self.ap_ui:
            self.pack_start(self.ap_ui[essid], False, False, 2)
        self.pack_start(self.button_connect, False, False, 2)
        self.pack_start(self.passbox, False, False, 2)
        self.pack_start(l, False, False, 2)
        
        self.show_all()
        self.passbox.hide()
        
        
