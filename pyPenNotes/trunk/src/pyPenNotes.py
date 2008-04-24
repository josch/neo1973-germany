#!/usr/bin/python
"""
 * pyPenNotes.py - pyPenNotes - initialize GUI
 *
 * (C) 2008 by Kristian Mueller <kristian-m@kristian-m.de>
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
import gtk
import gobject ## for multithreading

import notesList
from UserDrawingArea import UserDrawingArea
import SaveRestore

COLOR_LIST = ["#00000000ffff", "#ffff00000000", "#0000ffff0000", "#ffffffff0000", "#ffffffffffff", "#000000000000"]
DEFAULT_BG = 5 ## Black
DEFAULT_FG = 0 ## Blue
DEFAULT_SIZE = 4 ## Diameter 4 Pixel
DATA_FILE = "~/.penNotes.strokes_data"
QUALITY_LOSS = 5 ## Quality loss when removing unneeded points. Measured in pixels.

class pyPenNotes:
    ## init the class
    def __init__(self):
        self.state = "pre-init"
        self.current_note_number = 0
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_default_size(480, 640)
        self.window.set_title("pyPenNotes")
        self.window.connect("destroy", self.end_program)
        self.window.show()
        self.more_options_visible = False
        self.state = "init-done"
        self.save_restore = SaveRestore.BasicFile(DATA_FILE)
        self.save_restore.quality_loss = QUALITY_LOSS

    def update_ui(self):
        if self.state == "init-done":
            self.create_window()
            self.state = "running"
            return False ## okay, we're done
        else:
            return True ## please come back later

    ## create content of the main window
    ## asynchronous - so we can have a faster start up
    def create_window(self):
        vbox = gtk.VBox()
        main_toolbar = gtk.Toolbar()
        main_toolbar.set_style(gtk.TOOLBAR_ICONS);
        self.sub_toolbar = gtk.Toolbar()
        self.sub_toolbar.set_style(gtk.TOOLBAR_ICONS);
        self.area = UserDrawingArea()
        self.area.line_width = DEFAULT_SIZE
        self.table = gtk.Table(2,2)
        self.hruler = gtk.HRuler()
        self.vruler = gtk.VRuler()
        self.hruler.set_range(0, 400, 0, 400) #todo
        self.vruler.set_range(0, 300, 0, 300) #todo
        self.table.attach(self.hruler, 1, 2, 0, 1, yoptions=0)
        self.table.attach(self.vruler, 0, 1, 1, 2, xoptions=0)
        self.table.attach(self.area, 1, 2, 1, 2)

        size_evnt_box = gtk.EventBox()
        self.size_number_entry = gtk.Label()
        size_evnt_box.add(self.size_number_entry)
        self.size_number_entry.set_text("%2.2dpx" % DEFAULT_SIZE)
        self.size_number_entry.modify_fg(gtk.STATE_NORMAL, \
                    self.size_number_entry.get_colormap().alloc_color(\
                                                    COLOR_LIST[DEFAULT_FG]))
        self.size_number_entry.set_width_chars(4) # max: "99 px"
        size_evnt_box.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        size_evnt_box.connect("button_press_event", self.fg_color_select)

        note_evnt_box = gtk.EventBox()
        self.note_number_entry = gtk.Label()
        note_evnt_box.add(self.note_number_entry)
        self.note_number_entry.set_text("%4.4d" % (self.current_note_number+1))
        self.note_number_entry.modify_fg(gtk.STATE_NORMAL, \
                                    self.size_number_entry.get_colormap().\
                                    alloc_color(COLOR_LIST[DEFAULT_BG]))
        self.note_number_entry.set_width_chars(4)
        note_evnt_box.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        note_evnt_box.connect("button_press_event", self.bg_color_select)

        #######################################################################
        ## fill in toolbar items ##############################################
        #######################################################################
        
        def create_toolbutton(stock, callback, expand = False):
            btn = gtk.ToolButton(stock);
            btn.connect("clicked", callback);
            if(expand):
                btn.set_expand(True)
            return btn

        ## size <
        main_toolbar.insert(create_toolbutton("gtk-go-back", self.prev_size), -1)
        ## size ??px
        size_item = gtk.ToolItem()
        size_item.add(size_evnt_box)
        main_toolbar.insert(size_item, -1)
        ## size >
        main_toolbar.insert(create_toolbutton("gtk-go-forward", self.next_size), -1)
        main_toolbar.insert(gtk.SeparatorToolItem(), -1)

        ## cls
        self.more_btn = gtk.ToggleToolButton("gtk-go-down");
        self.more_btn.connect("toggled", self.more_options);
        self.more_btn.set_expand(True);
        main_toolbar.insert(self.more_btn, -1)
        
        main_toolbar.insert(gtk.SeparatorToolItem(), -1)

        ## note <
        main_toolbar.insert(create_toolbutton("gtk-go-back", self.prev_note), -1)
        ## note ????
        note_item = gtk.ToolItem()
        note_item.add(note_evnt_box)
        main_toolbar.insert(note_item, -1)
        ## note >
        main_toolbar.insert(create_toolbutton("gtk-go-forward", self.next_note), -1)


        # Fill in the sub toolbar:
        
        # Clear
        self.sub_toolbar.insert(create_toolbutton("gtk-clear", self.clear_note, True), -1)
        # Undo
        self.sub_toolbar.insert(create_toolbutton("gtk-undo", self.undo, True), -1)
        # Revert to saved
        self.sub_toolbar.insert(create_toolbutton("gtk-revert-to-saved", self.revert_to_saved, True), -1)
        # Save
        self.sub_toolbar.insert(create_toolbutton("gtk-save", self.save, True),-1)
        # Quit
        self.sub_toolbar.insert(create_toolbutton("gtk-quit", self.end_program, True), -1)
        
        #Experimental:
#        self.sub_toolbar.insert(create_toolbutton(\
#              "gtk-revert-to-saved-ltr", self.print_list_sub_number, True), -1)
#        self.sub_toolbar.insert(create_toolbutton(\
#                  "gtk-revert-to-saved-ltr", self.print_list_number, True), -1)


        vbox.pack_start(main_toolbar, False, False, 0)
        vbox.pack_start(self.sub_toolbar, False, False, 0)
        vbox.add(self.table);
        self.window.add(vbox)
        def motion_notify(ruler, event):
            return ruler.emit("motion_notify_event", event)
        self.area.add_events(gtk.gdk.POINTER_MOTION_MASK |
                             gtk.gdk.POINTER_MOTION_HINT_MASK )
        self.area.connect_object("motion_notify_event", motion_notify,
                                 self.hruler)
        self.area.connect_object("motion_notify_event", motion_notify,
                                 self.vruler)

        def size_allocate_cb(wid, allocation):
            x, y, w, h = allocation
            l,u,p,m = self.hruler.get_range()
            m = max(m, w)
            self.hruler.set_range(l, l+w, p, m)
            l,u,p,m = self.vruler.get_range()
            m = max(m, h)
            self.vruler.set_range(l, l+h, p, m)
        self.area.connect('size-allocate', size_allocate_cb)
        self.window.show_all()
        self.sub_toolbar.hide()    ## Hide to make space on screen
        self.hruler.hide()
        self.vruler.hide()

        self.update_area()

        
        
    ###########################################################################
    ## callbacks    ###########################################################
    ###########################################################################

    ## debug correlation of notes list 
    def print_list_number(self, event):
        for i in range(len(self.pen_notes)):
            for j in range(len(self.pen_notes)):
                print ""
                notesList.pearson_correlation(self.pen_notes, i, j, "number", \
                                                                "sub_number")
        #notesList.pearson_corr(self.pen_notes, 0, 1, "number")

    ## debug correlation of notes list 
    def print_list_sub_number(self, event):
        notesList.pearson_correlation(self.pen_notes, 0, 1, "sub_number", \
                                                                    "number")
        #notesList.pearson_corr(self.pen_notes, 0, 1, "sub_number")

    ## change brush size--
    def prev_size(self, event):
        self.area.line_width /= 2
        if self.area.line_width <= 0:
            self.area.line_width = 1
        self.size_number_entry.set_text("%2.2d px" % self.area.line_width)


    ## change brush size++
    def next_size(self, event):
        self.area.line_width *= 2
        if self.area.line_width > 99:
            self.area.line_width = 99
        self.size_number_entry.set_text("%2.2d px" % self.area.line_width)

    def load_changes_from_area(self):
        """Load changes made to the area, so that they can be saved."""
        self.save_restore.set_note(self.current_note_number, \
            SaveRestore.PenNote(self.area.get_bg_color(), self.area.get_strokes()))
    
    def update_area(self):
        """Load notes with self.current_note_number and display them on the UserDrawingArea"""
        note = self.save_restore.get_note(self.current_note_number)
        self.area.set_bg_color(note.bg_color)
        self.area.set_strokes(note.strokes)
        
        self.note_number_entry.modify_fg(gtk.STATE_NORMAL, \
                                self.size_number_entry.get_colormap().\
                                alloc_color(self.area.get_bg_color()))

    def prev_note(self, event):
        """Select the previous note."""
        self.load_changes_from_area()
        if self.current_note_number > 0:
            self.current_note_number -= 1
            self.note_number_entry.set_text("%4.4d"%(self.current_note_number+1))
        self.update_area()
         
    def next_note(self, event):
        """Select the next or a new note."""
        self.load_changes_from_area()
        self.current_note_number += 1
        self.note_number_entry.set_text("%4.4d" % (self.current_note_number+1))
        self.update_area()


    def more_options(self, event):
        """Show more options. (A second toolbar and the rulers.)"""
        if self.more_options_visible:
            self.sub_toolbar.hide()
            self.hruler.hide()
            self.vruler.hide()
            self.more_options_visible = False
        else:
            self.sub_toolbar.show()
            self.hruler.show()
            self.vruler.show()
            self.more_options_visible = True

    def undo(self, event):
        self.area.undo()
    
    def revert_to_saved(self, event):
        self.save_restore.revert_changes()
        self.update_area()
    
    def save(self, event):
        self.load_changes_from_area()
        self.save_restore.save()

    def end_program(self, event):
        self.save(None)
        gtk.main_quit()



    ###########################################################################
    ## operation doing actual drawing to the screen ###########################
    ###########################################################################

    ## increment foreground color - select new pen color
    def fg_color_select(self, event, blub):
        index = COLOR_LIST.index(self.area.get_fg_color())
        index += 1
        if index >= len(COLOR_LIST):
            index = 0   ## cycle around
        self.area.set_fg_color(COLOR_LIST[index]);
        self.size_number_entry.modify_fg(gtk.STATE_NORMAL, \
                                        self.size_number_entry.get_colormap().\
                                        alloc_color(COLOR_LIST[index]))


    ## increment background color
    def bg_color_select(self, event, blub):
        index = COLOR_LIST.index(self.area.get_bg_color())
        index += 1
        if index >= len(COLOR_LIST):
            index = 0   ## cycle around
        self.area.set_bg_color(COLOR_LIST[index]);
        ## show color as fontcolor for note number
        self.note_number_entry.modify_fg(gtk.STATE_NORMAL, \
                                self.size_number_entry.get_colormap().\
                                alloc_color(COLOR_LIST[index]))


    ## trow away the content of the note
    def clear_note(self, event):
        self.area.clear()


def main():
    gobject.timeout_add(500, pyPenNotes.update_ui, py_pen_notes) # every 1/2 sec
    try:
        if gtk.gtk_version[0] == 2:
            gtk.gdk.threads_init()
    except:
        pass
    gtk.gdk.threads_enter()
    gtk.main()
    gtk.gdk.threads_leave()
    return 0

if __name__ == "__main__":
    py_pen_notes = pyPenNotes()
    main()
