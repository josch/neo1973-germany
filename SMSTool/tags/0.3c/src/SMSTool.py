#!/usr/bin/python
"""
 * SMSTool.py - Tool to send SMS - using libgsmd-tool
 *
 * ProcessInterface copied from SettingsGUI
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

import os
import gtk
import gobject 
import time

from smstool.ProcessInterface import *

LIBGSM_TOOL = "/usr/bin/libgsmd-tool"


class SMSTool:
    def delete_event(self, widget, event, data=None):
        gtk.main_quit()
        return False


    def update_ui(self):
        if self.message_box_activated:
            self.message_box_activated = False
            gtk.gdk.threads_enter()
            try:
                mbox = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, 
                        gtk.BUTTONS_OK, self.message_box_text);
                response = mbox.run()
                mbox.hide()
                mbox.destroy()
            finally:
                gtk.gdk.threads_leave()
            if self.close_application:
                exit()
        return True

    def __init__(self):
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title("SMS Tool")
        self.window.connect("delete_event", self.delete_event)
        self.window.set_border_width(0)
        self.message_box_activated = False
        self.close_application = False
        
        if not self.connect_to_gsmdtool(None):
            self.message_box_text = "Could not connect to the GSM daemon.\n\
                    SMSTool will quit now."
            # self.message_box_activated = True
            # self.close_application = True
        
        main_box = gtk.VBox()
        main_box.set_border_width(10)

        text_frame = gtk.Frame("Message Content")
        SMS_text_view = gtk.TextView()
        self.SMS_text_buffer = SMS_text_view.get_buffer()
        self.SMS_text_buffer.set_text("Hello mobile World!")
        text_frame.add(SMS_text_view)
        main_box.add(text_frame)

        number_frame = gtk.Frame("Telephone Number")
        self.number_entry = gtk.Entry()
        self.number_entry.set_text("00491706692447")
#        number_frame.set_spacing(15)
        number_frame.add(self.number_entry)
        main_box.pack_start(number_frame, False, False, 0)


        btn_box = gtk.HBox()
        
        """
        gsm_btn = gtk.Button("Connect\nto gsmd")
        gsm_btn.connect("clicked", self.connect_to_gsmdtool)
        btn_box.add(gsm_btn)        
        """
        
        send_btn = gtk.Button("Send\nSMS")
        send_btn.connect("clicked", self.send_sms)
        btn_box.add(send_btn)

        main_box.pack_start(btn_box, False, False, 0)
        
        self.window.add(main_box)
        self.window.show_all()

        
    def update_state(self, text):
        print ("state: %s" % text).rstrip("\n")
        
    def message_was_send(self, text):
        self.message_box_text = "Message send.\nModem: %s" % text
        self.message_box_activated = True

        
    def send_sms(self, widget):
        text = self.SMS_text_buffer.get_text(
                                    self.SMS_text_buffer.get_start_iter(),
                                    self.SMS_text_buffer.get_end_iter())
        number = self.number_entry.get_text()
        
        text = " ".join(text.split("\n"))
        text = " ".join(text.split("\r"))
        text = "\""+text+"\""
        
        print "sending... \n---\n%s\n--- \nto <%s>" % (text, number)
        if self.gsm_tool:
            self.gsm_tool.write_to_process("ss=0,%s,%s" % (number, text))
        else:
            self.update_state("ERROR: Could not send you message, sorry!")
        
    def connect_to_gsmdtool(self, widget):
        if os.path.exists(LIBGSM_TOOL):
            self.update_state("connection to gsmd...")
            self.gsm_tool = ProcessInterface(
                                                "%s -m shell" % LIBGSM_TOOL)
            time.sleep(1)   # wait for tool to connect (or not)
            error_out = self.gsm_tool.read_error_from_process()
            if len(error_out) > 0:
                error_out = error_out.rstrip('\n').lstrip('\n').rstrip(
                                                            '\r').lstrip('\r')
                print "error libgsm-tool: %s" % error_out
                return False

            self.gsm_tool.register_event_handler("", self.update_state)
            self.gsm_tool.register_event_handler("Send: ", self.message_was_send)
            """
            this is disabled, for now - we should be connected
            
            print "initializing gsm"
            self.gsm_tool.write_to_process("O")
            time.sleep(0.3)
            self.gsm_tool.write_to_process("r")
            """ 
            return True
        else:
            self.update_state("%s not found, can not send SMS." % LIBGSM_TOOL)
            self.gsm_tool = False
        return False
                
        
        
def main():
    gobject.timeout_add(500, SMSTool.update_ui) # every 1/2 second
    try:
        if gtk.gtk_version[0] == 2:
            gtk.gdk.threads_init()
    except:
        pass
    gtk.gdk.threads_enter()
    gtk.main()
    gtk.gdk.threads_leave()


if (__name__ == '__main__'):
    SMSTool = SMSTool()
    main()
