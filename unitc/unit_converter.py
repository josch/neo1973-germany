#!/usr/bin/python
# -*- coding: utf-8 -*-

# unit_converter - Converts between different units
# version 0.1
# 2008/02/13
# by Patrick Beck

import pygtk
pygtk.require('2.0')
import gtk
import xml.dom.minidom
from sys import exit

try:
    unitfile = 'unit.xml' # path to the unit file
    file = xml.dom.minidom.parse(unitfile) # parse the xml file
except:
    print 'The unitfile can not be opened or found'
    exit()

class unitconvert(object):

    toactive = 0 # status variable will be set to 1, when the 'to' field is the last activated field
    fromactive = 0 # the same, only for the 'from' field

    def delete_event(self, widget, event, data=None):
        return False

    def destroy(self, widget, data=None):
        gtk.main_quit()

    def fromentry_changed(self, widget):
        self.fromactive = 1
        self.toactive = 0

    def toentry_changed(self, widget):
        self.toactive = 1
        self.fromactive = 0

    def on_catcombo_changed(self, widget):
        self.create_menu()
    
    def category_isset(self): # get the selected category
        categoryname = self.catcombo.get_active_text()
        return categoryname

    def unit_from_isset(self): # get the selected unit from the 'from' field
        unit_from = self.fromcombo.get_active_text()
        return unit_from

    def unit_to_isset(self): # get the selected unit from the 'to' field
        unit_to = self.tocombo.get_active_text()
        return unit_to

    def number_from_isset(self): # get the data from the 'from' entry field 
        getnumber_from = self.fromentry.get_text()
        try: # Test if the entry is a number
            number_from = float(getnumber_from.replace(',','.')) # replace the comma with a dot for the internal calculation
            return number_from
        except:
            return 'nonnumber'

    def number_to_isset(self): # get the data for the 'to' entry field
        getnumber_to = self.toentry.get_text()
        try: # Test if the entry is a number
            number_to = float(getnumber_to.replace(',','.'))
            return number_to
        except:
            return 'nonnumber'
    
    def fromentry_set(self, printresult): # sets the result in the target field
        self.fromentry.set_text(printresult)

    def toentry_set(self, printresult): # the same as above
        self.toentry.set_text(printresult)

    def categorymenu(self): # creates the data for the category menu from the xml file
        category = []
        for categoryname in file.getElementsByTagName('category'): # browses through the elements in the file
                category.append(categoryname.getAttribute('name')) # append the name to the category list
        return category

    def unitmenu(self): # creates the data for the unit menu
        unit = []
        set_category = self.category_isset() # checks for the active category to add this units
        for categorynames in file.getElementsByTagName('category'): # search the categorys
            if categorynames.getAttribute('name') == set_category: # search through the file according to the set category
                for units in categorynames.getElementsByTagName('unit'): # get the units from the specific category
                    unit.append(units.getAttribute('name')) # appends the units from the category into the unit list
        return unit 
    
    def create_menu(self): # fill the gui with the data from categorymenu and unitmenu

        if self.category_isset() == None: # if no category menu exists
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
        
        category_isset = self.category_isset() # get the active category from the gui
        unit_to = self.unit_to_isset() # gets the active unit from the 'to' field
        unit_from = self.unit_from_isset() # gets the same for the 'from' field

        # a few tests for the inputs in the combo and entry field        
        if category_isset == None:
            self.fromentry_set('Choose a category')
            self.toentry_set('and the units')
        
        elif unit_from == None and unit_to == None:
            self.fromentry_set('Choose a unit')
            self.toentry_set('Choose a unit')

        elif unit_from == None:
            self.fromentry_set('Choose a unit')
            self.toentry_set('')
        
        elif unit_to == None:
            self.toentry_set('Choose a unit')
            self.fromentry_set('')

        # when the inputs are ok excecute the rest of the program
        else:

            if self.toactive == 1:
                number = self.number_to_isset()
                if number == 'nonnumber': # when the entry is not a number print a error
                    self.toentry_set('Error - put in a number')
            
                else:
                    for categorynames in file.getElementsByTagName('category'): # search the categorys
                        if categorynames.getAttribute('name') == category_isset: # search through the file according to the set category
                            for units in categorynames.getElementsByTagName('unit'): # get the units from the specific category
                                if units.getAttribute('name') == unit_from: # the name from the unit in the category musst set in the to field 
                                    if self.fromactive == 1: # when active gets the to_ref field
                                        toref =  units.getAttribute('to_ref')
                                    else:
                                        fromref = units.getAttribute('from_ref') # else the from_ref field
                                if units.getAttribute('name') == unit_to: 
                                    if self.fromactive == 1: 
                                        fromref = units.getAttribute('from_ref')
                                    else:
                                        toref = units.getAttribute('to_ref')
        
