"""
 * AudioPanel.py - SettingsGUI - Audio Settings
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

import sys
import os
import gtk
import SysFSAccess
#from settingsgui.GlobalConfiguration import *
from GlobalConfiguration import *


class AudioPanel(gtk.VBox):
    def __init__(self):
        gtk.VBox.__init__(self, False, 0)
        self.muted = 0
        self.volume_scales = {}
        self.create_notebook_page()
        
    def profile_changed_callback(self, box):
        os.system("/usr/sbin/alsactl -f %s%s restore" % (
                ALSA_STATES_DIR, ALSA_ENTRYS[box.get_active_text()]))
        print "called [%s]" % "/usr/sbin/alsactl -f %s%s restore" % (
                ALSA_STATES_DIR, ALSA_ENTRYS[box.get_active_text()])
    
        ## update scales
        for entry in self.volume_scales:
            self.volume_scales[entry].value = self.get_volume(entry)
    
    ## callback save from button
    def save_profile(self, widget):
        os.system("/usr/sbin/alsactl -f %s%s store" % (
                ALSA_STATES_DIR, ALSA_ENTRYS[self.profile_combo.get_active_text()]))
        print "called [%s]" % "/usr/sbin/alsactl -f %s%s store" % (
                ALSA_STATES_DIR, ALSA_ENTRYS[self.profile_combo.get_active_text()])
    

    ## called when a scaled was touched
    def volume_changed_callback(self, scale, channel):
        self.set_volume(channel, scale.value)

    ## callback from mute button
    def mute_audio(self, widget):
        if self.muted != 1:
            self.set_volume(ALSA_CHANNEL_RIGHT, 0)
            self.set_volume(ALSA_CHANNEL_LEFT, 0)
            self.set_volume(ALSA_CHANNEL_MONO, 0)
            self.mute_tbn.set_label("Unmute")
            self.muted = 1
        else:
            for scale in self.volume_scales:
                self.set_volume(scale, self.volume_scales[scale].value)
            self.mute_tbn.set_label("Mute")
            self.muted = 0
        
    ## will use amixer for now - so we dont depend on python-alsa which is not 
    ## in OpenEmbedded now...
    def set_volume(self, chan_id, value):
        amix_ostream = os.popen("%s  cset numid=%d %d" %(ALSA_AMIXER, chan_id, value))
        return True;

    def read_alsa_mixer(self):
        amix_ostream = os.popen("%s" %ALSA_AMIXER)
        mixer = {}  ## dict of mixer controls
        mixer_entry = {}
        for line in amix_ostream.read().split('\n'):
            if not line.startswith("  "):
                if len(line.split("'")) >= 2:
                    mixer["%s" % line.split("'")[1]] = {}
                    mixer_entry = mixer["%s" % line.split("'")[1]]


    ## will use amixer for now - so we dont depend on python-alsa which is not 
    ## in OpenEmbedded now...
    def get_volume(self, chan_id):
        amix_ostream = os.popen("%s  cget numid=%d" %(ALSA_AMIXER, chan_id))
        # ToDo - parse everything!
        amix_out = amix_ostream.readline()
        amix_out = amix_ostream.readline()
        amix_out = amix_ostream.readline()
        if amix_out.find("INTEGER") >=0:
            amix_out = amix_ostream.readline()
            if amix_out.find("value") >= 0:                  
                return int((amix_out.split('=')[1]).split(',')[0])
                #return int(amix_out.split('=')[1])
            return 0;
        return 0;
    
    def get_max_volume(self, chan_id):
        amix_ostream = os.popen("%s  cget numid=%d" %(ALSA_AMIXER, chan_id))
        # ToDo - parse everything!
        amix_out = amix_ostream.readline()
        amix_out = amix_ostream.readline()
        for value_entry in amix_out.split(','):
            if value_entry.find("max") >= 0:
                return int(value_entry.split('=')[1])
        return 100;
    
    def create_notebook_page(self):
        audio_channels = [
            ["Right Speaker", ALSA_CHANNEL_RIGHT],
            ["Left Speaker", ALSA_CHANNEL_LEFT],
            ["Mono Output", ALSA_CHANNEL_MONO],
        ]
        self.set_border_width(0)

        # profile selector dropdown box
        upper_box = gtk.HBox()
        self.profile_combo = gtk.combo_box_new_text()
        for entry in ALSA_ENTRYS.keys():
            self.profile_combo.append_text(entry)
        self.profile_combo.connect('changed', self.profile_changed_callback)
        upper_box.add(self.profile_combo)
        
        self.mute_btn = gtk.Button("Mute")
        self.mute_btn.connect("clicked", self.mute_audio)
        upper_box.pack_start(self.mute_btn, False, False, 0)

        self.add_profile_btn = gtk.Button()
        image = gtk.Image()
        image.set_from_icon_name("gtk-save", gtk.ICON_SIZE_MENU)
        self.add_profile_btn.add(image)
        self.add_profile_btn.connect('clicked', self.save_profile)
        upper_box.pack_start(self.add_profile_btn, False, False, 0)

        self.pack_start(upper_box, False, False, 0)

        # volume control
        for channel in audio_channels:
            init_volume = self.get_volume(channel[1])

            frame = gtk.Frame(channel[0])
            self.pack_start(frame, False, True, 0)

            max_value = self.get_max_volume(channel[1])
            scale_adj = gtk.Adjustment(init_volume, 0.0, max_value, 1.0, 1.0, 0.0)
            scale_adj.connect("value_changed", self.volume_changed_callback, channel[1])
            self.volume_scales.update({channel[1]: scale_adj})
            volume_scale = gtk.HScale(scale_adj)
            volume_scale.set_digits(0)
            frame.add(volume_scale)
#            self.pack_start(volume_scale, False, False, 0)

        self.show_all()

        ### ToDo.
        
