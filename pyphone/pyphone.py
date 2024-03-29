#!/usr/bin/python
#coding=utf8

WIDTH = 480
HEIGHT = 640

TITLE = "pyphone"
WM_NAME = "pyphone"
WM_CLASS = "swallow"

import os
import sys
import e_dbus
import evas
import evas.decorators
import edje
import edje.decorators
import ecore
import ecore.evas
from dbus import SystemBus, Interface
from optparse import OptionParser
import time

class edje_group(edje.Edje):
    def __init__(self, main, group):
        self.main = main
        f = os.path.splitext(sys.argv[0])[0] + ".edj"
        try:
            edje.Edje.__init__(self, self.main.evas_canvas.evas_obj.evas, file=f, group=group)
        except edje.EdjeLoadError, e:
            raise SystemExit("error loading %s: %s" % (f, e))
        self.size = self.main.evas_canvas.evas_obj.evas.size
    
    @edje.decorators.signal_callback("transition:*", "*")
    def on_edje_signal_transition(self, emission, source):
        if not self.main.in_transition:
            self.main.in_transition = True
            self.main.transition_to(emission.split(':')[1])
        
    @edje.decorators.signal_callback("finished_transition", "*")
    def on_edje_signal_finished_transition(self, emission, source):
        self.main.transition_finished()
        self.main.in_transition = False

class pyphone_main(edje_group):
    def __init__(self, main):
        edje_group.__init__(self, main, "main")
    
class pyphone_phone(edje_group):
    def __init__(self, main):
        edje_group.__init__(self, main, "phone")
        self.text = []
        
    @edje.decorators.signal_callback("dialer_button_pressed", "*")
    def on_edje_signal_dialer_button_pressed(self, emission, source):
        if "button_" in source:
            key = source.split("_", 1)[1]
            if key in ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "#"):
                self.text.append(key)
                self.part_text_set("label", "".join(self.text))
            elif key in "star":
                self.text.append("*")
                self.part_text_set("label", "".join(self.text))
            elif key in "delete":
                self.text = self.text[:-1]
                self.part_text_set("label", "".join(self.text))
        else:
            key = source
        #self.text.append(source)
        #self.part_text_set("label", "".join(self.text))
        