#                   if self.fromactive == 1: # select the basis for the calculation => when the from field was changed use the data from this field 
#                       number = number_from
#                   if self.toactive == 1:
#                    number = number_to

                    result = eval(toref) # execute the formular in the toref field and safe it to result
                    endresult = eval(fromref) # convert from the refunit to the target unit
                    printresult = str(endresult).replace('.',',') # for the better readability replace the dot with a comma
        
#                    if self.fromactive == 1:
#                        self.toentry_set(printresult) # sets the result into the 'from' field
#                    else:
                    self.fromentry_set(printresult) # same as above for the 'to' field

            else:
                number = self.number_from_isset()
                if number == 'nonnumber': # when the entry is not a number print a error
                    self.fromentry_set('Error - put in a number')
                
                else:
                    for categorynames in file.getElementsByTagName('category'): # search the categorys
                        if categorynames.getAttribute('name') == category_isset: # search through the file according to the set category
                            for units in categorynames.getElementsByTagName('unit'): # get the units from the specific category
                                if units.getAttribute('name') == unit_from: # the name from the unit in the category musst set in the to field 
                                    if self.fromactive == 1: # when active gets the to_ref field
                                        toref =  units.getAttribute('to_ref')
                                    else:
                                        fromref = units.getAttribute('from_ref') # else the from_ref field
                                if units.getAttribute('name') == unit_to: 
                                    if self.fromactive == 1: 
                                        fromref = units.getAttribute('from_ref')
                                    else:
                                        toref = units.getAttribute('to_ref')
        
#                    if self.fromactive == 1: # select the basis for the calculation => when the from field was changed use the data from this field 
#                    number = number_from
#                    if self.toactive == 1:
#                        number = number_to

                    result = eval(toref) # execute the formular in the toref field and safe it to result
                    endresult = eval(fromref) # convert from the refunit to the target unit
                    printresult = str(endresult).replace('.',',') # for the better readability replace the dot with a comma
        
#                    if self.fromactive == 1:
                    self.toentry_set(printresult) # sets the result into the 'from' field
#                    else:
#                        self.fromentry_set(printresult) # same as above for the 'to' field
        
    def clear(self, widget): # clears the entry fields
        self.fromentry.set_text('')
        self.toentry.set_text('')

    def fromentry_cursor(self, widget, data=None):
        self.fromentry.set_text('')

    def toentry_cursor(self, widget, data=None):
        self.toentry.set_text('')

    def __init__(self):
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
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
        self.fromentry.set_text('Input a number here ')
        self.fromentry.connect('changed', self.fromentry_changed)
        self.fromentry.connect('activate', self.convert)
        self.fromentry.connect('focus_in_event', self.fromentry_cursor)
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
        self.toentry.set_text('... or here')
        self.toentry.connect('changed', self.toentry_changed)
        self.toentry.connect('activate', self.convert)
        self.toentry.connect('focus_in_event', self.toentry_cursor)
        self.tobox.pack_start(self.toentry, False, False, 0)   

#a combobox for the to unit
        self.tocombo = gtk.combo_box_new_text()
        self.tobox.pack_start(self.tocombo, False, False , 0)

#create a box for the go and clear button
        self.sendbox = gtk.HBox(True,2)
        self.box.pack_end(self.sendbox, False, False, 0)

        self.gobutton = gtk.Button('Go')
        self.sendbox.pack_start(self.gobutton, True, True, 0)
        self.gobutton.connect('clicked', self.convert)
        
        self.clearbutton = gtk.Button('Clear')
        self.sendbox.pack_start(self.clearbutton, True, True, 0)
        self.clearbutton.connect('clicked', self.clear)

# Display all elements
        self.window.show_all()

def main():
    gtk.main()
    return 0

if __name__ == '__main__':
    unitconvert().create_menu()
    main()
