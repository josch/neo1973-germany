#!/usr/bin/python
'''
authors: Pau1us <paulus.mail@oleco.net>
license: gpl v2 or later
PyBat is a tool to set usb in host or devices mode aund to set the charging speed.
'''

import ecore
import ecore.evas
import edje
import sys
import os
import e_dbus
from dbus import SystemBus, Interface


if ecore.evas.engine_type_supported_get("software_x11_16"):
     f = ecore.evas.SoftwareX11_16
else:
     print "warning: x11-16 is not supported, fallback to x11"
     f = ecore.evas.SoftwareX11

ee = f(w=640, h=480)
ee.fullscreen = 0


# Load and setup UI
ee.title = "PyBat"
ee.name_class = ("pybat", "pybat")
canvas = ee.evas
edje_file = os.path.join(os.path.dirname(sys.argv[0]), "PyBat.edj")
#edje_file = 'PyBat.edj'
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

class PyBatclass:
  def __init__(self, edje_obj):
    self.system = os.uname()[2][0:6]
    if self.system == "2.6.27":
      self.filePowerpath = "/sys/devices/platform/s3c2440-i2c/i2c-adapter/i2c-0/0-0073/"
      self.filehostmodepath = "/sys/devices/platform/s3c2410-ohci/"
    elif self.system == "2.6.28":
      self.filePowerpath = "/sys/devices/platform/s3c2440-i2c/i2c-adapter:i2c-0/0-0073/pcf50633-mbc/"
      self.filehostmodepath = "/sys/class/i2c-adapter/i2c-0/0-0073/neo1973-pm-host.0/"
    self.filePower = os.open( self.filePowerpath+"force_usb_limit_dangerous", os.O_RDWR )
    self.filePowerread = os.open( self.filePowerpath+"usb_curlim", os.O_RDONLY )
    self.fileusbmode = open( "/sys/devices/platform/s3c2410-ohci/usb_mode", "r+" )
    self.filehostmode = os.open( self.filehostmodepath+"hostmode", os.O_RDWR )
    self.mode = self.fileusbmode.readline()
    self.power = str(os.read(self.filePowerread, 4))
    self.mode = self.mode.split()[0]
    self.power = self.power.split()[0]
    #print self.mode
    #print "l%st" % (self.power)
    edje_obj.signal_emit("%s" % (self.mode), "is_clicked")
    edje_obj.signal_emit("l%s" % (self.power), "is_clicked")
#DBus:
#    self.systembus=systembus = SystemBus(mainloop=e_dbus.DBusEcoreMainLoop())
#    self.odeviced_proxy = self.systembus.get_object('org.freesmartphone.odeviced', '/org/freesmartphone/Device/PowerControl/UsbHost')
#    self.PowerControl_iface = Interface(self.odeviced_proxy, 'org.freesmartphone.Device.PowerControl')

  def write_data(self, usbmode, power):
        if usbmode == "host":
          self.fileusbmode.write("host")
          #print "#echo host > /sys/devices/platform/s3c2410-ohci/usb_mode"
          if power == "-500":
            os.system("ifdown usb0 &")
            #dbus:
            #self.PowerControl_iface.SetPower(1)
            os.write(self.filehostmode, "1")
            #print "#echo 1 > /sys/devices/platform/neo1973-pm-host.0/hostmode"
          else:
            os.system("ifdown usb0 &")
            os.write(self.filehostmode, "0")
            #print "#echo 0 > /sys/devices/platform/neo1973-pm-host.0/hostmode"
            os.write(self.filePower, power)
            #print "#echo %s > /sys/class/i2c-adapter/i2c-0/0-0073/force_usb_limit_dangerous" % (power)
        elif usbmode == "device":
          if power != "-500":
            self.fileusbmode.write("device")
            #print "#echo device > /sys/devices/platform/s3c2410-ohci/usb_mode"
            os.write(self.filehostmode, "0")
            #print "#echo 0 > /sys/devices/platform/neo1973-pm-host.0/hostmode"
            #self.PowerControl_iface.SetPower(0)
            os.system("ifup usb0 &")
            os.write(self.filePower, power)
            #print "#echo %s > /sys/class/i2c-adapter/i2c-0/0-0073/force_usb_limit_dangerous" % (power)
        
  def button_pressed(self, edje_obj, signal, source):
        if source == "usbmode":
                self.mode = signal
                if self.mode == "device" and self.power == "-500":
                  edje_obj.part_text_set("text_field", "won't work!")
                else:
                  edje_obj.part_text_set("text_field", "")
        elif source == "power":
                self.power = signal
                if signal != "-500":
                  if self.mode == "device":
                    edje_obj.signal_emit("hide_provide", "") 
                  elif self.mode == "host":
                   edje_obj.signal_emit("l-500", "is_default")
                if signal == "0":
                   edje_obj.part_text_set("text_field", "")
                elif signal == "100":
                   edje_obj.part_text_set("text_field", "")
                elif signal == "500":
                   edje_obj.part_text_set("text_field", "make shure your charger can provide 0.5A")
                elif signal == "1000":
                   edje_obj.part_text_set("text_field", "make shure your charger can provide 1A")
                elif signal == "500":
                   edje_obj.part_text_set("text_field", "")
        elif source == "programm":
                if signal == "ok":
                        self.write_data(self.mode, self.power)
                        ecore.main_loop_quit()
                elif signal == "cancel":
                        ecore.main_loop_quit()

test = PyBatclass(edje_obj)
edje_obj.signal_callback_add("*", "*", test.button_pressed)

# Give focus to object, show window and enter event loop
edje_obj.focus = True
ee.show()

ecore.main_loop_begin()

