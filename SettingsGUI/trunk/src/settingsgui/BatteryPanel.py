
"""
 * BatteryPanel.py - SettingsGUI - Battery Status
 *
 * GUI for battery on Neo Freerunner
 * written by HdR <hdr@meetr.de>
 * battery status icons made by Kore Nordmann <mail@kore-nordmann.de>
 * start icon from tango icons <http://tango.freedesktop.org/Tango_Desktop_Project>
 *
 * ! this script comes with explicit no warranty !
 * License: gpl
 *
 *
 * SettingsGUI is (C) 2007 by Kristian Mueller <kristian-m@kristian-m.de>
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


import gobject,gtk
import os

class BatteryPanel(gtk.VBox):
    charger_type = "/sys/class/i2c-adapter/i2c-0/0-0073/charger_type"
    capacity = "/sys/devices/platform/bq27000-battery.0/power_supply/bat/capacity"
    voltage = "/sys/devices/platform/bq27000-battery.0/power_supply/bat/voltage_now"
    status = "/sys/devices/platform/bq27000-battery.0/power_supply/bat/status"
    image_dir = "/usr/share/settingsgui/battery/"
    usb_limit = "/sys/class/i2c-adapter/i2c-0/0-0073/force_usb_limit_dangerous"
    #charger_type = "charger_type"
    #capacity = "capacity"
    #voltage = "voltage"
    #status = "status"
    #image_dir = "./"

    # Check the current amperage
    def check_type(self):
        self.f = open(self.charger_type, 'r')
        self.type = self.f.readline().rstrip('\n')
        self.f.close()

        try:
         self.current = self.type.split(" ")[3]
        except:
         return False

        if (self.current == '1A'):
         self.amperage = 1000;
        elif (self.current == '500mA'):
         self.amperage = 500;
        elif (self.current == '100mA'):
         self.amperage = 100;
        else:
         self.amperage = False;

        return (self.amperage)

    # Check current battery capacity
    def check_capacity(self):
        try:
            self.f = open(self.capacity, 'r')
            self.q = self.f.readline().rstrip('\n')
        except(IOError):
            print "ERROR: could not read capacity!"
            self.q = "0"
        finally:
            self.f.close()

        # print "q was %s" % self.q
        return (int(self.q))

    # Check current battery voltage
    def check_voltage(self):
        try:
            self.f = open(self.voltage, 'r')
            self.q = float(self.f.readline().rstrip('\n'))
            self.v = int(self.q)/1000000;
        except(IOError):
            print "ERROR: could not read voltage!"
            # self.q = "0"
        finally:
            self.f.close()
        return (self.v)

    # Check current status (Charging/Discharging)
    def check_status(self):
        self.f = open(self.status, 'r')
        self.q = self.f.readline().rstrip('\n')
        self.f.close()
        return(self.q)
   
    # Set the load amperage manually
    def set_charge_limit(self, button, limit):
        if (self.check_type()):
            os.system("echo %d > %s" % (limit,self.usb_limit))
        return True
   
    # Update the capacity label
    def update_capacity(self, label, image):
        cap = self.check_capacity()
        label.set_text ("Battery capacity: %d%%" % cap)
        if (cap <= 5):
            image.set_from_file(self.image_dir+"battery_stat_00.png")
        elif (cap <= 20):
            image.set_from_file(self.image_dir+"battery_stat_11.png")
        elif (cap <= 38):
            image.set_from_file(self.image_dir+"battery_stat_23.png")
        elif (cap <= 56):
            image.set_from_file(self.image_dir+"battery_stat_42.png")
        elif (cap <= 85):
            image.set_from_file(self.image_dir+"battery_stat_64.png")
        else:
            image.set_from_file(self.image_dir+"battery_stat_99.png")
        return True
   
    # Update the charge label
    def update_charge(self, label):
        rate = self.check_type()
        if (rate):
            label.set_text ("Battery charging: %d mA" % rate)
        else: 
            label.set_text ("Battery charging: %s" % self.check_status())
        return True

    def update_voltage(self, label):
        voltage = self.check_voltage()
        label.set_text ("Current voltage: %.2f V" % voltage)
        return True
   
    # Gtk GUI
    def __init__(self):
        # init main window
        #self.win.connect("delete_event", self.delete_event)
        gtk.VBox.__init__(self, False, 0)

        self.v = 0;
        #self.q = 0;


        # add a VBox
        self.vbox = gtk.VBox(homogeneous=False, spacing=5)
        self.add(self.vbox)

        # add a HBox
        self.hbox0 = gtk.HBox()
        self.vbox.pack_start(self.hbox0)
        self.hbox0.show()

        # Add a Image
        self.stat_image = gtk.Image()
        self.stat_image.set_from_file(self.image_dir+"battery_stat_01.png")
        self.hbox0.pack_start(self.stat_image)
        self.stat_image.show()

        # Add a Vbox for info labels
        self.vbox1 = gtk.VBox()
        self.hbox0.pack_start(self.vbox1)
        self.vbox1.show()

        # Add Capacity label
        self.capacity_label = gtk.Label("Battery capacity: checking")
        self.vbox1.pack_start(self.capacity_label)
        self.capacity_label.show()
        gobject.timeout_add (1000, self.update_capacity, self.capacity_label, self.stat_image)

        # Add chargelevel label
        self.charge_label = gtk.Label("Battery charging: checking")
        self.vbox1.pack_start(self.charge_label)
        self.charge_label.show()
        gobject.timeout_add (1000, self.update_charge, self.charge_label)

        # Add voltage label
        self.voltage_label = gtk.Label("Current voltage: checking")
        self.vbox1.pack_start(self.voltage_label)
        self.voltage_label.show()
        gobject.timeout_add (1000, self.update_voltage, self.voltage_label)

        # Add HBox for buttons
        self.hbox1 = gtk.HBox(homogeneous=False, spacing=5)
        self.vbox.pack_start(self.hbox1)
        self.hbox1.show()

        # Add button for 100mA
        self.button_100 = gtk.Button("Charge at\n100mA")
        self.hbox1.pack_start(self.button_100)
        self.button_100.connect("clicked", self.set_charge_limit, 100)
        self.button_100.show()

        # Add button for 500mA
        self.button_500 = gtk.Button("Charge at\n500mA")
        self.hbox1.pack_start(self.button_500)
        self.button_500.connect("clicked", self.set_charge_limit, 500)
        self.button_500.show()

        # add button for 1000mA
        self.button_1000 = gtk.Button("Charge at\n1000mA")
        self.hbox1.pack_start(self.button_1000)
        self.button_1000.connect("clicked", self.set_charge_limit, 1000)
        self.button_1000.show()

        # show main window
        self.show_all()
