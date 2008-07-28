"""
 * SettingsGUI.py - Creating the main window
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

import time
import sys
import gtk
import gobject
import time
import threading
#from settingsgui.GlobalConfiguration import * 
from GlobalConfiguration import * 


battery_image_dir = "/usr/share/settingsgui/battery/"

class ToggleInterface(threading.Thread):
    def __init__(self, settings_gui):
        self.settings_gui = settings_gui
        threading.Thread.__init__(self)
        ## init
        print "INIT THREAD FOR UI"
        self.out_data = []
        self.keep_going = True
        self.start()

    def run(self):
        print "STARTING UI"
        gtk.gdk.threads_init()
        gtk.gdk.threads_enter()
#        if :
#            self.settings_gui.create_UI()

class SettingsGUI:
    def delete_event(self, widget, event, data=None):
        gtk.main_quit()
        print("Waiting for all processes to quit...")
        time.sleep(1.5)
        sys.exit(0)
        return False

    def add_notebook_page(self, panel, icon_name):
        image = gtk.Image()
        image.set_from_icon_name(icon_name, gtk.ICON_SIZE_LARGE_TOOLBAR)
        image.show()
        image_alignment = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=1.0, yscale=1.0)
        image_alignment.add(image)
        image_alignment.set_padding(NOTEBK_PADDING, NOTEBK_PADDING, 0, 0)
        image_alignment.show()
        scroll_win = gtk.ScrolledWindow()
        scroll_win.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scroll_win.show()
        scroll_win.add_with_viewport(panel)
        self.notebook.append_page(scroll_win, image_alignment)

    # do this in an extra method - so init can return faster
    def create_UI(self):
        if self.state != "init-done":
            return

        self.state = "running"
        self.window.remove(self.loading_lbl)
        start_time = self.start_time
        self.window.set_title("SettingsGUI")
        print "0.2: %s" %(time.time() - start_time)

        ## not working from shell - is within package
        #from settingsgui.ScreenPanel import ScreenPanel
        #from settingsgui.AudioPanel import AudioPanel
        #from settingsgui.GSMPanel import GSMPanel
        #from settingsgui.GPRSPanel import GPRSPanel
        #from settingsgui.BluetoothPanel import BluetoothPanel

        from ScreenPanel import ScreenPanel
        from AudioPanel import AudioPanel
        from GSMPanel import GSMPanel
        from GPRSPanel import GPRSPanel
        from BluetoothPanel import BluetoothPanel
        from MofiPanel import MofiPanel
        from BatteryPanel import BatteryPanel


        print "0.3: %s" %(time.time() - start_time)


        self.notebook = gtk.Notebook()
        self.notebook.set_tab_pos(gtk.POS_BOTTOM)

        
        print "1: %s" %(time.time() - start_time)

        self.add_notebook_page(ScreenPanel(), "preferences-desktop-screensaver")
        
        print "2: %s" %(time.time() - start_time)
        
        self.add_notebook_page(AudioPanel(), "moko-speaker")
        print "3: %s" %(time.time() - start_time)
        GSM_Panel = GSMPanel()
        self.add_notebook_page(GSM_Panel, "moko-call-redial")
        print "4: %s" %(time.time() - start_time)
        self.add_notebook_page(GPRSPanel(GSM_Panel), "gtk-network")
        print "5: %s" %(time.time() - start_time)
        self.add_notebook_page(BluetoothPanel(), "gtk-connect")
        print "6: %s" %(time.time() - start_time)
        self.add_notebook_page(MofiPanel(), "gtk-network")
        print "7: %s" %(time.time() - start_time)

        #battery_image = gtk.Image()
        #battery_image.set_from_file(battery_image_dir + "battery.png")
        self.add_notebook_page(BatteryPanel(), "gtk-disconnect")
        print "8: %s" %(time.time() - start_time)

        ## expand page selectors to full width
        for child in self.notebook.get_children():
            self.notebook.child_set_property(child, "tab_expand", True)
        self.notebook.show()
        
        print "9: %s" %(time.time() - start_time)

        #self.main_panel.add(self.notebook)

        txt = gtk.Label("Loading ...")
        self.window.add(self.notebook)

        self.window.show_all()
        #self.window.queue_draw_area(0,0,-1,-1)
        self.window.show()

    def __init__(self):
        self.state = "init"
        start_time = time.time()
        self.start_time = start_time
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_border_width(0)
        self.window.set_default_size(480, 640)
        self.window.connect("delete_event", self.delete_event)
        self.notebook = gtk.Notebook()
        self.state = "init-done"
        # we can't let them wait!
        print "0.1: %s" %(time.time() - start_time)
        self.loading_lbl = gtk.Label("Loading ...")
        self.window.add(self.loading_lbl)
        self.window.show_all()
#        self.window.add(txt)
        #self.main_panel = gtk.VBox()
        #self.main_panel.add(self.notebook)
#        self.notebook.show()
#        self.window.add(self.notebook)
        #interface_thread = ToggleInterface(self)
