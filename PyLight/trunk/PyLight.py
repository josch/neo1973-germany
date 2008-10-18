#!/usr/bin/python
'''
authors: Pau1us <paulus.mail@oleco.net>
license: gpl v2 or later
PyLight is a small application to set the display to a selectable color
'''

import ecore
import ecore.evas
import edje
import sys
import os

#from testclass import *

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
ee.title = "PyLight"
ee.name_class = ("pylight", "pylight")
canvas = ee.evas
edje_file = os.path.join(os.path.dirname(sys.argv[0]), "PyLight.edj")
#edje_file = 'PyLight.edj'
try:
    edje_obj = edje.Edje(canvas, file=edje_file, group="main")
except Exception, e: # should be EdjeLoadError, but it's wrong on python2.5
    raise SystemExit("Failed to load Edje file: %s" % edje_file)

# resize edje to fit our window, show and remember it for later use
edje_obj.size = canvas.size
edje_obj.show()
ee.data["edje"] = edje_obj

edje_obj.signal_emit("off", "light")

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

def drag(edje_obj, signal, source):
  drag.x,drag.y = edje_obj.part_drag_value_get("slider_red")
  drag.red = (drag.x -1) * (-255)
  drag.x,drag.y = edje_obj.part_drag_value_get("slider_green")
  drag.green = (drag.x -1) * (-255)
  drag.x,drag.y = edje_obj.part_drag_value_get("slider_blue")
  drag.blue = (drag.x -1) * (-255)
  #print "x: %s\n" % (drag.xx)
  edje.color_class_set("user_color", drag.red, drag.green, drag.blue, 255, 0, 0, 0, 0, 0, 0, 0, 0)
  #print "%s , %s\n" % ( source, signal)
edje_obj.on_key_down_add(key_down_cb, ee)

def click_ok(edje_obj, signal, source):
  ee.fullscreen = 1
  edje_obj.signal_emit("on", "light")
  
def click_back(edje_obj, signal, source):
  ee.fullscreen = 0
  edje_obj.signal_emit("off", "light")
  
def click_close(edje_obj, signal, source):
  ecore.main_loop_quit()


#test = testclass(edje_obj)
edje_obj.signal_callback_add("drag", "slider_*", drag)
edje_obj.signal_callback_add("ok", "programm", click_ok)
edje_obj.signal_callback_add("close", "programm", click_close)
edje_obj.signal_callback_add("back", "programm", click_back)
#edje_obj.signal_callback_add("StopSelected", "*", icon_selected)

# Give focus to object, show window and enter event loop
edje_obj.focus = True
ee.show()





#ecore.main_loop_begin()
ecore.main_loop_begin()

