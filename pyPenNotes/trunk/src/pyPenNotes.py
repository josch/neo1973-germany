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
import sys ## exit
import os ## file handling

import notesList

COLOR_LIST = ["#0000FF", "#FF0000", "#00FF00", "#FFFF00", "#FFFFFF", "#000000"]
DEFAULT_BG = 5 ## Black
DEFAULT_FG = 0 ## Blue
DEFAULT_SIZE = 4 ## Diameter 4 Pixel
DATA_FILE = "~/.penNotes.strokes_data"

## A note is defined by its strokes a background and the line thickness.
## Strokes of the same color and thickness are combined in a strokes_list.
## The order of strokes will stay the same.
class PenNote:
    def __init__(self):
        self.bg_color = DEFAULT_BG
        self.last_fg_color = 0
        self.last_line_thickness = DEFAULT_SIZE
        self.last_stroke = (0, 0)
        self.strokes_list = []   # current list of strokes from 
                                 # the same color or thickness
                                 # strokes are tuples of src and dest
        self.image_list = []     # list of (color, thickness, strokes_list)
        self.image_list.append((self.last_fg_color, self.last_line_thickness,
                                                            self.strokes_list))

    def add_stroke(self, src, dest, color, line_thickness):
        if (color != self.last_fg_color) or \
                (self.last_line_thickness != line_thickness) \
                or self.last_stroke != src:
            self.strokes_list = []
            self.strokes_list.append((src[0], src[1]))
            self.image_list.append((color, line_thickness, self.strokes_list))
            self.last_fg_color = color
            self.last_line_thickness = line_thickness

        self.strokes_list.append((dest[0], dest[1]))
        self.last_stroke = dest

    def append_point_to_stroke(self, coord):
        self.strokes_list.append(coord)

    def append_new_point(self, coord, color, thickness):
        self.strokes_list = []
        self.strokes_list.append(coord)
        self.image_list.append((color, thickness, self.strokes_list))
        self.last_fg_color = color
        self.last_line_thickness = thickness

    def clear(self):
        self.__init__()