class pyphone_sms(edje_group):
    def __init__(self, main):
        edje_group.__init__(self, main, "sms")
        self.text = []
        self.button_labels2 = [
            [
                [".,?!", "abc", "def", ""],
                ["ghi", "jkl", "mno", ""],
                ["pqrs", "tuv", "wxyz", ""],
                ["", "", "⇦⇧⇨", ""],
            ],
            [
                ["", "", "", ""],
                ["", "", "", ""],
                ["", "", "", ""],
                ["", "", "", ""],
            ]
        ]
        self.button_labels = [
            [
                ["1", "2", "3", "↤"],
                ["4", "5", "6", "↲"],
                ["7", "8", "9", "Abc"],
                ["+", "0", "⇩", "+"],
            ],
            [
                ["1", "?", "", ""],
                [".", ",", "", ""],
                ["!", "", "", ""],
                ["", "", "", ""],
            ],
            [
                ["", "2", "c", ""],
                ["", "a", "b", ""],
                ["", "", "", ""],
                ["", "", "", ""],
            ],
            [
                ["", "", "3", "f"],
                ["", "", "d", "e"],
                ["", "", "", ""],
                ["", "", "", ""],
            ],
            [
                ["", "", "", "↤"],
                ["", "", "", ""],
                ["", "", "", ""],
                ["", "", "", ""],
            ],
            [
                ["", "", "", ""],
                ["4", "i", "", ""],
                ["g", "h", "", ""],
                ["", "", "", ""],
            ],
            [
                ["", "", "", ""],
                ["", "5", "l", ""],
                ["", "j", "k", ""],
                ["", "", "", ""],
            ],
            [
                ["", "", "", ""],
                ["", "", "6", "o"],
                ["", "", "m", "n"],
                ["", "", "", ""],
            ],
            [
                ["", "", "", ""],
                ["", "", "", ""],
                ["", "", "", ""],
                ["", "", "", ""],
            ],
            [
                ["", "", "", ""],
                ["", "s", "", ""],
                ["7", "r", "", ""],
                ["p", "q", "", ""],
            ],
            [
                ["", "", "", ""],
                ["", "", "", ""],
                ["", "8", "v", ""],
                ["", "t", "u", ""],
            ],
            [
                ["", "", "", ""],
                ["", "", "", "z"],
                ["", "", "9", "y"],
                ["", "", "w", "x"],
            ],
            [
                ["", "", "", ""],
                ["", "", "", ""],
                ["", "", "", ""],
                ["", "", "", ""],
            ],
            [
                ["", "", "", ""],
                ["", "", "", ""],
                ["", "", "", ""],
                ["", "", "", ""],
            ],
            [
                ["", "", "", ""],
                ["", "", "", ""],
                ["", "", "", ""],
                ["", " ", "", ""],
            ],
            [
                ["", "", "", ""],
                ["", "", "", ""],
                ["", "", "⇧", ""],
                ["", "⇦", "⇩", "⇨"],
            ],
            [
                ["", "", "", ""],
                ["", "", "", ""],
                ["", "", "", ""],
                ["", "", "", ""],
            ]
        ]
        self.set_button_text(0)
        self.active = 0
        
    @edje.decorators.signal_callback("kb_button_mouse_up", "*")
    def on_edje_signal_dialer_button_mouse_up(self, emission, source):
        now = time.time()
        x = int(source[-3:-2])
        y = int(source[-1:])
        key = self.button_labels[self.active][y][x]
        self.text.append(key)
        self.part_text_set("label", "".join(self.text))
        self.set_button_text(0)
        print "mouse up:", time.time()-now
        
    @edje.decorators.signal_callback("kb_button_mouse_down", "*")
    def on_edje_signal_dialer_button_mouse_down(self, emission, source):
        now = time.time()
        x = int(source[-3:-2])
        y = int(source[-1:])
        num = 4*y+x+1
        if self.active == 0:
            self.set_button_text(num)
        print "mouse down:", time.time()-now
        
        
    @edje.decorators.signal_callback("kb_mutton_mouse_in", "*")
    def on_edje_signal_dialer_button_mouse_in(self, emission, source):
        now = time.time()
        x = int(source[-3:-2])
        y = int(source[-1:])
        self.part_text_set("label_preview", self.button_labels[self.active][y][x])
        print "mouse in:", time.time()-now
    
    def set_button_text(self, num):
        for i in xrange(4):
            for j in xrange(4):
                self.part_text_set("label_%d_%d" % (i,j) , self.button_labels[num][j][i])
        self.active = num
        
        if num != 0:
            num = 1

        for i in xrange(4):
            for j in xrange(4):
                self.part_text_set("label2_%d_%d" % (i,j) , self.button_labels2[num][j][i])
        
class TestView(object):
    def on_key_down(self, obj, event):
        if event.keyname in ("F6", "f"):
            self.evas_canvas.evas_obj.fullscreen = not self.evas_canvas.evas_obj.fullscreen
        elif event.keyname == "Escape":
            ecore.main_loop_quit()

    def __init__(self):
        self.options, self.args = myOptionParser(usage="usage: %prog [options]").parse_args()
        
        edje.frametime_set(1.0 / self.options.fps)
        
        self.evas_canvas = EvasCanvas(
            fullscreen=not self.options.no_fullscreen,
            engine=self.options.engine,
            size=self.options.geometry
        )
        
        self.groups = {}
        for part in ("swallow", "main", "contacts", "power"):
            self.groups[part] = edje_group(self, part)
            self.evas_canvas.evas_obj.data[part] = self.groups[part]
        
        self.groups["sms"] = pyphone_sms(self)
        self.evas_canvas.evas_obj.data["sms"] = self.groups["sms"]
        self.groups["phone"] = pyphone_phone(self)
        self.evas_canvas.evas_obj.data["phone"] = self.groups["phone"]
        
        self.groups["swallow"].show()
        self.groups["swallow"].on_key_down_add(self.on_key_down)
        
        self.groups["swallow"].part_swallow("swallow2", self.groups["main"])
        self.current_group = self.groups["main"]
        self.previous_group = self.groups["phone"]
        self.in_transition = False
        ecore.timer_add(1.0, self.display_time)
        self.display_time()

    def display_time(self):
        self.groups["main"].part_text_set("label", time.strftime("%H:%M:%S", time.localtime()));
        return True;
    
    def transition_to(self, target):
        print "transition to", target
        
        self.previous_group = self.current_group
        
        self.current_group = self.groups[target]
        self.current_group.signal_emit("visible", "")
        self.groups["swallow"].part_swallow("swallow1", self.current_group)
        self.previous_group.signal_emit("fadeout", "")
    
    def transition_finished(self):
        print "finished"
        self.previous_group.hide()
        self.groups["swallow"].part_swallow("swallow2", self.current_group)
        

