#!/usr/bin/python
# -*- coding: utf-8 -*-

# copyright: f. gau
# license: gpl
# the function accell_cb is based on this
# source code: http://folks.o-hand.com/thomas/openmoko/gta02.py


WIDTH = 480
HEIGHT = 640
FS = True
TITLE = "pyaccel"
WM_INFO = ("pyaccel", "pyaccel")

from struct import unpack_from

import gobject
gobject.threads_init()
import os
from os import system
import sys
import evas
import evas.decorators
import edje
import edje.decorators
import ecore
import ecore.evas

# Open the accelerometer
f = open("/dev/input/event3", "r")
x = y = z = 0
newmode = ""

for i in "data/themes/pyaccel.edj".split():
	if os.path.exists( i ):
		global edjepath
		edjepath = i
		break
else:
	raise "Edje not found"

class edje_group(edje.Edje):
	def __init__(self, main, group):
		self.main = main
		global edjepath
		f = edjepath
		try:
			edje.Edje.__init__(self, self.main.evas_canvas.evas_obj.evas, file=f, group=group)
		except edje.EdjeLoadError, e:
			raise SystemExit("error loading %s: %s" % (f, e))
		self.size = self.main.evas_canvas.evas_obj.evas.size

class TestView(object):
	def on_key_down(self, obj, event):
		if event.keyname in ("F6", "f"):
			self.evas_canvas.evas_obj.fullscreen = not self.evas_canvas.evas_obj.fullscreen
		elif event.keyname == "Escape":
			ecore.main_loop_quit()

	def __init__(self):
		edje.frametime_set(1.0 / 20)
		self.evas_canvas = EvasCanvas(fullscreen=FS, engine="x11-16", size="480x640")
		
		self.groups = {}
		for part in ("bg", "main"):
			self.groups[part] = edje_group(self, part)
			self.evas_canvas.evas_obj.data[part] = self.groups[part]

		self.groups["bg"].show()
		self.groups["main"].show()
		ecore.timer_add(0.1, self.accell_cb)
		self.accell_cb()

	def accell_cb (self):
		global x, y, z
		global newmode

		text = "x = %3d;  y = %3d;  z = %3d" % ( x, y, z )
		maxx = maxy = maxz = 0
		minx = miny = minz = 0

		block = f.read(16)
		if block[8] == "\x02":
			if block[10] == "\x00":
				x = unpack_from( "@l", block[12:] )[0]
				maxx, minx = max( x, maxx ), min( x, minx )
			if block[10] == "\x01":
				y = unpack_from( "@l", block[12:] )[0]
				maxy, miny = max( y, maxy ), min( y, miny )
			if block[10] == "\x02":
				z = unpack_from( "@l", block[12:] )[0]
				maxz, minz = max( z, maxz ), min( z, minz )
			text = "x = %3d;  y = %3d;  z = %3d" % ( x, y, z )

		if abs(x) < 600 and abs(y) > 600:
			newmode = "portrait"
			system('xrandr -o 0')
		if abs(x) > 600 and abs(y) < 600:
			newmode = "landscape"
			system('xrandr -o 3')

		self.groups["main"].part_text_set("accel_txt", "%s, %s" % (text, newmode))
#		print 'Values: %s\n%s' % (text, newmode)
		return True

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

		self.evas_obj = f(w=480, h=640)
		self.evas_obj.callback_delete_request = self.on_delete_request
		self.evas_obj.callback_resize = self.on_resize

		self.evas_obj.title = TITLE
		self.evas_obj.name_class = WM_INFO
		self.evas_obj.fullscreen = FS
		self.evas_obj.show()

	def on_resize(self, evas_obj):
		x, y, w, h = evas_obj.evas.viewport
		size = (w, h)
		for key in evas_obj.data.keys():
			evas_obj.data[key].size = size

	def on_delete_request(self, evas_obj):
		ecore.main_loop_quit()

if __name__ == "__main__":
	TestView()
	ecore.main_loop_begin()
	f.close()

'''
export LDFLAGS="$LDFLAGS -L/opt/e17/lib"
export PKG_CONFIG_PATH="/opt/e17/lib/pkgconfig:$PKG_CONFIG_PATH"
export PATH="$PATH:/opt/e17/bin"
export PYTHONPATH="/home/fgau/usr/lib/python2.5/site-packages"

edje_cc -v -id ../images -fd ../fonts *edc
'''
