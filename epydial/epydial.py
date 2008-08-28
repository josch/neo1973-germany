#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
__author__ = ""
__version__ = "prototype"
__copyright__ = "Copyright (c) 2008"
__license__ = "GPL3"

WIDTH = 480
HEIGHT = 640
FULLSCREEN = True
TITLE = "epydial"
WM_INFO = ("epydial", "epydial")

import os
import sys
import ecore
import ecore.evas
import evas.decorators
import edje.decorators
import edje
from dbus import SystemBus
from e_dbus import DBusEcoreMainLoop
import e_dbus
from datetime import datetime
from os import system # alsactl is used with a sytem call
from pyneo.dbus_support import *
from pyneo.sys_support import pr_set_name

from ConfigParser import SafeConfigParser
from os.path import exists
import time
from time import sleep

#import sqlite3

for i in "data/themes/dialer.edj".split():
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
		
class dialer_main(edje_group):
	def __init__(self, main):
		edje_group.__init__(self, main, "pyneo/dialer/main")
		self.text = []

		dbus_ml = e_dbus.DBusEcoreMainLoop()
		self.system_bus = SystemBus(mainloop=dbus_ml)
		ecore.timer_add(5, self.init_dbus)

	def init_dbus(self):
		try:
			self.gsm = object_by_url('dbus:///org/pyneo/GsmDevice')
			self.wireless = object_by_url('dbus:///org/pyneo/gsmdevice/Network')
			self.keyring = object_by_url('dbus:///org/pyneo/GsmDevice')
		except Exception, e:
			print e
			#if not self.dbus_timer:
			#	self.dbus_timer = ecore.timer_add(2, self.init_dbus)
			# We had an error, keep the timer running
			#return True

		# No error, all went well
		#if self.dbus_timer: self.dbus_timer.stop()
		# D-Bus is ready, let's init GSM
		self.gsm_on()

	def gsm_on(self):
		try:
			if self.gsm.GetPower('sample', dbus_interface=DIN_POWERED, ):
				print '---', 'gsm device is already on'
			else:
				self.gsm.SetPower('sample', True, dbus_interface=DIN_POWERED, )
				print '---', 'switching device on'
		except Exception, e:
			print e
			#if not self.gsm_timer:
			#	self.gsm_timer = ecore.timer_add(5, self.gsm_on)
			# We had an error, keep the timer running
			#return True
		# No error
		#if self.gsm_timer: self.gsm_timer.stop()
		# GSM ready, let's ask SIM PIN
		self.sim_pin()

	def sim_pin(self):
		self.res = dedbusmap(self.keyring.GetOpened(dbus_interface=DIN_KEYRING))
		if self.res['code'] != 'READY': # TODO unify!
			print '---', 'opening keyring'
			self.part_text_set("numberdisplay_text", "Enter " + self.res['code'])
			self.res = dedbusmap(self.keyring.GetOpened(dbus_interface=DIN_KEYRING))
		else:
			print '---', 'already authorized'
			self.nw_register()
			
	def nw_register(self):
		self.nw_res = dedbusmap(self.wireless.GetStatus(dbus_interface=DIN_WIRELESS))
		if not self.nw_res['stat'] in (1, 5, ): # TODO unify!
			print '---', 'registering to gsm network'
			self.wireless.Register(dbus_interface=DIN_WIRELESS)
			self.nw_res = dedbusmap(self.wireless.GetStatus(dbus_interface=DIN_WIRELESS))
		else:
			self.part_text_set("numberdisplay_text", "please dial")
			print '---', 'already registered'

	@edje.decorators.signal_callback("dialer_send", "*")
	def on_edje_signal_numberkey_triggered(self, emission, source):
		if self.res['code'] != 'READY':
			if source in ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "#", "*", ):
				self.text.append(source)
				print ''.join(self.text)
				self.part_text_set("numberdisplay_text", "".join(self.text))
			elif source == "backspace":
				self.text = self.text[:-1]
				print ''.join(self.text)
				self.part_text_set("numberdisplay_text", "".join(self.text))
			elif source == "dial":
				print '---', 'send pin'
				self.keyring.Open(''.join(self.text), dbus_interface=DIN_KEYRING, )
				self.part_text_set("numberdisplay_text", "register ...")
				self.nw_register()
		else:
			if source in ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "#", "*", ):
				self.text.append(source)
				print ''.join(self.text)
				self.part_text_set("numberdisplay_text", "".join(self.text))
			elif source == "backspace":
				self.text = self.text[:-1]
				print ''.join(self.text)
				self.part_text_set("numberdisplay_text", "".join(self.text))
			elif source == "dial":
				print '---', 'dial number'
				self.part_text_set("numberdisplay_text", "calling ...")
				system('alsactl -f /usr/share/openmoko/scenarios/gsmhandset.state restore')
				name = self.wireless.Initiate(''.join(self.text), dbus_interface=DIN_VOICE_CALL_INITIATOR, timeout=200, )
				sleep(20)
				call = object_by_url(name)
				call.Hangup(dbus_interface=DIN_CALL)

class TestView(object):
	def __init__(self):
		edje.frametime_set(1.0 / 20)
		self.evas_canvas = EvasCanvas(fullscreen=FULLSCREEN, engine="x11-16", size="480x640")
		
		self.groups = {}
		self.groups["pyneo/dialer/main"] = dialer_main(self)
        	self.evas_canvas.evas_obj.data["pyneo/dialer/main"] = self.groups["pyneo/dialer/main"]
		self.groups["pyneo/dialer/main"].show()
		self.groups["pyneo/dialer/main"].part_text_set("numberdisplay_text", "wait ...")

class EvasCanvas(object):
	def __init__(self, fullscreen, engine, size):
		if engine == "x11":
			f = ecore.evas.SoftwareX11
#		elif engine == "x11-16":
#			if ecore.evas.engine_type_supported_get("software_x11_16"):
#				f = ecore.evas.SoftwareX11_16
		else:
			print "warning: x11-16 is not supported, fallback to x11"
			f = ecore.evas.SoftwareX11

		self.evas_obj = f(w=480, h=640)
		self.evas_obj.callback_delete_request = self.on_delete_request
		self.evas_obj.callback_resize = self.on_resize

		self.evas_obj.title = TITLE
		self.evas_obj.name_class = WM_INFO
		self.evas_obj.fullscreen = fullscreen
#		self.evas_obj.size = size
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

'''	
export LDFLAGS="$LDFLAGS -L/opt/e17/lib"
export PKG_CONFIG_PATH="/opt/e17/lib/pkgconfig:$PKG_CONFIG_PATH"
export PATH="$PATH:/opt/e17/bin"
export PYTHONPATH="/home/fgau/usr/lib/python2.5/site-packages"

edje_cc -v -id ../images -fd ../fonts *edc
'''

