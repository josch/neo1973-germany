from PyTrackerClient import *
import ecore
import ecore.evas
import edje
import sys
import os
import atexit

atexit.register(test.StopTrack())

test=TrackClient('anon','passwd','80.61.221.9')


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
ee.title = "test"
ee.name_class = ("test", "test")
canvas = ee.evas
#edje_file = os.path.join(os.path.dirname(sys.argv[0]), "PyTracker.edj")
edje_file = 'data/PyTracker.edj'
try:
    edje_obj = edje.Edje(canvas, file=edje_file, group="test")
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


def icon_selected(edje_obj, signal, source):
	if signal == "StartSelected":
		test.StartTrack()
	elif signal == "StopSelected":
		test.StopTrack()

edje_obj.signal_callback_add("StartSelected", "*", icon_selected)
edje_obj.signal_callback_add("StopSelected", "*", icon_selected)

# Give focus to object, show window and enter event loop
edje_obj.focus = True
ee.show()

#ecore.main_loop_begin()
ee.evas.image_cache_set( 6*1024*1024 )
ecore.main_loop_begin()
