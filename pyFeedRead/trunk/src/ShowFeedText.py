"""
 * ShowFeedContent.py - FeedRead - show text
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
# import BeautifulSoup
import re
import os

class ShowFeedText(gtk.VBox):
    def __init__(self, FeedPanel):
        gtk.VBox.__init__(self, False, 0)
        self.FeedContentPanel = FeedPanel
        self.create_notebook_page()
    
    def get_url_content(self, title, url):
        self.state_entry.set_text(self.FeedContentPanel.feed_provider)
        ## html to text 
        ## from http://mail.python.org/pipermail/python-list/2005-February/309923.html
        comments = re.compile('<!--.*?-->', re.DOTALL)
        tags = re.compile('<.*?>', re.DOTALL)
        """        
        def extracttext(obj):
            if isinstance(obj,BeautifulSoup.Tag):
                return "".join(extracttext(c) for c in obj.contents)
            else:
                return str(obj)
        
        def striptags(text):
            text = re.sub(comments,'', text)
            text = re.sub(tags,'', text)
            return text


        def bsouptext(text):
            if len(text) > 0:
#                try:
                souptree = BeautifulSoup.BeautifulSoup(text)
#                if isinstance(souptree.body, str):
                bodytext = extracttext(souptree.body.fetchText)
                text = re.sub(comments,'', bodytext)
                text = collapsenewlines(text)
                return text
 #               except:
 #                   return ""
            return ""
        """
        def collapsenewlines(text):
            tmp_text = "\n".join(line for line in text.splitlines() if line)
            ret_text = ""
            for line in tmp_text.split("\n"):
                if len(line.rstrip()) >= 1:
                    ret_text += line.rstrip() + '\n'
            return ret_text
            return " ".join(word for word in \
                ("\n".join(line for line in text.splitlines() if line)).split(" ") \
                if len(word) > 1)
        
        descr_text = self.FeedContentPanel.descriptions[url]
        if len(descr_text) >= 1:
            descr_text = re.sub(comments,'', descr_text)
#            descr_text = collapsenewlines(descr_text)
            return descr_text


        #doc = urllib.urlopen(url)
        print "url: %s" %url
        #doc_text = doc.read()

        ### different aproach using lynx
        ELINKS_CMD = "links -dump -dump-charset utf8 -dump-width 1024"  # -assume_charset=utf8 -display_charset=utf8"
        LINKS_CMD = "links -dump"
        LYNX_CMD = "lynx -dump -assume_charset=utf8 -display_charset=utf8 -width=1024"
        CMD = LINKS_CMD
        try: 
#            print "Command: %s" %("%s %s" %(CMD, url))
#            lynx_ostream = os.popen("%s %s" %(CMD, url))
#            message_text = re.sub(comments,'', lynx_ostream.read())
            
            doc = urllib.urlopen(url)
            print "1"
            new_text = ""
            message_text = doc.read()
            message_text = re.sub(comments,'', message_text)
            tag_level = 0
            for char in message_text:
                if char == '<':
                    tag_level += 1
                if char == '>':
                    tag_level -= 1
                else:
                    if tag_level >= 1:
                        continue
                    else:
                        try:
                            new_text += char.encode('utf-8')
                        except:
                            new_text += '?'

            message_text = collapsenewlines(new_text)
            return message_text
        except:
            return "Error: Could not run the links program to load data."
    
    def load_feed(self, widget):
        (model, model_iter) = self.FeedContentPanel.feed_list.get_selection().get_selected()
        if model_iter >= 1:
            feed_name = model.get_value(model_iter, 0)    # column is first (name)
            url = model.get_value(model_iter, 1)    # column is second (url)
            text = self.get_url_content(feed_name, url)
        else:
            feed_name = "none"
            url = "http://"
            text = "No Content"
        
        self.text_buffer.set_text("%s\n\n%s" % (feed_name, text) )

    def create_notebook_page(self):
        self.set_border_width(0)

        text_box = gtk.VBox(False, 0)
        #text_box.set_border_width(15)
        
        update_btn = gtk.Button("update")
        update_btn.connect("clicked", self.load_feed)        
        self.pack_start(update_btn, False, False, 0)
        
        self.state_entry = gtk.Entry()
        self.state_entry.set_text("")
        self.state_entry.set_sensitive(0)
        text_box.pack_start(self.state_entry, False, False, 0)
        
        scroll_win = gtk.ScrolledWindow()
        scroll_win.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        text_view = gtk.TextView()
        text_view.set_cursor_visible(False)
        text_view.set_wrap_mode(gtk.WRAP_WORD)
        self.text_buffer = text_view.get_buffer()
        
        text_view.set_editable(False)

        scroll_win.add(text_view)
        text_box.add(scroll_win)

        self.pack_start(text_box, True, True, 0)
        self.show_all()
                