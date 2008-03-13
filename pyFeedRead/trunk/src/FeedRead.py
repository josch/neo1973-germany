#!/usr/bin/python
"""
 * FeedRead.py - pyFeedRead - initialize GUI
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

import gtk
from SelectFeedPanel import *
from ShowFeedContent import *
from ShowFeedText import *

NOTEBK_PADDING = 6
# NOTEBK_PADDING = 0

class FeedRead:
    def __init__(self):
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title("pyFeedRead")
        self.window.connect("delete_event", self.delete_event)
        self.window.set_border_width(0)
        self.window.set_default_size(480, 640)

        self.notebook = gtk.Notebook()
        self.notebook.set_tab_pos(gtk.POS_BOTTOM)

        FeedPanel = SelectFeedPanel()
        self.add_notebook_page(FeedPanel, "gtk-index")
        FeedContentPanel = ShowFeedContent(FeedPanel)
        self.add_notebook_page(FeedContentPanel, "gtk-justify-left")
        self.add_notebook_page(ShowFeedText(FeedContentPanel), "gtk-justify-center")

        ## expand page selectors to full width
        for child in self.notebook.get_children():
            self.notebook.child_set_property(child, "tab_expand", True)
        self.notebook.show()

        self.window.add(self.notebook)
        self.window.show_all()

    def delete_event(self, widget, event, data=None):
        gtk.main_quit()
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




def main():
    gtk.gdk.threads_init()
    gtk.gdk.threads_enter() 
    try:
        gtk.main()        
    except:
        exit(0)
    gtk.gdk.threads_leave() 
       
if (__name__ == '__main__'):
    FeedRead = FeedRead()
    main()

