#!/usr/bin/python
# -*- coding: utf-8 -*-

# unit_converter - Converts between different units

import pygtk
pygtk.require('2.0')
import gtk
from lxml import etree
from StringIO import StringIO

unitfile = 'unit.xml'
file = etree.parse(unitfile) #parse the xml file

class unitconvert(object):

    def delete_event(self, widget, event, data=None):
        return False

    def destroy(self, widget, data=None):
        gtk.main_quit()

    def on_catcombo_changed(self, widget):
        self.create_menu()

    def categorymenu(self): # creates the data for the category menu from the xml file
        category = []
        for categoryname in file.findall('//category'): # browses through the elements in the file
                category.append(categoryname.get('name')) # append the name to the category list
        return category

    def unitmenu(self): # creates the data for the unit menu
        unit = []
        category_set = self.catcombo.get_active_text() # checks for the active category to add this units
        for categorynames in file.findall('//category'): # search the categorys
            if categorynames.get('name') == category_set: # search through the file according to the set category
                for units in categorynames.getchildren(): # get the units from the specific category
                    unit.append(units.get('name')) # appends the units from the category into the unit list
        return unit 
    
    def create_menu(self): # fill the gui with the data from categorymenu and unitmenu

        if self.catcombo.get_active_text() == None: # if no category menu exists
            for categorys in self.categorymenu():
                self.catcombo.append_text(categorys) # append the categorys to the menu
        
        modelfrom = self.fromcombo.get_model() # get the data from the fromcombo field ...
        modelfrom.clear() # ... and delete them for the new data 
        modelto = self.tocombo.get_model() # the same as fromcombo
        modelto.clear()

        for units in self.unitmenu():
            self.fromcombo.append_text(units) # filling the unit menus
            self.tocombo.append_text(units)

    def convert(self, widget):

        category_set = self.catcombo.get_active_text()
        unit2 = self.tocombo.get_active_text()
        unit1 = self.fromcombo.get_active_text()
        number = float(self.fromentry.get_text().replace(',','.')) # save the number as a float object and replace the commas with dots for the internal calculation
        fromref = ''
        toref = ''
        for categorynames in file.findall('//category'): # search the categorys
            if categorynames.get('name') == category_set: # search through the file according to the set category
                for units in categorynames.getchildren(): # get the units from the specific category
                    if units.get('name') == unit1: # the name from the unit in the category musst set in the to field 
                        toref =  units.get('to_ref') # search in this unit for the to_ref formular
                    if units.get('name') == unit2: # the same as above only with the from field
                        fromref = units.get('from_ref')
        
        result = eval(toref) # execute the formular in the toref field and safe it to result
        endresult = eval(fromref) # the same as above
        printresult = str(endresult).replace('.',',') # for the better readability replace the dot with a comma
        self.toentry.set_text(printresult) # sets the result into the to field
        
    def clear(self, widget): # clears the entry fields
        self.fromentry.set_text('')
        self.toentry.set_text('')

    def __init__(self):
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_size_request(480,640)
        self.window.set_title('Unit Converter')
        self.window.connect('delete_event', self.delete_event)
        self.window.connect('destroy', self.destroy)
        
# create a box in the dimensions of the window and add it to them        
        self.box = gtk.VBox(False,2)
        self.window.add(self.box)
        
# create a Hbox for the category and add them to self.box
        self.catbox = gtk.HBox(True,2)

# frame for the category box    
        self.catframe = gtk.Frame('Category')
        self.box.pack_start(self.catframe, False, False, 0)

# a combobox for the categorys
        self.catcombo = gtk.combo_box_new_text()
        self.catcombo.connect('changed', self.on_catcombo_changed)
        self.catbox.pack_start(self.catcombo, False, False, 0)
        self.catframe.add(self.catbox)
#create a vbox for the From units
        self.frombox = gtk.VBox(False,2)

#frame for the from box
        self.fromframe = gtk.Frame('Convert from ...')
        self.box.pack_start(self.fromframe, False, False, 0)
        self.fromframe.add(self.frombox)

#create a entry for the 'Convert from' field    
        self.fromentry = gtk.Entry()
        self.fromentry.set_text('Convert from ...')
        self.frombox.pack_start(self.fromentry, False, False, 0)

#a combobox for the from unit
        self.fromcombo = gtk.combo_box_new_text()
        self.frombox.pack_start(self.fromcombo, False, False, 0)

#create a vbox for the To units
        self.tobox = gtk.VBox(False,2)

#frame for the to box
        self.toframe = gtk.Frame('Convert to ...')
        self.box.pack_start(self.toframe, False, False, 0)
        self.toframe.add(self.tobox)

#create a entry for the 'Convert to' field
        self.toentry = gtk.Entry()
        self.toentry.set_text('Convert to ...')
        self.tobox.pack_start(self.toentry, False, False, 0)   

#a combobox for the to unit
        self.tocombo = gtk.combo_box_new_text()
        self.tobox.pack_start(self.tocombo, False, False , 0)

#create a box for the go and clear button
        self.sendbox = gtk.HBox(True,2)
        self.box.pack_end(self.sendbox, False, False, 0)

        self.gobutton = gtk.Button('Go')
        self.sendbox.pack_start(self.gobutton, False, False, 0)
        self.gobutton.connect('clicked', self.convert)
        
        self.clearbutton = gtk.Button('Clear')
        self.sendbox.pack_start(self.clearbutton, False, False, 0)
        self.clearbutton.connect('clicked', self.clear)

# Display all elements
        self.box.show()
        self.catbox.show()
        self.catcombo.show()
        self.catframe.show()
        self.fromentry.show()
        self.fromcombo.show()
        self.fromframe.show()
        self.frombox.show()
        self.toentry.show()
        self.tocombo.show()
        self.toframe.show()
        self.tobox.show()
        self.sendbox.show()
        self.clearbutton.show()
        self.gobutton.show() 
        self.window.show()

def main():
    gtk.main()
    return 0

if __name__ == '__main__':
    unitconvert().create_menu()
    main()