class pyPenNotes:
    ## init the class
    def __init__(self):
        self.state = "pre-init"
        self.current_note_number = 0
        self.size_num = DEFAULT_SIZE
        self.fg_color = DEFAULT_FG
        self.bg_color = DEFAULT_BG
        self.pen_notes = []
        self.current_note = PenNote()
        self.pen_notes.append(self.current_note)
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_default_size(480, 640)
        self.window.set_title("pyPenNotes")
        self.window.connect("destroy", lambda w: gtk.main_quit())
        self.window.show()
        self.more_options_visible = False
        self.state = "init-done"

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
        self.area = gtk.DrawingArea()
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
        self.size_number_entry.set_text("%2.2dpx" % self.size_num)
        self.size_number_entry.modify_fg(gtk.STATE_NORMAL, \
                    self.size_number_entry.get_colormap().alloc_color(\
                                                    COLOR_LIST[self.fg_color]))
        self.size_number_entry.set_width_chars(4) # max: "99 px"
        size_evnt_box.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        size_evnt_box.connect("button_press_event", self.fg_color_select)

        note_evnt_box = gtk.EventBox()
        self.note_number_entry = gtk.Label()
        note_evnt_box.add(self.note_number_entry)
        self.note_number_entry.set_text("%4.4d" % (self.current_note_number+1))
        self.note_number_entry.modify_fg(gtk.STATE_NORMAL, \
                                    self.size_number_entry.get_colormap().\
                                    alloc_color(COLOR_LIST[self.bg_color]))
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
        self.sub_toolbar.insert(create_toolbutton("gtk-revert-to-saved", self.load, True), -1)
        # Save
        self.sub_toolbar.insert(create_toolbutton("gtk-save",self.save, True),-1)
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
        self.area.set_events(gtk.gdk.POINTER_MOTION_MASK |
                             gtk.gdk.POINTER_MOTION_HINT_MASK )
        self.area.connect("expose-event", self.area_expose_cb)

        def motion_notify(ruler, event):
            return ruler.emit("motion_notify_event", event)

        def add_pixel(widget, event):
            if self.clicked:
                pos = widget.get_pointer()
                # print "blub <%s/%s>" % (widget.get_pointer()[0], \
                #                                    widget.get_pointer()[1])
                backup_fb = self.gc.foreground
                try:
                    self.gc.foreground = widget.window.get_colormap().alloc_color(\
                                                    COLOR_LIST[self.fg_color])

                    if self.last == (0, 0):
                        self.last = pos
                    self.gc.set_line_attributes(self.size_num, \
                            gtk.gdk.LINE_SOLID, gtk.gdk.CAP_ROUND, \
                            gtk.gdk.CAP_ROUND)
                    widget.window.draw_line(self.gc, self.last[0], \
                            self.last[1], pos[0], pos[1])
                finally:
                    self.gc.foreground = backup_fb
                self.current_note.add_stroke((self.last[0], self.last[1]),
                                (pos[0], pos[1]), self.fg_color, self.size_num)
                self.last = pos

        self.area.connect_object("motion_notify_event", motion_notify,
                                 self.hruler)
        self.area.connect_object("motion_notify_event", motion_notify,
                                 self.vruler)

        self.clicked = False
        self.last = (0, 0)
        def click(widget, event):
            self.clicked = True
            add_pixel(widget, event)

        def unclick(widget, event):
            self.last = (0, 0);
            self.clicked = False

        self.area.add_events(gtk.gdk.BUTTON_MOTION_MASK | \
            gtk.gdk.BUTTON_PRESS_MASK | \
            gtk.gdk.BUTTON_RELEASE_MASK)
        self.area.connect("button-press-event", click)
        self.area.connect("button-release-event", unclick)
        self.area.connect("motion-notify-event", add_pixel)

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


        ## lets update the screen so our load can redraw to something
        self.area_expose_cb(self.area, None)
        self.load(None)


    ###########################################################################
    ## GTK stuff ##############################################################
    ###########################################################################
    def delete_event(self, widget, event, data=None):
        self.save(None)
        gtk.main_quit()
        return False
        
        
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
        self.size_num /= 2
        if self.size_num <= 0:
            self.size_num = 1
        self.size_number_entry.set_text("%2.2d px" % self.size_num)


    ## change brush size++
    def next_size(self, event):
        self.size_num *= 2
        if self.size_num > 99:
            self.size_num = 99
        self.size_number_entry.set_text("%2.2d px" % self.size_num)



    ## prev note
    def prev_note(self, event):
        if self.current_note_number > 0:
            self.current_note_number -= 1
            self.note_number_entry.set_text("%4.4d"%(self.current_note_number+1))
            self.current_note = self.pen_notes[self.current_note_number]
            self.redraw()

    ## new or next note
    def next_note(self, event):
        self.current_note_number += 1
        self.note_number_entry.set_text("%4.4d" % (self.current_note_number+1))
        if len(self.pen_notes) <= self.current_note_number:
            print "creating a new Note..."
            self.current_note = PenNote()
            self.current_note.bg_color = self.bg_color
            self.pen_notes.append(self.current_note)
        self.current_note = self.pen_notes[self.current_note_number]
        self.redraw()


    ## show more options (a second toolbar)
    def more_options(self, event):
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
        if len(self.current_note.image_list) >= 1:
            self.current_note.image_list.pop()
            self.redraw()

    def end_program(self, event):
        self.save(None)
        sys.exit()

    ###########################################################################
    ## save and restore - as kind-of-CSV-file #################################
    ###########################################################################


    ## load from file - format is:
    ## fg, bg, thickness; x,y x,y x,y
    ## every line not containing at last two ',' declare a new note
    def load(self, event):
        ## throw away the old stuff :-(
        self.pen_notes = []
        count = 0 

        data_file_name = os.path.expanduser(DATA_FILE)

        if os.path.exists(data_file_name):
            file_fd = open(data_file_name, 'r')
            try:
                for line in file_fd.read().split('\n'):
                    comma_values = line.split(",")
                    if len(comma_values) >= 2:  ## at least 1 coord
                        fg_color = int(comma_values[0])
                        bg_color = int(comma_values[1])
                        self.current_note.bg_color = bg_color
                        thickness = int(comma_values[2].split(";")[0])
                        if len(line.split(";")[1].rstrip()) <= 0:
                            continue
                        new_stroke = True
                        for coord in line.split("; ")[1].split(" "):
                            coords = coord.split(",")
                            if len(coords) <= 1:
                                continue
                            ## first point
                            if new_stroke:
                                self.current_note.append_new_point(\
                                                            (int(coords[0]), \
                                        int(coords[1])), fg_color, thickness)

