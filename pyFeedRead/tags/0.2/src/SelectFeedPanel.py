"""
 * SelectFeedPanel.py - FeedRead - list of feeds
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
import os

DATA_FILE = "~/.pyFeedRead.data"

class SelectFeedPanel(gtk.VBox):
    def __init__(self):
        gtk.VBox.__init__(self, False, 0)
        data_file = os.path.expanduser(DATA_FILE)
        if os.path.exists(data_file):
            try:
                data_fd = open(data_file, 'r')
                self.saved_store = self.load_feed_list(data_fd.read().split('\n'))
                data_fd.close()
            except:
                self.saved_store = None
        else:
            self.saved_store = None

        self.create_notebook_page()

    def load_feed_list(self, lines):
        store = gtk.ListStore(str, str)
        for line in lines:
            if len(line.split("\"")) >= 4:
                name = line.split("\"")[1]
                url = line.split("\"")[3]
                store.append([name, url])
        return store


    def save_cb(self, widget):
        data_file = os.path.expanduser(DATA_FILE)
        data_fs = open(data_file , 'w')
        list_iter = self.list_store.get_iter_first()
        while list_iter != None:
            name = self.list_store.get(list_iter, 0)[0]
            url = self.list_store.get(list_iter, 1)[0]
            list_iter = self.list_store.iter_next(list_iter)
            data_fs.write("\"%s\",\"%s\"\n" %(name, url))
        data_fs .close()

    def edited_cb(self, cell, path, new_text, user_data):
        liststore, column = user_data
        liststore[path][column] = new_text
        return
    
    def create_notebook_page(self):
        self.set_border_width(0)

        list_frame = gtk.Frame("Feeds")
        list_frame.set_border_width(0)
        list_box = gtk.VBox(False, 0)
        list_box.set_border_width(15)
        scroll_win = gtk.ScrolledWindow()
        scroll_win.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        if self.saved_store == None:
            self.list_store = gtk.ListStore(str, str)
            self.feed_list = gtk.TreeView(self.list_store)
            self.list_store.append(['Spiegel Online', 'http://www.spiegel.de/schlagzeilen/rss/0,5291,10,00.xml'])
            self.list_store.append(['Reuters', 'http://today.reuters.com/rss/topNews'])
            self.list_store.append(['Heise', 'http://www.heise.de/newsticker/heise.rdf'])
        else:
            self.list_store = self.saved_store
            self.feed_list = gtk.TreeView(self.list_store)
        
        cell0 = gtk.CellRendererText()        
        cell0.set_property('editable', True)
        cell1 = gtk.CellRendererText()
        cell1.feed_listet_property('editable', True)
          
        cell0.connect('edited', self.edited_cb, (self.list_store, 0))
        cell1.connect('edited', self.edited_cb, (self.list_store, 1))
          
        tvcolumn0 = gtk.TreeViewColumn('Feed Name', cell0, markup=0)
        tvcolumn1 = gtk.TreeViewColumn('Feed URL', cell1, markup=1)
        
        self.feed_list.append_column(tvcolumn0)
        self.feed_list.append_column(tvcolumn1)
        
        tvcolumn0.set_sort_column_id(0)
        tvcolumn1.set_sort_column_id(1)
        tvcolumn0.set_resizable(True)
        tvcolumn1.set_resizable(True)
        
        scroll_win.add(self.feed_list)
        list_box.add(scroll_win)
        
        btn_box = gtk.HBox()
        
        add_btn = gtk.Button("Add\nnew Feed")
        add_btn.connect("clicked", self.add_feed)
        btn_box.add(add_btn)
        
        save_btn = gtk.Button("Save\nList")
        save_btn.connect("clicked", self.save_cb)
        btn_box.add(save_btn)
        
        list_box.pack_start(btn_box, False, False, 0)
        
        list_frame.add(list_box)
        self.pack_start(list_frame, True, True, 0)
        self.show_all()
        
    def add_feed(self, widget):
        row_iter = self.list_store.append(['New', 'http://'])
        
