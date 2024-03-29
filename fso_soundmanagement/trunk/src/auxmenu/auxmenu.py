#!/usr/bin/python
'''
authors: Pau1us <paulus.mail@oleco.net>
license: gpl v2 or later
auxmenu is a small menu to mute the phone, take screenshots, lock the display, send to standby and shutdown. It is intended to appear, if AUX is pressed.
'''

import ecore
import ecore.evas
import edje
import sys
import os
import e_dbus
import time
from dbus import SystemBus, Interface


if ecore.evas.engine_type_supported_get("software_x11_16"):
    f = ecore.evas.SoftwareX11_16
else:
    print "warning: x11-16 is not supported, fallback to x11"
    f = ecore.evas.SoftwareX11
ee = f(w=640, h=480)
ee.fullscreen = 1 


# Load and setup UI
ee.title = "auxmenu"
ee.name_class = ("auxmenu", "auxmenu")
canvas = ee.evas
edje_file = os.path.join(os.path.dirname(sys.argv[0]), "auxmenu.edj")

try:
    edje_obj = edje.Edje(canvas, file=edje_file, group="main")
except Exception, e: # should be EdjeLoadError, but it's wrong on python2.5
    raise SystemExit("Failed to load Edje file: %s" % edje_file)

# resize edje to fit our window, show and remember it for later use
edje_obj.size = canvas.size
edje_obj.show()
ee.data["edje"] = edje_obj


# Setup callbacks for resize, keydown and selected item
def resize_cb(ee):
    r = ee.evas.rect
    ee.data["edje"].size = r.size

ee.callback_resize = resize_cb


class auxmenuclass:
  def __init__(self, edje_obj):
    print "init"
    #DBus:
    self.systembus=systembus = SystemBus(mainloop=e_dbus.DBusEcoreMainLoop())
    self.odeviced_proxy = self.systembus.get_object('org.freesmartphone.oeventsd', '/org/freesmartphone/Preferences')
    self.Preferences_iface = Interface(self.odeviced_proxy, 'org.freesmartphone.Preferences')
    self.ousaged_proxy = self.systembus.get_object('org.freesmartphone.ousaged', '/org/freesmartphone/Usage')
    self.Usage_iface = Interface(self.ousaged_proxy, 'org.freesmartphone.Usage')
    
    self.profile = self.Preferences_iface.GetProfile()
    if self.profile == "silent" or self.profile == "headset_silent":
      edje_obj.part_text_set("text_mute", "UNMUTE")
    else:
      edje_obj.part_text_set("text_mute", "MUTE")
    
  def button_pressed(self, edje_obj, signal, source):
    if signal == "mute":
      print "mute"
      self.mute()
    elif signal == "snapshot":
      print "snapshot"
      os.system("gpe-scap &")
    elif signal == "lock":
      print "lock"
    elif signal == "standby":
      print "standby"
      #os.system("apm -s")
      self.Usage_iface.Suspend()
    elif signal == "shutdown":
      print "shutdown"
      os.system("poweroff")
    ecore.main_loop_quit()
  def mute(self):
    if self.profile == "default":
      self.Preferences_iface.SetProfile("silent")
      os.system("alsactl restore -f /usr/share/openmoko/scenarios/silent.state")
    elif self.profile == "headset":
      self.Preferences_iface.SetProfile("headset_silent")
      os.system("alsactl restore -f /usr/share/openmoko/scenarios/headset.state")
    elif self.profile == "silent":
      self.Preferences_iface.SetProfile("default")
      os.system("alsactl restore -f /usr/share/openmoko/scenarios/stereoout.state")
    elif self.profile == "headset_silent":
      self.Preferences_iface.SetProfile("headset")
      os.system("alsactl restore -f /usr/share/openmoko/scenarios/headset.state")

menu = auxmenuclass(edje_obj)

edje_obj.signal_callback_add("*", "button", menu.button_pressed)



# Give focus to object, show window and enter event loop
edje_obj.focus = True
ee.show()

ecore.main_loop_begin()
