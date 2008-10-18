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

# Parse command line
from optparse import OptionParser

def parse_geometry(option, opt, value, parser):
    try:
        w, h = value.split("x")
        w = int(w)
        h = int(h)
    except Exception, e:
        raise optparse.OptionValueError("Invalid format for %s" % option)
    parser.values.geometry = (w, h)

usage = "usage: %prog [options]"
op = OptionParser(usage=usage)
op.add_option("-e", "--engine", type="choice",
              choices=("x11", "x11-16"), default="x11-16",
              help=("which display engine to use (x11, x11-16), "
                    "default=%default"))
op.add_option("-n", "--no-fullscreen", action="store_true",
              help="do not launch in fullscreen")
op.add_option("-g", "--geometry", type="string", metavar="WxH",
              action="callback", callback=parse_geometry,
              default=(480, 640),
              help="use given window geometry")
op.add_option("-f", "--fps", type="int", default=50,
              help="frames per second to use, default=%default")


# Handle options and create output window
options, args = op.parse_args()
if options.engine == "x11":
    f = ecore.evas.SoftwareX11
elif options.engine == "x11-16":
    if ecore.evas.engine_type_supported_get("software_x11_16"):
        f = ecore.evas.SoftwareX11_16
    else:
        print "warning: x11-16 is not supported, fallback to x11"
        f = ecore.evas.SoftwareX11

w, h = options.geometry
ee = f(w=w, h=h)
ee.fullscreen = 0 # not options.no_fullscreen
edje.frametime_set(1.0 / options.fps)


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


def key_down_cb(bg, event, ee):
    k = event.key
    if k == "Escape":
        ecore.main_loop_quit()
    if k in ("F6", "f"):
        ee.fullscreen = not ee.fullscreen

edje_obj.on_key_down_add(key_down_cb, ee)


class PyBatclass:
  def __init__(self, edje_obj):
    self.filePower = os.open( "/sys/devices/platform/s3c2440-i2c/i2c-adapter/i2c-0/0-0073/force_usb_limit_dangerous", os.O_RDWR )
    self.filePowerread = os.open( "/sys/devices/platform/s3c2440-i2c/i2c-adapter/i2c-0/0-0073/usb_curlim", os.O_RDONLY )
    self.fileusbmode = open( "/sys/devices/platform/s3c2410-ohci/usb_mode", "r+" )
    self.filehostmode = os.open( "/sys/devices/platform/neo1973-pm-host.0/hostmode", os.O_RDWR )
    self.mode = self.fileusbmode.readline()
    self.power = str(os.read(self.filePowerread, 4))
    # while self.mode[-1] == whitespace:
    #  self.mode = self.mode[:-1]
    self.mode = self.mode.split()[0]
    #while self.power[-1] == whitespace:
    #  self.power = self.power[:-1] 
    self.power = self.power.split()[0]
    print self.mode
    print "l%st" % (self.power)
    edje_obj.signal_emit("%s" % (self.mode), "is_clicked")
    edje_obj.signal_emit("l%s" % (self.power), "is_clicked")
    
    self.systembus=systembus = SystemBus(mainloop=e_dbus.DBusEcoreMainLoop())
    
    self.odeviced_proxy = self.systembus.get_object('org.freesmartphone.odeviced', '/org/freesmartphone/Device/PowerControl/UsbHost')
    self.PowerControl_iface = Interface(self.odeviced_proxy, 'org.freesmartphone.Device.PowerControl')

  def write_data(self, usbmode, power):
        if usbmode == "host":
          if power == "-500":
            os.system("ifdown usb0 &")
            #dbus:
            self.PowerControl_iface.SetPower(1)
            print "#echo 1 > /sys/devices/platform/neo1973-pm-host.0/hostmode"
          else:
            os.system("ifdown usb0 &")
            self.fileusbmode.write("host")
            print "#echo host > /sys/devices/platform/s3c2410-ohci/usb_mode"
            os.write(self.filehostmode, "0")
            print "#echo 0 > /sys/devices/platform/neo1973-pm-host.0/hostmode"
            os.write(self.filePower, power)
            print "#echo %s > /sys/class/i2c-adapter/i2c-0/0-0073/force_usb_limit_dangerous" % (power)
        elif usbmode == "device":
          if power != "-500":
            self.PowerControl_iface.SetPower(0)
            os.system("ifup usb0 &")
            print "#echo device > /sys/devices/platform/s3c2410-ohci/usb_mode"
            print "#echo 0 > /sys/devices/platform/neo1973-pm-host.0/hostmode"
            os.write(self.filePower, power)
            print "#echo %s > /sys/class/i2c-adapter/i2c-0/0-0073/force_usb_limit_dangerous" % (power)
        
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
#edje_obj.signal_callback_add("StopSelected", "*", icon_selected)

# Give focus to object, show window and enter event loop
edje_obj.focus = True
ee.show()





#ecore.main_loop_begin()
ecore.main_loop_begin()

