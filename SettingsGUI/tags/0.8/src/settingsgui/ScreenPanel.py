"""
 * ScreenPanel.py - SettingGUI - Screen Settings Section
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
from SysFSAccess import *
from GlobalConfiguration import * 
#from settingsgui.SysFSAccess import *
#from settingsgui.GlobalConfiguration import * 

class ScreenPanel(gtk.VBox):
    orientation = 0

    def __init__(self):
        gtk.VBox.__init__(self, False, 0)
        self.create_notebook_page()

    def toggle_backlight(self, widget):
        print "trying to toggle the backlight"
        value = get_sysfs_value(SYSFS_ENTRY_BACKLIGHT_POWER)
        if value.find("1") != -1:
            set_sysfs_value(SYSFS_ENTRY_BACKLIGHT_POWER, 0)
            value = "1"
        else:
            set_sysfs_value(SYSFS_ENTRY_BACKLIGHT_POWER, 1)
            value = "0"

    def toggle_orientation(self, widget):
        print "trying to toggle screen orientation"
        if self.orientation == 0:
            os.system("/usr/bin/xrandr -o 1")
            self.orientation = 1
        else:
            os.system("/usr/bin/xrandr -o 0")
            self.orientation = 0
        

    def restart_x_server(self, widget):
        mbox = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, gtk.BUTTONS_YES_NO, 
                    "You hit the Restart-Phone-GUI-Button!\nThis will restart the X11-Server!\nDo you really want to quit ALL applications? (including SettingGUI)")
        response = mbox.run()
        mbox.hide()
        mbox.destroy()   
        if response == gtk.RESPONSE_YES:
            print "SettingsGUI is restarting X11..."
            os.system("/etc/init.d/xserver-nodm restart")


    def bl_level_changed(self, widget):
        tmp_value = widget.value
        tmp_value = tmp_value * 50
        print "trying to set backlight to %s" % tmp_value
        set_sysfs_value(SYSFS_ENTRY_BACKLIGHT_BRIGHTNESS, tmp_value)

    def create_notebook_page(self):
        self.set_border_width(0)

        level_frame = gtk.Frame("Backlight Level")
        level_frame.set_border_width(0)
        level_box = gtk.VBox(False, 0)
        level_box.set_border_width(15)

        init_value = get_sysfs_value(SYSFS_ENTRY_BACKLIGHT_BRIGHTNESS)
        if len(init_value) > 0:
            init_value = float(init_value) / 50
        else:
            init_value = 50
        

        ## scale to set backlight level
        scale_adj = gtk.Adjustment(init_value, 0.0, 100.0, 1.0, 1.0, 0.0)
        scale_adj.connect("value_changed", self.bl_level_changed, )
        backlight_scale = gtk.HScale(scale_adj)
        backlight_scale.set_digits(0)
        level_box.add(backlight_scale)

        level_frame.add(level_box)
        self.pack_start(level_frame, False, False, 0)

        button_box = gtk.HBox(False, 0)
        button_box.set_border_width(0)
        self.add(button_box)        
        
        ## button to restart xserver
        restart_x_btn = gtk.Button("Restart Phone GUI")
        restart_x_btn.connect("clicked", self.restart_x_server)
        # button_box.add(restart_x_btn)
        
        ## button to toggle backlight
        bl_toggle_btn = gtk.Button("Backlight\non/off")
        bl_toggle_btn.connect("clicked", self.toggle_backlight)
        button_box.add(bl_toggle_btn)
        
        ## button to change orientation
        orientation_toggle_btn = gtk.Button("Landscape/\nPortrait")
        orientation_toggle_btn.connect("clicked", self.toggle_orientation)
        button_box.add(orientation_toggle_btn)

        self.show_all()
        ## label to describe notebook page
        label = gtk.Label("Backlight")
        return (self, label)