#                            self.current_note.strokes_list.append(\
#                                               int(coords[0]), int(coords[1])))

                            self.current_note.append_point_to_stroke(\
                                            (int(coords[0]), int(coords[1])))

                            new_stroke = False
                    else:
                        if len(line) >= 1:
                            count += 1
                            self.current_note = PenNote()
                            self.pen_notes.append(self.current_note)
            finally:
                file_fd.close()
        else:
            print "No notebook file found - using an empty one."
            count += 1
            self.current_note = PenNote()
            self.pen_notes.append(self.current_note)

        print "count: %s, current: %s" %(count, self.current_note_number)
        if count <= self.current_note_number:
            print "Sorry there is no note %4.4d left bringing you to note 0001"\
                                                                % (count + 1) 
            # Count is zero-indexed, while what is displayed to the user is not
            self.current_note_number = 0
            self.next_note(None) # Update the note number box
            self.prev_note(None) #

        self.current_note = self.pen_notes[self.current_note_number]
        self.redraw()

    ## save to file - format is:
    ## fg, bg, thickness; x,y x,y x,y
    def save(self, event):
        file_fd = open(os.path.expanduser(DATA_FILE), 'w')
        count = 0

        for note in self.pen_notes:
            bg_color = note.bg_color
            count += 1
            file_fd.write("Note %4.4d\n" %count)

            for piece in note.image_list:
                fg_color = piece[0]
                thickness = piece[1]
                line = "%d, %d, %d; " %(fg_color, bg_color, thickness)
                if len(piece[2]) >= 1:
                    for coord in piece[2]:
                        line += "%d,%d " % coord
                file_fd.write("%s\n" %line)







    ###########################################################################
    ## operation doing actual drawing to the screen ###########################
    ###########################################################################

    ## increment foreground color - select new pen color
    def fg_color_select(self, event, blub):
        self.fg_color += 1
        if self.fg_color >= len(COLOR_LIST):
            self.fg_color = 0   ## cycle around
        self.size_number_entry.modify_fg(gtk.STATE_NORMAL, \
                                        self.size_number_entry.get_colormap().\
                                        alloc_color(COLOR_LIST[self.fg_color]))


    ## increment background color and redraw screen using the new one
    def bg_color_select(self, event, blub):
        self.bg_color += 1
        if self.bg_color >= len(COLOR_LIST):
            self.bg_color = 0   ## cycle around
        ## show color as fontcolor for note number
        self.note_number_entry.modify_fg(gtk.STATE_NORMAL, \
                                self.size_number_entry.get_colormap().\
                                alloc_color(COLOR_LIST[self.bg_color]))
        self.current_note.bg_color = self.bg_color
        self.redraw()


    ## overdraw the screen using background color
    def clear_draw_screen(self, event):
        fg_backup = self.gc.foreground
        self.gc.foreground = self.area.window.get_colormap()\
                        .alloc_color(COLOR_LIST[self.current_note.bg_color])
        self.area.window.draw_rectangle(self.gc, True, 0, 0, -1, -1)
        self.gc.foreground = fg_backup


    ## trow away the content of the note
    def clear_note(self, event):
        self.current_note.clear()
        self.current_note.bg_color = self.bg_color
        self.redraw()


    ## redraw screen using the notes content
    def redraw(self):
        ## step 1 - clear screen <-- will cause a flicker!
        bg = self.current_note.bg_color
        self.clear_draw_screen(None)

        fg_backup = self.gc.foreground
        self.gc.foreground = self.area.window.get_colormap().\
                                                    alloc_color(COLOR_LIST[bg])
        self.gc.foreground = fg_backup

        ## step 2 - paint all pieces of the same color
        for piece in self.current_note.image_list:
            color = piece[0]
            line_thickness = piece[1]
            ## step 3 - draw all lines of one color
            if len(piece[2]) >= 1:
                fg_backup = self.gc.foreground
                self.gc.foreground = self.area.window.get_colormap().\
                                                alloc_color(COLOR_LIST[color])
                self.gc.set_line_attributes(line_thickness, \
                                gtk.gdk.LINE_SOLID, gtk.gdk.CAP_ROUND, \
                                gtk.gdk.CAP_ROUND)
                self.area.window.draw_lines(self.gc, piece[2])
                self.gc.foreground = fg_backup


    ## is called when ever a redraw is needed
    def area_expose_cb(self, area, event):
        self.style = self.area.get_style()
        self.gc = self.style.fg_gc[gtk.STATE_NORMAL]
        self.redraw()
        #self.gc.set_background(gtk.gdk.color_parse("#000000"))
        #self.gc.set_foreground(gtk.gdk.color_parse("#FFFFFF"))
        return True


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
