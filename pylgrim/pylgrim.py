#!/usr/bin/python
#coding=utf8
'''
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

#TODO: restructure tile loading
#TODO: add wikipedia geotagging
#TODO: add dynamic preloading
#TODO: add gps connection

import os
import sys
from e_dbus import DBusEcoreMainLoop
import evas
import evas.decorators
import edje
import edje.decorators
import ecore
import ecore.evas
from dbus import SystemBus, Interface
import time
import math
import urllib

class Tile(evas.Image):
    def __init__(self, canvas):
        evas.Image.__init__(self,canvas)
        self.pass_events = True
        self.show()
        #we need this to store the original position while the zoom animations
        self.position = (0,0)

    def set_position(self, x, y):
        self.position = (x,y)
        self.move(x,y)

class Mark(evas.Image):
    def __init__(self, canvas):
        evas.Image.__init__(self,canvas)
        self.pass_events = True
        self.show()
        #we need this to store the original position while the zoom animations
        self.position = (0,0)

    def set_position(self, x, y):
        self.position = (x,y)
        self.move(x,y)

class Pylgrim(edje.Edje):
    def __init__(self, evas_canvas, filename, initial_lat, initial_lon, initial_zoom=10, offline=False, use_overlay=True):
        self.evas_canvas = evas_canvas
        self.offline = offline
        self.use_overlay = use_overlay

        edje.Edje.__init__(self, self.evas_canvas.evas_obj.evas, file=filename, group="pylgrim")
        self.size = self.evas_canvas.evas_obj.evas.size
        self.on_key_down_add(self.on_key_down)
        self.on_key_up_add(self.on_key_up)
        self.focus = True
        self.evas_canvas.evas_obj.data["pylgrim"] = self
        self.show()

        #mouse position
        self.x_pos, self.y_pos = (0,0)

        #global variable for zooming
        self.zoom_step = 0.0

        #global list for tiles to download
        self.tiles_to_download = []
        self.tiles_to_download_total = 0
        self.tiles_to_preload = []

        #initial lat,lon,zoom
        self.lat = 0
        self.lon = 0
        self.x = 0
        self.y = 0
        self.z = 0
        self.offset_x = 0
        self.offset_y = 0

        self.icons = []

        self.overlay = edje.Edje(self.evas_canvas.evas_obj.evas, file=filename, group='overlay')
        self.overlay.size = self.evas_canvas.evas_obj.evas.size
        self.overlay.layer = 2
        self.evas_canvas.evas_obj.data["overlay"] = self.overlay
        self.overlay.show()
        if self.use_overlay:

            self.progress_bg = evas.Rectangle(self.evas_canvas.evas_obj.evas)
            self.progress_bg.geometry = 0,0,0,0
            self.progress_bg.color = 255, 255, 255, 255
            self.progress_bg.layer = 3
            self.progress_bg.show()

            self.progress = evas.Rectangle(self.evas_canvas.evas_obj.evas)
            self.progress.geometry = 0,0,0,0
            self.progress.color = 255, 0, 0, 255
            self.progress.layer = 4
            self.progress.show()

        #calculate size of tile raster
        self.border_x = int(math.ceil(self.size[0]/256.0))
        self.border_y = int(math.ceil(self.size[1]/256.0))

        self.mouse_down = False

        self.animate = False

        self.set_current_tile(initial_lat, initial_lon, initial_zoom)

        '''
        self.marker = Mark(self.evas_canvas.evas_obj.evas)
        self.marker.file_set("blue-dot.png")
        self.marker.lat = 49.073866
        self.marker.lon = 8.184814
        self.marker.size_set(32,32)
        self.marker.fill_set(0,0,32,32)
        self.marker.x = (self.marker.lon+180)/360 * 2**self.z
        self.marker.y = (1-math.log(math.tan(self.marker.lat*math.pi/180) + 1/math.cos(self.marker.lat*math.pi/180))/math.pi)/2 * 2**self.z
        self.marker.offset_x, self.marker.offset_y = int((self.marker.x-int(self.marker.x))*256),int((self.marker.y-int(self.marker.y))*256)
        self.marker.set_position(self.size[0]/2-16+256*(int(self.marker.x)-int(self.x))+self.marker.offset_x-self.offset_x, self.size[1]/2-32+256*(int(self.marker.y)-int(self.y))+self.marker.offset_y-self.offset_y)
        self.marker.layer = 1
        self.marker.show()
        '''

        ecore.timer_add(3, self.init_dbus)

    def init_dbus(self):
        print 'LocationFeed init_dbus'
        try:
            gps_obj = SystemBus(mainloop=DBusEcoreMainLoop()).get_object('org.mobile.gps', '/org/mobile/gps/RemoteObject')
            gps_name = 'org.mobile.gps.RemoteInterface'
            gps_obj.connect_to_signal("position", self.position, dbus_interface=gps_name)
            self.gps_interface = Interface(gps_obj, gps_name)
            #self.gps_interface.get_position()
            return False
        except Exception, e:
            print 'LocationFeed', e
            return True

    def on_key_down(self, obj, event):
        if event.keyname in ("F6", "f"):
            self.evas_canvas.evas_obj.fullscreen = not self.evas_canvas.evas_obj.fullscreen
        elif event.keyname in ("Escape", "q"):
            ecore.main_loop_quit()
        elif event.keyname in ("F7","plus") and not self.animate:
            ecore.timer_add(0.05, self.animate_zoom_in)
        elif event.keyname in ("F8","minus") and not self.animate:
            ecore.timer_add(0.05, self.animate_zoom_out)
        elif event.keyname in ("Up",) and not self.animate:
            delta_y = -10
            for icon in self.icons:
                icon.set_position(icon.pos[0],icon.pos[1]-delta_y)
            self.current_pos = (self.current_pos[0],self.current_pos[1]-delta_y)
        elif event.keyname in ("Down",) and not self.animate:
            delta_y = 10
            for icon in self.icons:
                icon.set_position(icon.pos[0],icon.pos[1]-delta_y)
            self.current_pos = (self.current_pos[0],self.current_pos[1]-delta_y)
        elif event.keyname in ("Left",) and not self.animate:
            delta_x = -10
            for icon in self.icons:
                icon.set_position(icon.pos[0]-delta_x,icon.pos[1])
            self.current_pos = (self.current_pos[0]-delta_x,self.current_pos[1])
        elif event.keyname in ("Right",) and not self.animate:
            delta_x = 10
            for icon in self.icons:
                icon.set_position(icon.pos[0]-delta_x,icon.pos[1])
            self.current_pos = (self.current_pos[0]-delta_x,self.current_pos[1])
        else:
            print "key not recognized:",event.keyname

    def on_key_up(self, obj, event):
        if event.keyname in ("Up","Down", "Left", "Right") and not self.animate:
            if abs(self.current_pos[0]) > self.size[0]/2 or abs(self.current_pos[1]) > self.size[1]/2:
                self.x = int(self.x) + (self.offset_x-self.current_pos[0])/256.0
                self.y = int(self.y) + (self.offset_y-self.current_pos[1])/256.0
                self.offset_x, self.offset_y = int((self.x-int(self.x))*256),int((self.y-int(self.y))*256)
                self.init_redraw()
            self.update_coordinates()

    def download(self, x,y,z):
        filename = "%d/%d/%d.png"%(z,x,y)
        print 'download', filename
        try:
            dirname = "%d/%d"%(z,x)
            if not os.path.exists(dirname):
                    os.makedirs(dirname)
            localFile = open(filename, 'w')
            webFile = urllib.urlopen("http://a.tile.openstreetmap.org/%d/%d/%d.png"%(z,x,y))
            localFile.write(webFile.read())
            webFile.close()
            localFile.close()
        except Exception, e:
            print 'download error', e
            if os.path.exists(filename):
                os.unlink(filename)

    def position(self, content):
        latitude = float(content.get('latitude', self.lat))
        longitude = float(content.get('longitude', self.lon))
        print 'position', latitude, longitude
        if not self.animate:
            self.set_current_tile(latitude, longitude, self.z)

    #jump to coordinates
    def set_current_tile(self, lat, lon, z):
        x = (lon+180)/360 * 2**z
        y = (1-math.log(math.tan(lat*math.pi/180) + 1/math.cos(lat*math.pi/180))/math.pi)/2 * 2**z
        offset_x, offset_y = int((x-int(x))*256),int((y-int(y))*256)
        #only redraw if x, y, z, offset_x or offset_y differ from before
        if int(x) != int(self.x) \
        or int(y) != int(self.y) \
        or z != self.z \
        or offset_x != self.offset_x \
        or offset_y != self.offset_y:
            self.z = z
            self.x = x
            self.y = y
            self.offset_x, self.offset_y = offset_x, offset_y
            self.init_redraw()

    def init_redraw(self):
        print "redraw"
        self.animate = True
        #reload icons list if its length differs from before eg. when size changes
        if len(self.icons) != (2*self.border_x+1)*(2*self.border_y+1):
            print "x:", self.border_x, "y:", self.border_y
            #clean up
            for icon in self.icons:
                icon.delete()
            self.icons = []
            #fill
            for i in xrange((2*self.border_x+1)*(2*self.border_y+1)):
                self.icons.append(Tile(self.evas_canvas.evas_obj.evas))
        if not self.offline:
            #add all tiles that are not yet downloaded to a list
            for i in xrange(2*self.border_x+1):
                for j in xrange(2*self.border_y+1):
                    if not os.path.exists("%d/%d/%d.png"%(self.z,self.x+i-self.border_x,self.y+j-self.border_y))\
                    and not (self.z,self.x+i-self.border_x,self.y+j-self.border_y) in self.tiles_to_download:
                        self.tiles_to_download.append((self.z,self.x+i-self.border_x,self.y+j-self.border_y))
            self.tiles_to_download_total = len(self.tiles_to_download)
            '''
            #add additional tiles around the raster to a preload list
            for i in xrange(2*self.border_x+3):
                if i == 0 or i == 2*self.border_x+2:
                    #if first or last row, download full row
                    for j in xrange(2*self.border_y+3):
                        if not os.path.exists("%d/%d/%d.png"%(self.z,self.x+i-self.border_x-1,self.y+j-self.border_y-1)):
                            self.tiles_to_preload.append((self.z,self.x+i-self.border_x-1,self.y+j-self.border_y-1))
                            #lots TODO here
                            #let preload more than one tile - maybe a preload_border_x/y variable
                            #manage simultaneos proeloads
                            #manage not preloading duplicates
                else
                    #else download first and last tile
            '''
            #if there are tiles to download, display progress bar
            if self.use_overlay and self.tiles_to_download_total > 0:
                self.progress_bg.geometry = 39, self.size[1]/2-1, self.size[0]-78,22
                self.progress.geometry = 40, self.size[1]/2, 1,20
                self.overlay.part_text_set("progress", "downloaded 0 of %d tiles"%self.tiles_to_download_total)
        ecore.timer_add(0.0, self.download_and_paint_current_tiles)

    def download_and_paint_current_tiles(self):
        if len(self.tiles_to_download) > 0:
            z,x,y = self.tiles_to_download.pop()
            if self.use_overlay:
                self.progress.geometry = 40, self.size[1]/2, (self.size[0]-80)*(self.tiles_to_download_total-len(self.tiles_to_download))/self.tiles_to_download_total,20
                self.overlay.part_text_set("progress", "downloaded %d of %d tiles"%(self.tiles_to_download_total-len(self.tiles_to_download),self.tiles_to_download_total))
            self.download(x,y,z)
            return True

        #we get here if all tiles are downloaded
        for i in xrange(2*self.border_x+1):
            for j in xrange(2*self.border_y+1):
                #if some errors occur replace with placeholder
                filename = "%d/%d/%d.png"%(self.z,self.x+i-self.border_x,self.y+j-self.border_y)
                try:
                    self.icons[(2*self.border_y+1)*i+j].file_set(filename)
                except Exception, e:
                    print e
                    if os.path.exists(filename):
                        os.unlink(filename)
                    self.icons[(2*self.border_y+1)*i+j].file_set("404.png")
                self.icons[(2*self.border_y+1)*i+j].set_position((i-self.border_x)*256+self.size[0]/2-self.offset_x,(j-self.border_y)*256+self.size[1]/2-self.offset_y)
                self.icons[(2*self.border_y+1)*i+j].size = 256,256
                self.icons[(2*self.border_y+1)*i+j].fill = 0, 0, 256, 256
        self.current_pos = (0,0)
        if self.use_overlay:
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
            self.animate = True
            if self.zoom_step < 1.0:
                self.zoom_in(self.zoom_step)
                self.zoom_step+=0.125
                return True

            self.zoom_step = 0.0
            self.set_current_tile(self.lat, self.lon, self.z+1)
        else:
            self.animate = False
        return False

    def animate_zoom_out(self):
        if self.z > 5:
            self.animate = True
            if self.zoom_step < 1.0:
                self.zoom_out(self.zoom_step)
                self.zoom_step+=0.125
                return True

            self.zoom_step = 0.0
            self.set_current_tile(self.lat, self.lon, self.z-1)
        else:
            self.animate = False
        return False

    @edje.decorators.signal_callback("mouse,down,1", "*")
    def on_mouse_down(self, emission, source):
        if not self.animate:
            if source in "plus":
                ecore.timer_add(0.05, self.animate_zoom_in)
            elif source in "minus":
                ecore.timer_add(0.05, self.animate_zoom_out)
            else:
                self.x_pos, self.y_pos = self.evas_canvas.evas_obj.evas.pointer_canvas_xy
                self.mouse_down = True

    @edje.decorators.signal_callback("mouse,up,1", "*")
    def on_mouse_up(self, emission, source):
        self.mouse_down = False
        if not self.animate:
            #redraw if moved further than one tile in each direction 'cause the preoload will only download one tile further than requested
            if abs(self.current_pos[0]) > 256 or abs(self.current_pos[1]) > 256:
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

            #self.marker.set_position(self.marker.pos[0]-delta_x,self.marker.pos[1]-delta_y)

if __name__ == "__main__":
    WIDTH = 480
    HEIGHT = 640

    TITLE = "pylgrim"
    WM_NAME = "pylgrim"
    WM_CLASS = "swallow"


    from optparse import OptionParser

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
            self.add_option("-o",
                        "--offline",
                        action="store_true",
                        help="do not attempt to download tiles")
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
            #calculate size of tile raster
            evas_obj.data["pylgrim"].border_x = int(math.ceil(evas_obj.data["pylgrim"].size[0]/256.0))
            evas_obj.data["pylgrim"].border_y = int(math.ceil(evas_obj.data["pylgrim"].size[1]/256.0))
            evas_obj.data["pylgrim"].init_redraw()

        def on_delete_request(self, evas_obj):
            ecore.main_loop_quit()

    options, args = myOptionParser(usage="usage: %prog [options]").parse_args()
    edje.frametime_set(1.0 / options.fps)
    evas_canvas = EvasCanvas(
        fullscreen=not options.no_fullscreen,
        engine=options.engine,
        size=options.geometry
        )
    filename = os.path.splitext(sys.argv[0])[0] + ".edj"
    Pylgrim(evas_canvas, filename, 49.009051, 8.402481, 13, options.offline, )
    ecore.main_loop_begin()

'''
export CPPFLAGS="$CPPFLAGS -I/opt/e17/include"
export LDFLAGS="$LDFLAGS -L/opt/e17/lib"
export PKG_CONFIG_PATH="/opt/e17/lib/pkgconfig:$PKG_CONFIG_PATH"
export PATH="$PATH:/opt/e17/bin"
export PYTHONPATH="/home/josch/usr/lib/python2.5/site-packages"
'''
