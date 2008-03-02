#!/usr/bin/python
#coding=utf8

WIDTH = 480
HEIGHT = 640

TITLE = "pylgrim"
WM_NAME = "pylgrim"
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
import math

class tile(evas.Image):
    def __init__(self, canvas):
        evas.Image.__init__(self,canvas)
        self.pass_events = True
        self.show()
        self.position = (0,0)
    
    def set_position(self, x, y):
        self.position = (x,y)
        self.move(x,y)

class TestView(edje.Edje):
    def on_key_down(self, obj, event):
        if event.keyname in ("F6", "f"):
            self.evas_canvas.evas_obj.fullscreen = not self.evas_canvas.evas_obj.fullscreen
        elif event.keyname in ("Escape", "q"):
            ecore.main_loop_quit()
        else:
            print "key not recognized:",event.keyname
    
    def download(self, x,y,z):
        import urllib
        webFile = urllib.urlopen("http://a.tile.openstreetmap.org/%d/%d/%d.png"%(z,x,y))
        if not os.path.exists("%d"%z):
            os.mkdir("%d"%z)
        if not os.path.exists("%d/%d"%(z,x)):
            os.mkdir("%d/%d"%(z,x))
        localFile = open("%d/%d/%d.png"%(z,x,y), 'w')
        localFile.write(webFile.read())
        webFile.close()
        localFile.close()

    
    def __init__(self):
        self.options, self.args = myOptionParser(usage="usage: %prog [options]").parse_args()
        
        edje.frametime_set(1.0 / self.options.fps)
        
        self.evas_canvas = EvasCanvas(
            fullscreen=not self.options.no_fullscreen,
            engine=self.options.engine,
            size=self.options.geometry
        )
        
        f = os.path.splitext(sys.argv[0])[0] + ".edj"
        try:
            edje.Edje.__init__(self, self.evas_canvas.evas_obj.evas, file=f, group="main")
        except edje.EdjeLoadError, e:
            raise SystemExit("error loading %s: %s" % (f, e))
        self.size = self.evas_canvas.evas_obj.evas.size
        self.on_key_down_add(self.on_key_down)
        self.focus = True
        self.evas_canvas.evas_obj.data["main"] = self
        self.show()
        
        
        #mouse position
        self.x_pos, self.y_pos = (0,0)
        
        #global variable for zooming
        self.zoom_step = 0.0
        
        #global list for tiles to download
        self.tiles_to_download = []
        self.tiles_to_download_total = 0
        
        #initial lat,lon,zoom
        self.lat = 49.009051
        self.lon = 8.402481
        self.z = 10
        
        self.icons = []
        
        self.overlay = edje.Edje(self.evas_canvas.evas_obj.evas, file=f, group='overlay')
        self.overlay.size = self.evas_canvas.evas_obj.evas.size
        self.overlay.layer = 1
        self.evas_canvas.evas_obj.data["overlay"] = self.overlay
        self.overlay.show()
        
        self.progress_bg = evas.Rectangle(self.evas_canvas.evas_obj.evas)
        self.progress_bg.geometry = 0,0,0,0
        self.progress_bg.color = 255, 255, 255, 255
        self.progress_bg.layer = 2
        self.progress_bg.show()
        
        self.progress = evas.Rectangle(self.evas_canvas.evas_obj.evas)
        self.progress.geometry = 0,0,0,0
        self.progress.color = 255, 0, 0, 255
        self.progress.layer = 3
        self.progress.show()
        
        self.border = 0
        
        self.mouse_down = False
        
        self.animate = False
        
        self.set_current_tile(self.lat, self.lon, self.z)
        
    
    #jump to coordinates
    def set_current_tile(self, lat, lon, z):
        self.z = z
        self.x = (lon+180)/360 * 2**z
        self.y = (1-math.log(math.tan(lat*math.pi/180) + 1/math.cos(lat*math.pi/180))/math.pi)/2 * 2**z
        self.offset_x, self.offset_y = int((self.x-int(self.x))*256),int((self.y-int(self.y))*256)
        self.init_redraw()
        
    def init_redraw(self):
        self.animate = True
        #calculate size of tile raster - reload if it differs from before eg. when size changes
        self.border = int((self.size[0]+self.size[1])/512)+1
        if len(self.icons) != (2*self.border+1)**2:
            print "use", self.border
            #clean up
            for icon in self.icons:
                icon.delete()
            self.icons = []
            #fill
            for i in xrange((2*self.border+1)**2):
                self.icons.append(tile(self.evas_canvas.evas_obj.evas))
        #add all tiles that are not yet downloaded to a list
        for i in xrange(2*self.border+1):
            for j in xrange(2*self.border+1):
                if not os.path.exists("%d/%d/%d.png"%(self.z,self.x+i-self.border,self.y+j-self.border)):
                    self.tiles_to_download.append((self.z,self.x+i-self.border,self.y+j-self.border))
        self.tiles_to_download_total = len(self.tiles_to_download)
        #if there are tiles to download, display progress bar
        if self.tiles_to_download_total > 0:
            self.progress_bg.geometry = 39, self.size[1]/2-1, self.size[0]-78,22
            self.progress.geometry = 40, self.size[1]/2, 1,20
            self.overlay.part_text_set("progress", "downloaded 0 of %d tiles"%self.tiles_to_download_total)
        ecore.timer_add(0.0, self.download_and_paint_current_tiles)
    
    def download_and_paint_current_tiles(self):
        if len(self.tiles_to_download) > 0:
            z,x,y = self.tiles_to_download.pop()
            self.progress.geometry = 40, self.size[1]/2, (self.size[0]-80)*(self.tiles_to_download_total-len(self.tiles_to_download))/self.tiles_to_download_total,20
            self.overlay.part_text_set("progress", "downloaded %d of %d tiles"%(self.tiles_to_download_total-len(self.tiles_to_download),self.tiles_to_download_total))
            self.download(x,y,z)
            return True
        
        #if all tiles are downloaded
        for i in xrange(2*self.border+1):
            for j in xrange(2*self.border+1):
                self.icons[(2*self.border+1)*i+j].file_set("%d/%d/%d.png"%(self.z,self.x+i-self.border,self.y+j-self.border))
                self.icons[(2*self.border+1)*i+j].set_position((i-self.border)*256+self.size[0]/2-self.offset_x,(j-self.border)*256+self.size[1]/2-self.offset_y)
                self.icons[(2*self.border+1)*i+j].size = 256,256
                self.icons[(2*self.border+1)*i+j].fill = 0, 0, 256, 256
        self.current_pos = (0,0)
        self.overlay.part_text_set("progress", "")
        self.progress_bg.geometry = 0,0,0,0
        self.progress.geometry = 0,0,0,0
        self.update_coordinates()
        self.animate = False
        return False
    
    def update_coordinates(self):
        x = int(self.x) + (self.offset_x-self.current_pos[0])/256.0
        y = int(self.y) + (self.offset_y-self.current_pos[1])/256.0
        self.lon = (x*360)/2**self.z-180
        n = math.pi*(1-2*y/2**self.z)
        self.lat = 180/math.pi*math.atan(0.5*(math.exp(n)-math.exp(-n)))
        self.overlay.part_text_set("label", "lat:%f lon:%f zoom:%d"%(self.lat,self.lon,self.z))
    
    def zoom_in(self, z):
        for icon in self.icons:
            x = (1+z)*(icon.position[0]-self.size[0]/2)+self.size[0]/2
            y = (1+z)*(icon.position[1]-self.size[1]/2)+self.size[1]/2
            icon.geometry = int(x),int(y),256+int(256*z),256+int(256*z)
            icon.fill = 0, 0, 256+int(256*z),256+int(256*z)
            
    def zoom_out(self, z):
        for icon in self.icons:
            x = (1-z*0.5)*(icon.position[0]-self.size[0]/2)+self.size[0]/2
            y = (1-z*0.5)*(icon.position[1]-self.size[1]/2)+self.size[1]/2
            icon.geometry = int(x),int(y),256-int(256*z*0.5),256-int(256*z*0.5)
            icon.fill = 0, 0, 256-int(256*z*0.5),256-int(256*z*0.5)
    
    def animate_zoom_in(self):
        if self.z < 18:
            if self.zoom_step < 1.0:
                self.zoom_in(self.zoom_step)
                self.zoom_step+=0.125
                return True
            
            self.zoom_step = 0.0
            self.z+=1
            self.set_current_tile(self.lat, self.lon, self.z)
        return False
        
    def animate_zoom_out(self):
        if self.z > 5:
            if self.zoom_step < 1.0:
                self.zoom_out(self.zoom_step)
                self.zoom_step+=0.125
                return True
            
            self.zoom_step = 0.0
            self.z-=1
            self.set_current_tile(self.lat, self.lon, self.z)
        return False
    
    @edje.decorators.signal_callback("mouse,down,1", "*")
    def on_mouse_down(self, emission, source):
        if not self.animate:
            if source in "plus":
                self.animate = True
                ecore.timer_add(0.05, self.animate_zoom_in)
            if source in "minus":
                self.animate = True
                ecore.timer_add(0.05, self.animate_zoom_out)
            else:
                self.x_pos, self.y_pos = self.evas_canvas.evas_obj.evas.pointer_canvas_xy
                self.mouse_down = True
        
    @edje.decorators.signal_callback("mouse,up,1", "*")
    def on_mouse_up(self, emission, source):
        self.mouse_down = False
        if not self.animate:
            if abs(self.current_pos[0]) > self.size[0]/2 or abs(self.current_pos[1]) > self.size[1]/2:
                self.x = int(self.x) + (self.offset_x-self.current_pos[0])/256.0
                self.y = int(self.y) + (self.offset_y-self.current_pos[1])/256.0
                self.offset_x, self.offset_y = int((self.x-int(self.x))*256),int((self.y-int(self.y))*256)
                self.init_redraw()
            if abs(self.current_pos[0]) > 0 or abs(self.current_pos[1]) > 0:
                #on mouse up + move: update current coordinates
                self.update_coordinates()
        
    @edje.decorators.signal_callback("mouse,move", "*")
    def on_mouse_move(self, emission, source):
        if self.mouse_down and not self.animate:
            x_pos, y_pos = self.evas_canvas.evas_obj.evas.pointer_canvas_xy
            delta_x = self.x_pos - x_pos
            delta_y = self.y_pos - y_pos
            self.x_pos, self.y_pos = x_pos, y_pos
            for icon in self.icons:
                icon.set_position(icon.pos[0]-delta_x,icon.pos[1]-delta_y)
            self.current_pos = (self.current_pos[0]-delta_x,self.current_pos[1]-delta_y)
            
        
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
        self.evas_obj.fullscreen = fullscreen
        self.evas_obj.size = size
        self.evas_obj.show()

    def on_resize(self, evas_obj):
        x, y, w, h = evas_obj.evas.viewport
        size = (w, h)
        for key in evas_obj.data.keys():
            evas_obj.data[key].size = size
        evas_obj.data["main"].init_redraw()

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
        
    def parse_geometry(self, option, opt, value, parser):
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