class EvasCanvas(object):
    def __init__(self, fullscreen, engine, size):
        if engine == "x11":
            f = ecore.evas.SoftwareX11
        elif engine == "x11-16":
            if ecore.evas.engine_type_supported_get("software_x11_16"):
                f = ecore.evas.SoftwareX11_16
            else:
                print "warning: x11-16 is not supported, fallback to x11"
                f = ecore.evas.SoftwareX11

        self.evas_obj = f(w=size[0], h=size[1])
        self.evas_obj.callback_delete_request = self.on_delete_request
        self.evas_obj.callback_resize = self.on_resize

        self.evas_obj.title = TITLE
        self.evas_obj.name_class = (WM_NAME, WM_CLASS)
        self.evas_obj.fullscreen = False #fullscreen
        self.evas_obj.size = size
        self.evas_obj.show()

    def on_resize(self, evas_obj):
        x, y, w, h = evas_obj.evas.viewport
        size = (w, h)
        for key in evas_obj.data.keys():
            evas_obj.data[key].size = size

    def on_delete_request(self, evas_obj):
        ecore.main_loop_quit()

class myOptionParser(OptionParser):
    def __init__(self, usage):
        OptionParser.__init__(self, usage)
        self.add_option("-e",
                      "--engine",
                      type="choice",
                      choices=("x11", "x11-16"),
                      default="x11-16",
                      help=("which display engine to use (x11, x11-16), "
                            "default=%default"))
        self.add_option("-n",
                      "--no-fullscreen",
                      action="store_true",
                      help="do not launch in fullscreen")
        self.add_option("-g",
                      "--geometry",
                      type="string",
                      metavar="WxH",
                      action="callback",
                      callback=self.parse_geometry,
                      default=(WIDTH, HEIGHT),
                      help="use given window geometry")
        self.add_option("-f",
                      "--fps",
                      type="int",
                      default=20,
                      help="frames per second to use, default=%default")
        
    def parse_geometry(option, opt, value, parser):
        try:
            w, h = value.split("x")
            w = int(w)
            h = int(h)
        except Exception, e:
            raise optparse.OptionValueError("Invalid format for %s" % option)
        parser.values.geometry = (w, h)

class dbus(object):
    def __init__(self):
        try:
            obj = SystemBus(mainloop=e_dbus.DBusEcoreMainLoop()).get_object('org.mobile.gsm', '/org/mobile/gsm/RemoteObject')
        except Exception, e:
            print e
            raise SystemExit

        #connect functions to dbus events
        dbus_interface = 'org.mobile.gsm.RemoteInterface'
        for fkt in (self.modem_info, self.sim_info, self.network_info, self.gsmCRING, self.gsmNO_CARRIER, self.gsmBUSY, self.error,):
            obj.connect_to_signal(fkt.__name__, fkt, dbus_interface=dbus_interface)
        gsm = Interface(obj, dbus_interface)

        #get status info on startup
        gsm.FireModemInfo()
        gsm.FireNetworkInfo()
    
    def modem_info(self, array):
        print array

    def sim_info(self, array):
        print array
        
    def network_info(self, array):
        print array
        
    def gsmBUSY(self, string):
        print string

    def gsmCRING(self, string):
        print string

    def gsmNO_CARRIER(self, *values):
        print values

    def error(self, string):
        print string

if __name__ == "__main__":
    TestView()
    #dbus()
    ecore.main_loop_begin()

'''
export CPPFLAGS="$CPPFLAGS -I/opt/e17/include"
export LDFLAGS="$LDFLAGS -L/opt/e17/lib"
export PKG_CONFIG_PATH="/opt/e17/lib/pkgconfig:$PKG_CONFIG_PATH"
export PATH="$PATH:/opt/e17/bin"
export PYTHONPATH="/home/josch/usr/lib/python2.5/site-packages"
'''
