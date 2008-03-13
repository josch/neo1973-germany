"""
 * ShowFeedContent.py - FeedRead - show feed entries
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
import urllib

class ShowFeedContent(gtk.VBox):
    def __init__(self, FeedPanel):
        gtk.VBox.__init__(self, False, 0)
        self.FeedPanel = FeedPanel
        self.feed_provider = ""
        self.create_notebook_page()
        self.descriptions = {}
        
    def get_feed_content(self, url):
        doc = urllib.urlopen(url)
        print "searching feed..."
        link = ""
        name = ""
        description = ""
        found_item = False
        for line in doc.read().split("\n"):
            if line.find("<item ") >= 0 or line.find("<item>") >= 0 or found_item:
                found_item = True
            else:
                continue

            if line.find("</item>") >= 0:
                self.list_store.append([name, link])
                self.descriptions.update({link: description})
                found_item = False

            if line.find("<link>") >= 0:
                link = line.split(">")[1].split("<")[0]

            if line.find("<title>") >= 0:
                name = line.split(">")[1].split("<")[0]

            if line.find("<description>") >= 0:
                description = line.split(">")[1].split("<")[0]
        
    def load_feed(self, widget):
        (model, model_iter) = self.FeedPanel.feed_list.get_selection().get_selected()
        if model_iter >= 1:
            self.list_store.clear()
            feed_name = model.get_value(model_iter, 0)    # column is first (name)
            self.feed_provider = feed_name
            self.state_entry.set_text(feed_name)
            url = model.get_value(model_iter, 1)    # column is second (url)
            text = self.get_feed_content(url)
        else:
            feed_name = "none"
            url = "http://"
            text = "No Content"
    
    def create_notebook_page(self):
        self.set_border_width(0)

        list_box = gtk.VBox(False, 0)
        #list_box.set_border_width(15)

        update_btn = gtk.Button("update")
        update_btn.connect("clicked", self.load_feed)
        self.pack_start(update_btn, False, False, 0)

        self.state_entry = gtk.Entry()
        self.state_entry.set_text("")
        self.state_entry.set_sensitive(0)
        list_box.pack_start(self.state_entry, False, False, 0)

        scroll_win = gtk.ScrolledWindow()
        scroll_win.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        self.list_store = gtk.ListStore(str, str)
        self.feed_list = gtk.TreeView(self.list_store)
        cell = gtk.CellRendererText()
        cell.set_property('editable', True)
        tvcolumn0 = gtk.TreeViewColumn('Article', cell, markup=0)
        tvcolumn1 = gtk.TreeViewColumn('URL', cell, markup=1)
        
        self.feed_list.append_column(tvcolumn0)
        self.feed_list.append_column(tvcolumn1)
        
        tvcolumn0.set_sort_column_id(0)
        tvcolumn1.set_sort_column_id(1)
        tvcolumn0.set_resizable(True)
        tvcolumn1.set_resizable(True)
        
        scroll_win.add(self.feed_list)
        list_box.add(scroll_win)
        
        self.pack_start(list_box, True, True, 0)
        self.show_all()
